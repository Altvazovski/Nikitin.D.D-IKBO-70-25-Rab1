"""Запуск эмулятора из командной строки."""

import argparse
import os

from emulator.errors import VfsError
from emulator.shell import PROGRAM, STATUS_ERROR, Shell
from emulator.vfs import VFS

try:
    import readline  # noqa: F401  (история и редактирование ввода)
except ImportError:
    readline = None

NOT_SET = "<not set>"


def parse_args(argv=None):
    """Разобрать параметры командной строки эмулятора."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Эмулятор командной оболочки UNIX-подобной ОС.")
    parser.add_argument(
        "--vfs", metavar="PATH",
        help="путь к физическому расположению VFS (ZIP-архив)")
    parser.add_argument(
        "--script", metavar="PATH",
        help="путь к стартовому скрипту с командами эмулятора")
    return parser.parse_args(argv)


def describe_path(path):
    """Вернуть путь в виде для отладочного вывода."""
    if path is None:
        return NOT_SET
    return os.path.abspath(path)


def print_config(config, write):
    """Вывести отладочную информацию о всех параметрах запуска."""
    write("[debug] emulator configuration:")
    write(f"[debug]   vfs path     = {describe_path(config.vfs)}")
    write(f"[debug]   start script = {describe_path(config.script)}")


def read_script(path):
    """Прочитать стартовый скрипт и вернуть список строк."""
    with open(path, encoding="utf-8") as script:
        return script.read().splitlines()


def run_start_script(shell, path):
    """Выполнить стартовый скрипт.

    :return: код завершения, если скрипт завершил работу, иначе None.
    """
    try:
        lines = read_script(path)
    except (OSError, UnicodeDecodeError) as error:
        reason = getattr(error, "strerror", None) or error
        shell.write(f"{PROGRAM}: cannot read script '{path}': {reason}")
        return STATUS_ERROR
    return shell.run_script(lines)


def load_vfs(path):
    """Загрузить VFS из архива или создать пустую, если путь не задан."""
    if path is None:
        return VFS()
    return VFS.from_zip(path)


def print_vfs_info(vfs, write):
    """Вывести отладочную информацию о загруженной VFS."""
    dirs, files = vfs.count()
    write(f"[debug]   vfs loaded   = '{vfs.name}': "
          f"{dirs} directories, {files} files")


def main(argv=None):
    """Запустить эмулятор и вернуть код завершения."""
    config = parse_args(argv)
    shell = Shell()
    print_config(config, shell.write)
    try:
        shell.vfs = load_vfs(config.vfs)
    except VfsError as error:
        shell.write(f"{PROGRAM}: cannot load VFS: {error}")
        return STATUS_ERROR
    print_vfs_info(shell.vfs, shell.write)
    if config.script is not None:
        code = run_start_script(shell, config.script)
        if code is not None:
            return code
    return shell.run_interactive()
