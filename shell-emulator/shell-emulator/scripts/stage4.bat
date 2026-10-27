@echo off
rem Этап 4: основные команды на VFS с тремя уровнями вложенности.
cd /d "%~dp0.."
python scripts\make_vfs.py
call run.bat --vfs vfs\deep.zip --script examples\stage4.txt
