@echo off
rem Этап 2: параметр --script и сочетание всех параметров.
set "ROOT=%~dp0.."

echo === --script: скрипт с ошибочными строками ===
call "%ROOT%\run.bat" --script "%ROOT%\examples\stage2.txt"
echo код возврата: %ERRORLEVEL%

echo === --script без exit: переход в интерактивный режим ===
echo exit 7| call "%ROOT%\run.bat" --script "%ROOT%\examples\no_exit.txt"
echo код возврата: %ERRORLEVEL%

echo === --script: несуществующий файл ===
call "%ROOT%\run.bat" --script "%ROOT%\examples\missing.txt"
echo код возврата: %ERRORLEVEL%

echo === Все параметры вместе ===
call "%ROOT%\run.bat" --vfs "%ROOT%\vfs\minimal.zip" --script "%ROOT%\examples\stage2.txt"
