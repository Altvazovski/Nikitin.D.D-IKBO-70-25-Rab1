@echo off
rem Этап 3: ошибки загрузки VFS (пустой, отсутствующий, повреждённый архив).
cd /d "%~dp0.."
python scripts\make_vfs.py

echo === Пустой архив ===
echo exit| call run.bat --vfs vfs\empty.zip
echo === Несуществующий архив ===
call run.bat --vfs vfs\missing.zip
echo код возврата: %ERRORLEVEL%
echo === Файл не является ZIP-архивом ===
call run.bat --vfs vfs\broken.zip
echo код возврата: %ERRORLEVEL%
echo === Вместо архива указан каталог ===
call run.bat --vfs vfs
echo код возврата: %ERRORLEVEL%
