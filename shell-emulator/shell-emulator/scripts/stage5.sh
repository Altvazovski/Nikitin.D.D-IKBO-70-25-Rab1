#!/bin/sh
# Этап 5: команды rmdir, mv, help на VFS с тремя уровнями вложенности.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
python3 scripts/make_vfs.py
mkdir -p out
./run.sh --vfs vfs/deep.zip --script examples/stage5.txt
