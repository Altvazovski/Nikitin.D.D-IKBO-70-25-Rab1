"""Команды навигации по VFS: ``ls`` и ``cd``."""

import time

from emulator.commands.options import parse_options, report
from emulator.errors import CommandError, VfsError

LS_OPTIONS = "alR"
CD_MAX_ARGS = 1
SINGLE_OPERAND = 1
PREVIOUS_DIR = "-"
HIDDEN_PREFIX = "."
DIR_MODE = "drwxr-xr-x"
FILE_MODE = "-rw-r--r--"
SIZE_WIDTH = 8
TIME_FORMAT = "%b %d %H:%M"
TIME_PADDING = (0, 0, -1)


def format_mtime(mtime):
    """Отформатировать время изменения узла в стиле ``ls -l``."""
    return time.strftime(TIME_FORMAT, tuple(mtime) + TIME_PADDING)


def format_long(shell, node, name):
    """Сформировать строку длинного формата ``ls -l``."""
    mode = DIR_MODE if node.is_dir else FILE_MODE
    size = len(node.children) if node.is_dir else node.size
    owner = shell.user
    return (f"{mode} {owner} {owner} {size:>{SIZE_WIDTH}} "
            f"{format_mtime(node.mtime)} {name}")


def directory_entries(directory, flags):
    """Вернуть пары (имя, узел) содержимого каталога для ``ls``."""
    entries = []
    if "a" in flags:
        entries.append((".", directory))
        entries.append(("..", directory.parent or directory))
    for child in directory.sorted_children():
        if "a" in flags or not child.name.startswith(HIDDEN_PREFIX):
            entries.append((child.name, child))
    return entries


def print_entries(shell, entries, flags):
    """Вывести список элементов в кратком или длинном формате."""
    if not entries:
        return
    if "l" in flags:
        for name, node in entries:
            shell.write(format_long(shell, node, name))
    else:
        shell.write("  ".join(name for name, _ in entries))


def list_directory(shell, path, node, flags):
    """Вывести содержимое каталога (рекурсивно при ``-R``)."""
    entries = directory_entries(node, flags)
    print_entries(shell, entries, flags)
    if "R" not in flags:
        return
    for name, child in entries:
        if child.is_dir and name not in (".", ".."):
            sub_path = path.rstrip("/") + "/" + name
            shell.write()
            shell.write(f"{sub_path}:")
            list_directory(shell, sub_path, child, flags)


def resolve_operands(shell, operands):
    """Разрешить операнды ``ls``; вернуть (файлы, каталоги, ошибки)."""
    files, dirs, failed = [], [], False
    for path in operands:
        try:
            node = shell.vfs.resolve(path)
        except VfsError as error:
            report(shell, "ls", f"cannot access {error}")
            failed = True
            continue
        (dirs if node.is_dir else files).append((path, node))
    return files, dirs, failed


def cmd_ls(shell, args):
    """``ls [-alR] [PATH...]`` — вывести содержимое каталогов VFS."""
    flags, operands = parse_options(args, LS_OPTIONS)
    files, dirs, failed = resolve_operands(shell, operands or ["."])
    print_entries(shell, files, flags)
    show_headers = len(operands) > SINGLE_OPERAND or "R" in flags
    for index, (path, node) in enumerate(dirs):
        if index or files:
            shell.write()
        if show_headers:
            shell.write(f"{path}:")
        list_directory(shell, path, node, flags)
    if failed:
        raise CommandError("")


def cmd_cd(shell, args):
    """``cd [PATH | -]`` — сменить текущий каталог VFS.

    Без аргумента выполняется переход в корень VFS (``~``),
    ``cd -`` возвращает в предыдущий каталог.
    """
    if len(args) > CD_MAX_ARGS:
        raise CommandError("too many arguments")
    path = args[0] if args else "~"
    try:
        if path == PREVIOUS_DIR:
            target = shell.vfs.previous
            shell.write(shell.vfs.path_of(target))
        else:
            target = shell.vfs.resolve_dir(path)
    except VfsError as error:
        raise CommandError(str(error)) from error
    shell.vfs.change_dir(target)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
}
