#!/usr/bin/env python3
"""BMP（含 Alpha）↔ BGI / Ethornell 無副檔名圖檔

BGI 未壓縮資源，16-byte little-endian 檔頭（與 BGIBmpConverterV2 相同）::

    int16  width
    int16  height          # 恆為正
    int16  bpp             # 24 或 32
    int16  flag            # 0 = raw
    int32  0
    int32  0
    pixels                 # 由上往下、無列對齊
                           # 24-bit = BGR
                           # 32-bit = BGRA（第 4 byte 即引擎用的 alpha）

與舊版 BGIBmpConverterV2.begin_build_resource() 的差別
----------------------------------------------------
* 讀 bfOffBits，不寫死 0x36（支援 BITMAPV4 / V5）
* 處理 BMP 列 padding
* 正高度（由下往上）會翻成 BGI 的 top-down
* 32-bit 完整保留 Alpha，不會被 PIL / 舊轉換器丟掉

Usage::

    python3 bmp_to_bgi.py input.bmp
    python3 bmp_to_bgi.py input.bmp -o 01_1_koh
    python3 bmp_to_bgi.py ./bmp_folder -o ./bgi_folder
    python3 bmp_to_bgi.py 01_1_koh --to-bmp          # 反向：BGI → 帶 Alpha 的 V4 BMP
    python3 bmp_to_bgi.py input.bmp --keep-24
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
from typing import Optional, Tuple


class BmpError(ValueError):
    pass


# ---------------------------------------------------------------------------
# BMP → raw top-down BGR(A)
# ---------------------------------------------------------------------------

def read_bmp(path: str) -> Tuple[int, int, int, bytes]:
    """Return (width, height, bpp, top-down BGR/BGRA pixels)."""
    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 54 or data[:2] != b"BM":
        raise BmpError(f"不是 BMP：{path}")

    bf_off = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    if dib_size < 40 or bf_off > len(data):
        raise BmpError(f"不支援或檔頭損壞：{path} (DIB={dib_size}, off={bf_off})")

    width = struct.unpack_from("<i", data, 18)[0]
    height_signed = struct.unpack_from("<i", data, 22)[0]
    planes, bpp = struct.unpack_from("<HH", data, 26)
    compression = struct.unpack_from("<I", data, 30)[0]

    if width <= 0:
        raise BmpError(f"非法寬度 {width}")
    height = abs(height_signed)
    top_down = height_signed < 0

    if planes != 1:
        raise BmpError(f"不支援 planes={planes}")
    if bpp not in (24, 32):
        raise BmpError(f"只支援 24/32-bit BMP（實際 {bpp}）。8-bit 調色盤請用原版轉換器。")
    # 0=BI_RGB  3=BI_BITFIELDS  6=BI_ALPHABITFIELDS
    if compression not in (0, 3, 6):
        raise BmpError(f"不支援壓縮 BMP（compression={compression}）")

    # 常見 V4/V5 mask 是 BGRA（R=00FF0000 G=0000FF00 B=000000FF A=FF000000）
    # 與 BGI 位元組順序相同，直接拷貝即可。
    # 若 mask 是非標準順序，重排成 BGRA。
    masks = None
    if compression in (3, 6) or dib_size >= 56:
        mask_off = 54
        if mask_off + 16 <= len(data):
            r_m, g_m, b_m, a_m = struct.unpack_from("<IIII", data, mask_off)
            if any((r_m, g_m, b_m)):
                masks = (b_m, g_m, r_m, a_m)

    src_stride = ((width * bpp + 31) // 32) * 4
    end = bf_off + src_stride * height
    if end > len(data):
        raise BmpError(f"像素區被截斷：需要 {end} bytes，檔案只有 {len(data)}")

    raw = data[bf_off:end]
    dst_pp = bpp // 8
    dst_stride = width * dst_pp
    out = bytearray(dst_stride * height)

    standard_bgra = masks in (
        None,
        (0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000),
        (0x000000FF, 0x0000FF00, 0x00FF0000, 0x00000000),
    )

    for y in range(height):
        src_y = y if top_down else (height - 1 - y)
        src = raw[src_y * src_stride : src_y * src_stride + dst_stride]
        dst_off = y * dst_stride
        if standard_bgra or bpp == 24:
            out[dst_off : dst_off + dst_stride] = src
        else:
            b_m, g_m, r_m, a_m = masks
            for x in range(width):
                px = int.from_bytes(src[x * 4 : x * 4 + 4], "little")

                def ch(mask: int) -> int:
                    if mask == 0:
                        return 0xFF if mask is a_m else 0
                    shift = (mask & -mask).bit_length() - 1
                    bits = (mask >> shift).bit_count()
                    val = (px & mask) >> shift
                    if bits >= 8:
                        return (val >> (bits - 8)) & 0xFF
                    return (val * 255) // ((1 << bits) - 1)

                out[dst_off + x * 4 : dst_off + x * 4 + 4] = bytes(
                    (
                        ch(b_m),
                        ch(g_m),
                        ch(r_m),
                        ch(a_m) if a_m else 0xFF,
                    )
                )

    return width, height, bpp, bytes(out)


def write_bgi(path: str, width: int, height: int, bpp: int, pixels: bytes) -> None:
    if not (0 < width <= 0x7FFF and 0 < height <= 0x7FFF):
        raise BmpError(f"BGI 長寬是 int16，無法寫入 {width}x{height}")
    if bpp not in (24, 32):
        raise BmpError(f"BGI bpp 僅 24/32，收到 {bpp}")
    expected = width * height * (bpp // 8)
    if len(pixels) != expected:
        raise BmpError(f"像素長度 {len(pixels)} != {expected}")

    header = struct.pack("<hhhhii", width, height, bpp, 0, 0, 0)
    assert len(header) == 16
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as f:
        f.write(header)
        f.write(pixels)


def expand_24_to_32(bgr: bytes) -> bytes:
    out = bytearray(len(bgr) // 3 * 4)
    si = di = 0
    while si < len(bgr):
        out[di : di + 3] = bgr[si : si + 3]
        out[di + 3] = 0xFF
        si += 3
        di += 4
    return bytes(out)


# ---------------------------------------------------------------------------
# BGI → BITMAPV4（保留 Alpha，方便再編輯後轉回）
# ---------------------------------------------------------------------------

def read_bgi(path: str) -> Tuple[int, int, int, bytes]:
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 16:
        raise BmpError(f"不是 BGI 資源：{path}")
    width, height, bpp, flag = struct.unpack_from("<hhhh", data, 0)
    width, height, bpp = abs(width), abs(height), abs(bpp)
    if flag != 0:
        raise BmpError(f"{path} flag={flag}，可能是壓縮資源，本工具只處理 raw")
    if bpp not in (24, 32):
        raise BmpError(f"{path} bpp={bpp}，本工具只處理 24/32")
    pixels = data[16:]
    expected = width * height * (bpp // 8)
    if len(pixels) < expected:
        raise BmpError(f"{path} 像素不足：{len(pixels)} < {expected}")
    return width, height, bpp, pixels[:expected]


def write_bmp_v4(path: str, width: int, height: int, bpp: int, topdown: bytes) -> None:
    """寫 top-down BITMAPV4HEADER，32-bit 帶 BI_BITFIELDS + Alpha mask。"""
    if bpp not in (24, 32):
        raise BmpError(f"BMP 匯出僅 24/32，收到 {bpp}")
    row = width * (bpp // 8)
    stride = ((bpp * width + 31) // 32) * 4
    pad = stride - row
    body = bytearray()
    for y in range(height):
        body.extend(topdown[y * row : (y + 1) * row])
        if pad:
            body.extend(b"\x00" * pad)

    dib = 108
    off = 14 + dib
    compression = 3 if bpp == 32 else 0  # BI_BITFIELDS / BI_RGB
    file_size = off + len(body)

    buf = bytearray()
    buf += b"BM"
    buf += struct.pack("<IHHI", file_size, 0, 0, off)
    buf += struct.pack(
        "<IiiHHIIiiII",
        dib,
        width,
        -height,  # top-down
        1,
        bpp,
        compression,
        len(body),
        0,
        0,
        0,
        0,
    )
    if bpp == 32:
        # R, G, B, A masks → 記憶體位元組順序為 B, G, R, A
        buf += struct.pack("<IIII", 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    else:
        buf += struct.pack("<IIII", 0, 0, 0, 0)
    buf += b"Win "
    buf += b"\x00" * 48  # endpoints + gamma
    if len(buf) != off:
        raise RuntimeError(f"internal header {len(buf)} != {off}")
    buf += body

    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as f:
        f.write(buf)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def default_bgi_path(bmp_path: str) -> str:
    root, ext = os.path.splitext(bmp_path)
    return root if ext.lower() == ".bmp" else bmp_path + ".bgi"


def convert_bmp_file(src: str, dst: Optional[str], keep_24: bool) -> Tuple[str, int, int, int]:
    width, height, bpp, pixels = read_bmp(src)
    out_bpp = bpp
    if bpp == 24 and not keep_24:
        pixels = expand_24_to_32(pixels)
        out_bpp = 32
    dest = dst or default_bgi_path(src)
    write_bgi(dest, width, height, out_bpp, pixels)
    return dest, width, height, out_bpp


def convert_bgi_file(src: str, dst: Optional[str]) -> Tuple[str, int, int, int]:
    width, height, bpp, pixels = read_bgi(src)
    dest = dst or (src + ".bmp")
    write_bmp_v4(dest, width, height, bpp, pixels)
    return dest, width, height, bpp


def iter_jobs(src: str, out: Optional[str], to_bmp: bool):
    if os.path.isdir(src):
        outdir = out or src
        os.makedirs(outdir, exist_ok=True)
        for name in sorted(os.listdir(src)):
            path = os.path.join(src, name)
            if not os.path.isfile(path):
                continue
            is_bmp = os.path.splitext(name)[1].lower() == ".bmp"
            if to_bmp:
                if is_bmp:
                    continue
                yield path, os.path.join(outdir, name + ".bmp"), False
            else:
                if not is_bmp:
                    continue
                yield path, os.path.join(outdir, os.path.splitext(name)[0]), True
    else:
        if to_bmp:
            yield src, out or (src + ".bmp"), False
        else:
            yield src, out or default_bgi_path(src), True


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(
        description="BMP（含 Alpha）↔ BGI/Ethornell 無副檔名圖檔"
    )
    p.add_argument("input", help="BMP / BGI 檔，或資料夾")
    p.add_argument("-o", "--output", help="輸出檔或輸出資料夾")
    p.add_argument(
        "--to-bmp",
        action="store_true",
        help="反向：BGI raw → 帶 Alpha 的 BITMAPV4 BMP",
    )
    p.add_argument(
        "--keep-24",
        action="store_true",
        help="24-bit BMP 維持 24-bit BGI（預設會補不透明 Alpha 成 32-bit）",
    )
    args = p.parse_args(argv)

    if not os.path.exists(args.input):
        print(f"ERROR: 找不到 {args.input}", file=sys.stderr)
        return 1

    jobs = list(iter_jobs(args.input, args.output, args.to_bmp))
    if not jobs:
        print("ERROR: 沒有符合的檔案", file=sys.stderr)
        return 1

    rc = 0
    for src, dst, to_bgi in jobs:
        try:
            if to_bgi:
                dest, w, h, d = convert_bmp_file(src, dst, args.keep_24)
                print(f"BMP → BGI  {src}  →  {dest}  ({w}x{h}, {d}bpp)")
            else:
                dest, w, h, d = convert_bgi_file(src, dst)
                print(f"BGI → BMP  {src}  →  {dest}  ({w}x{h}, {d}bpp)")
        except BmpError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            rc = 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
