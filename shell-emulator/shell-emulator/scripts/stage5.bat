@echo off
rem Этап 5: команды rmdir, mv, help на VFS с тремя уровнями вложенности.
cd /d "%~dp0.."
python scripts\make_vfs.py
if not exist out mkdir out
call run.bat --vfs vfs\deep.zip --script examples\stage5.txt
