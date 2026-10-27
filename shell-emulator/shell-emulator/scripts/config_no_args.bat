@echo off
rem Этап 2: запуск без параметров и вызов справки по параметрам.
set "ROOT=%~dp0.."

echo === Запуск без параметров (ввод из stdin) ===
echo exit 0| call "%ROOT%\run.bat"

echo === Справка по параметрам ===
call "%ROOT%\run.bat" --help

echo === Неизвестный параметр ===
call "%ROOT%\run.bat" --unknown
echo код возврата: %ERRORLEVEL%
