#!/bin/sh
# Этап 3: работа с VFS 'minimal'.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
python3 scripts/make_vfs.py
mkdir -p out

echo "=== VFS 'minimal' + стартовый скрипт этапа 3 ==="
./run.sh --vfs vfs/minimal.zip --script examples/stage3.txt
echo "код возврата: $?"

echo "=== Содержимое архива, сохранённого vfs-save ==="
python3 -m zipfile -l out/saved.zip
