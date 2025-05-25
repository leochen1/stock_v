@echo off
D:
cd D:\SideProject\stock_v

:: 啟動虛擬環境
call venv\Scripts\activate.bat

:: 回到專案根目錄
cd /d D:\SideProject\stock_v

:: 依序執行 Python 腳本
python otc-today-data-download.py
python otc-line.py
python twse-line.py
python otc-txt.py
python twse-txt.py
python merge-txt.py
pause