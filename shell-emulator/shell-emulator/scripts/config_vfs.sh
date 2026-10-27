#!/bin/sh
# Этап 2: параметр --vfs (относительный и абсолютный путь).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== --vfs с относительным путём ==="
echo "exit" | "$ROOT/run.sh" --vfs vfs/minimal.zip

echo "=== --vfs с абсолютным путём ==="
echo "exit" | "$ROOT/run.sh" --vfs "$ROOT/vfs/deep.zip"

echo "=== --vfs без значения ==="
"$ROOT/run.sh" --vfs
echo "код возврата: $?"
