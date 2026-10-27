@echo off
rem Запуск эмулятора. Все аргументы передаются эмулятору.
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
python -m emulator %*
