#!/bin/sh
# Этап 3: ошибки загрузки VFS (пустой, отсутствующий, повреждённый архив).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
python3 scripts/make_vfs.py

echo "=== Пустой архив ==="
echo "exit" | ./run.sh --vfs vfs/empty.zip
echo "=== Несуществующий архив ==="
./run.sh --vfs vfs/missing.zip
echo "код возврата: $?"
echo "=== Файл не является ZIP-архивом ==="
./run.sh --vfs vfs/broken.zip
echo "код возврата: $?"
echo "=== Вместо архива указан каталог ==="
./run.sh --vfs vfs
echo "код возврата: $?"
