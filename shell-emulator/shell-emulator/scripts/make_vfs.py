"""Сгенерировать тестовые образы VFS в каталоге ``vfs/``.

Архивы не хранятся в репозитории: они создаются этим скриптом.
Запуск: ``python3 scripts/make_vfs.py [каталог]``.
"""

import os
import sys
import zipfile

STAMP = (2026, 9, 1, 12, 0, 0)
BINARY_DATA = bytes(range(256))
LOG_LINES = "boot ok\nboot ok\nnet up\nnet up\nnet up\ndisk full\nboot ok\n"

MINIMAL = {
    "hello.txt": "Hello, VFS!\n",
}

MULTI = {
    "notes.txt": "first note\nsecond note\n",
    "todo.txt": "buy milk\nbuy milk\nwrite report\n",
    "data.csv": "id,name\n1,alpha\n2,beta\n",
    "log.txt": LOG_LINES,
    "image.bin": BINARY_DATA,
}

DEEP = {
    "home/user/.profile": "export PATH=/bin\n",
    "home/user/docs/report.txt": "Report\n======\nAll good.\n",
    "home/user/docs/drafts/v1.txt": "draft one\n",
    "home/user/docs/drafts/old/v0.txt": "very old draft\n",
    "home/user/music/": None,
    "etc/config/app.conf": "debug=false\nport=8080\n",
    "var/log/syslog": LOG_LINES * 3,
    "bin/tool.bin": BINARY_DATA * 8,
    "tmp/": None,
}


def write_archive(path, entries):
    """Записать словарь ``имя -> содержимое`` в ZIP-архив."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            if isinstance(content, str):
                content = content.encode("utf-8")
            archive.writestr(info, content or b"")


def main(target):
    """Создать все тестовые образы VFS в каталоге ``target``."""
    os.makedirs(target, exist_ok=True)
    write_archive(os.path.join(target, "empty.zip"), {})
    write_archive(os.path.join(target, "minimal.zip"), MINIMAL)
    write_archive(os.path.join(target, "multi.zip"), MULTI)
    write_archive(os.path.join(target, "deep.zip"), DEEP)
    with open(os.path.join(target, "broken.zip"), "w",
              encoding="utf-8") as broken:
        broken.write("this is not a zip archive\n")
    print(f"VFS images created in {os.path.abspath(target)}")


if __name__ == "__main__":
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main((sys.argv[1:] or [os.path.join(ROOT, "vfs")])[0])
