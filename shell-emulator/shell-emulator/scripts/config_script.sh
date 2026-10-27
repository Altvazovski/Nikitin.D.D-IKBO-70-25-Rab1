#!/bin/sh
# Этап 2: параметр --script и сочетание всех параметров.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== --script: скрипт с ошибочными строками ==="
"$ROOT/run.sh" --script "$ROOT/examples/stage2.txt"
echo "код возврата: $?"

echo "=== --script без exit: переход в интерактивный режим ==="
echo "exit 7" | "$ROOT/run.sh" --script "$ROOT/examples/no_exit.txt"
echo "код возврата: $?"

echo "=== --script: несуществующий файл ==="
"$ROOT/run.sh" --script "$ROOT/examples/missing.txt"
echo "код возврата: $?"

echo "=== Все параметры вместе ==="
"$ROOT/run.sh" --vfs "$ROOT/vfs/minimal.zip" \
    --script "$ROOT/examples/stage2.txt"
