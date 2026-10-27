@echo off
rem Этап 3: работа с VFS 'multi'.
cd /d "%~dp0.."
python scripts\make_vfs.py
if not exist out mkdir out

echo === VFS 'multi' + стартовый скрипт этапа 3 ===
call run.bat --vfs vfs\multi.zip --script examples\stage3.txt
echo код возврата: %ERRORLEVEL%

echo === Содержимое архива, сохранённого vfs-save ===
python -m zipfile -l out\saved.zip
