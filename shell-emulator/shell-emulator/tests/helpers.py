"""Вспомогательные средства для тестов."""

import io
import os
import tempfile
import zipfile

from emulator.shell import Shell
from emulator.vfs import VFS


def make_shell(env=None, **kwargs):
    """Создать оболочку, пишущую вывод в буфер."""
    buffer = io.StringIO()
    shell = Shell(out=buffer, env=env if env is not None else {}, **kwargs)
    return shell, buffer


def run(shell, buffer, line):
    """Выполнить строку и вернуть (код, вывод), очистив буфер."""
    buffer.seek(0)
    buffer.truncate()
    status = shell.execute(line)
    return status, buffer.getvalue()


SAMPLE_ENTRIES = {
    "a.txt": "line\nline\nother\n",
    "dir/b.txt": "bee\n",
    "dir/sub/deep/c.txt": "sea\n",
    "dir/empty/": None,
    "bin.dat": bytes(range(256)),
}


def write_zip(path, entries=None):
    """Записать ZIP-архив с элементами ``entries`` (имя -> данные)."""
    entries = SAMPLE_ENTRIES if entries is None else entries
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in entries.items():
            if isinstance(content, str):
                content = content.encode("utf-8")
            archive.writestr(name, content or b"")
    return path


def make_vfs(entries=None):
    """Создать VFS из словаря элементов через временный архив."""
    with tempfile.TemporaryDirectory() as tmp:
        return VFS.from_zip(write_zip(os.path.join(tmp, "t.zip"), entries))
