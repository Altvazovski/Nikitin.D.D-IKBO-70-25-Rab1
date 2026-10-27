#!/bin/sh
# Этап 2: запуск без параметров и вызов справки по параметрам.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Запуск без параметров (ввод из stdin) ==="
printf 'ls -a\nexit 0\n' | "$ROOT/run.sh"

echo "=== Справка по параметрам ==="
"$ROOT/run.sh" --help

echo "=== Неизвестный параметр ==="
"$ROOT/run.sh" --unknown
echo "код возврата: $?"
