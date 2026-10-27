#!/bin/sh
# Этап 4: основные команды на VFS с тремя уровнями вложенности.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
python3 scripts/make_vfs.py
./run.sh --vfs vfs/deep.zip --script examples/stage4.txt
