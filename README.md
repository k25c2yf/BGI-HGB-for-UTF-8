# Hello, good-bye　開源中文補丁（UTF-8 / BGI）

基於 BGI `bgi_v1.669.3` 的《Hello, good-bye》（ハロー・グッドバイ）中文補丁。  
目前版本：**v2.5（Latest）**

- 繁體：BIG5
- 簡體：GBK

玩家下載請走 Releases，不要用 `/blob/` 頁面：  
**https://github.com/k25c2yf/BGI-HGB-for-UTF-8/releases/latest**

| 版本 | 檔案 |
|---|---|
| 繁體中文 | `HelloGoodBye-BIG5-bgi_v1.669.3_v2.5.exe` |
| 简体中文 | `HelloGoodBye-GBK-bgi_v1.669.3_v2.5.exe` |

### 相對上一版更新（v2.5）

1. 重新用 AI 重製人名中文圖片、按鍵圖片、支線圖片、選單圖片等 UI 圖。
2. 修改 `_bp` 系統檔內文字為中文（設定、存讀檔、確認框、勳章名稱／解除條件、backlog 人名等）。
3. 以 Grok 重新翻譯全部劇本，並做潤飾、校正（控制符、ruby、辭典、人名表保留）。
4. 更新打包引擎，降低被防毒標成惡意程式的情況。

---

## 年齡分級

本作為 **18+** 成人遊戲。未滿十八歲（或未達你所在地區法定成年年齡）請勿下載、安裝或遊玩。

---

## 玩家使用方式

1. 請先自行持有正版《Hello, good-bye》。本倉庫**不提供**原版遊戲本體。
2. 到 [Releases](https://github.com/k25c2yf/BGI-HGB-for-UTF-8/releases/latest) 下載對應 exe。
3. 執行下載到的整合包即可。繁、簡不要混用。
4. 防毒軟體有時會誤報自行封裝的 exe。

---

## 自行編譯／重新打包

以下給要從原始檔重建補丁的人。一般玩家不必做這段。

### 環境

- Windows
- [Python 3](https://www.python.org/downloads/)（安裝時勾選 Add Python to PATH）
- 7-Zip 或能解 `.7z` 的工具
- [Enigma Virtual Box](https://enigmaprotector.com/en/aboutvb.html)（倉庫根目錄也有 `enigmavb.exe`）

下載整個倉庫（Code → Download ZIP，或 `git clone`）後，在倉庫**根目錄**操作。

先確認這些路徑存在：

| 路徑 | 用途 |
|---|---|
| `source/` | 原版腳本 |
| `big5/` | 繁中劇本 txt |
| `jp/jpname/` | 各章原日文人名表（對應 `●編號●`，見下方說明） |
| `big5pic/big5pic.7z` | 繁中圖片包（需先解壓） |
| `gbpic/` | 簡中圖片包（需先解壓裡面的壓縮檔） |
| `sysprg/big5/` | 繁中系統 `_bp` |
| `sysprg/gb/` | 簡中系統 `_bp` |
| `bgi_v1.669.3_source.exe` | Enigma 主程式 |
| `outputbig5.bat` / `outputgb.bat` | 封包腳本 |
| `繁體中文轉簡體中文.py` | 繁→簡劇本 |

### `jp/jpname`：人名必須還原成日文

`jp/jpname/` 裡的檔（如 `jp_01_2.txt`）對應翻譯劇本裡同一條 `●數字號●` 的**原日文人名**（說話人欄，例如 `すぐり`、`カイト`、`メイ`）。

封包時要用這些檔把該標號還原成日文。遊戲是靠**日文原名**去對人名圖片（名牌立繪字）；改成中文或其他文字後，引擎對不到圖，畫面上只會出現普通文字名牌。

因此：

- 不要把 `jp/jpname` 裡的人名改成「直裡／海斗／芽衣」等中文。
- 中文名只寫在 `big5/`（或轉出的 `gb/`）對白與 backlog 用的系統檔。
- `outputgb.bat` 已會呼叫 `BGIScriptRepacker-jp.py`，把 `./jp/jpname/jp_章節.txt` 套回編譯結果。繁中流程若也要顯示人名圖，同樣必須經過這一步，不可省略。

### 1. 解圖片壓縮包

把 `big5pic` 裡的壓縮包（如 `big5pic.7z`）解成**資料夾**，不要只留 7z。  
簡體同樣處理 `gbpic` 裡的壓縮包。

解完後 `big5pic`、`gbpic` 底下應能直接看到圖片／bin，而不是只有一個壓縮檔。

### 2. 繁體：編譯腳本

在根目錄執行：

```bat
outputbig5.bat
```

成功後會出現 `outputbig5/`（以及過程用的 `temp/`）。  
bat 會自行 `pip install opencc-python-reimplemented`。

### 3. 繁體：Enigma Virtual Box 打包

1. 開啟 Enigma Virtual Box。
2. **主程式 %Input File%**：選根目錄的 `bgi_v1.669.3_source.exe`。
3. 把下列內容加進虛擬盒（Files）：
   - `big5pic` 解壓出來的**全部檔案**
   - `outputbig5/` 裡的全部檔案
   - `sysprg/big5/` 裡的繁中系統檔（覆蓋到遊戲讀取的 `sysprg` 位置）
4. 輸出檔名可設為  
   `HelloGoodBye-BIG5-bgi_v1.669.3_v2.5.exe`
5. Process / 開始封裝。

`sysprg` 的檔名要跟遊戲原本一致（例如 `omakeresult._bp`、`cnfgwnd._bp`、`logwnd._bp`），不要多包一層多餘資料夾導致引擎找不到。

### 4. 簡體：轉劇本並編譯

在根目錄依序執行：

```bat
python 繁體中文轉簡體中文.py
outputgb.bat
```

- 轉換腳本讀 `./big5`，寫出 `./gb`
- `outputgb.bat` 讀 `./gb`，並用 `./jp/jpname/` 把 `●編號●` 說話人還原成日文後，產出 `outputgbk/`

### 5. 簡體：Enigma Virtual Box 打包

1. 主程式同樣用 `bgi_v1.669.3_source.exe`。
2. 加入：
   - `gbpic` 解壓出來的**全部檔案**
   - `outputgbk/` 裡的全部檔案
   - `sysprg/gb/` 裡的簡中系統檔
3. 輸出檔名可設為  
   `HelloGoodBye-GBK-bgi_v1.669.3_v2.5.exe`

---

## v2.5 範圍（摘要）

- 劇本繁／簡中文化（控制符、ruby、辭典、人名表）
- 系統 UI、勳章名稱與解除條件
- 設定、存讀檔、確認框、backlog 人名
- 相關 BMP／字型缺字

系統字串受引擎碼表限制，部分用字採可編碼漢字（例如 档／顕／窓／関）。

---

## 注意與免責

- 遊戲著作權歸原製作公司（Lump of Sugar）及相關權利人。本專案只提供粉絲翻譯／技術適配，與官方無關。
- 補丁免費、僅供個人學習與研究。禁止販售。
- 解包、改檔、使用封裝工具的風險由使用者承擔。
- 文本含機器翻譯再修，歡迎開 Issue／PR。

---

## 倉庫說明

根目錄 exe 僅供開發對照。正式發布以 **Releases** 為準。  
`big5`、`jp/jpname`、`source`、`sysprg` 與各種 `.py` 是製作材料，一般玩家不需要。`jp/jpname` 只還原日文人名以對人名圖片，勿改成中文。

---

## 回報問題

請開 Issue，並附：使用 BIG5 或 GBK、章節／對話 ID（如 `●018672●`）、截圖。

已知舊稿曾把「すーちゃん」寫成「小蘇」，正確為「直裡／直里」。請確認已換成 v2.5。
