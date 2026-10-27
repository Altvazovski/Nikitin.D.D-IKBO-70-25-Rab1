#!/bin/sh
# Запуск эмулятора. Все аргументы передаются эмулятору.
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$DIR/src${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m emulator "$@"
