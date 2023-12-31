@echo on

setlocal enabledelayedexpansion

set "temp=./temp/"
set "gb=./gb/"
set "outputgbk=./outputgbk/"
set "jp=./jp/jpname/"

for %%i in (00 01_1 01_2 01_3 02a 02b 02c 02d 03a 03b 03c 03d 04a 04b 04c 04d 05abc 05d 06a 06b 06c 06d 07b 07c 07d 08d 08_1abc 08_2a 09a 09b 09c 09d 10d 10d_2h 10_1ac 10_2a 10_3abc 11a 11a_2 11b 11c 11d 11d_2h 11d_3 12a 12a_2h 12b 12b_2h 12c 12d 13a 13a_2h 13b 13c 13c_2h 13c_3 13d 14a 14b_2h 14b_3 14c 14d 15a 15a_2h 15b 15b_2h 15c 15d 15d_2h 16a 16b 16c 16c_2h 16d 17c 17c_2h 17d 18c) do (
  python BGIScriptRepackerV2.py ./source/%%i !gb!%%i_tc.txt !temp!%%i
  python BGIScriptRepacker-jp.py !temp!%%i !jp!jp_%%i.txt !outputgbk!%%i
)

echo 完成！

pause