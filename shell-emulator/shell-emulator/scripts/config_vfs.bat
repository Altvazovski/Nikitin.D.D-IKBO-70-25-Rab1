@echo off
rem Этап 2: параметр --vfs (относительный и абсолютный путь).
set "ROOT=%~dp0.."

echo === --vfs с относительным путём ===
echo exit| call "%ROOT%\run.bat" --vfs vfs\minimal.zip

echo === --vfs с абсолютным путём ===
echo exit| call "%ROOT%\run.bat" --vfs "%ROOT%\vfs\deep.zip"

echo === --vfs без значения ===
call "%ROOT%\run.bat" --vfs
echo код возврата: %ERRORLEVEL%
