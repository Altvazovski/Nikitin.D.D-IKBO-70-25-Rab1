"""Команды обработки текста: ``uniq``."""

import itertools

from emulator.commands.options import parse_options
from emulator.errors import CommandError, VfsError

UNIQ_OPTIONS = "cdui"
MAX_UNIQ_OPERANDS = 2
SINGLE = 1
COUNT_WIDTH = 7


def read_text(shell, path):
    """Прочитать текстовый файл VFS."""
    try:
        node = shell.vfs.resolve(path)
    except VfsError as error:
        raise CommandError(str(error)) from error
    if node.is_dir:
        raise CommandError(f"{path}: Is a directory")
    return node.text()


def group_lines(lines, ignore_case):
    """Сгруппировать соседние одинаковые строки: [(строка, число)]."""
    key = str.lower if ignore_case else None
    return [(group[0], len(group)) for group in
            (list(items) for _, items in itertools.groupby(lines, key))]


def keep_group(count, flags):
    """Проверить, нужно ли выводить группу строк с учётом -d и -u."""
    if "d" in flags and count == SINGLE:
        return False
    return not ("u" in flags and count > SINGLE)


def format_group(line, count, flags):
    """Отформатировать группу строк (с числом повторов при ``-c``)."""
    if "c" in flags:
        return f"{count:>{COUNT_WIDTH}} {line}"
    return line


def cmd_uniq(shell, args):
    """``uniq [-cdui] INPUT [OUTPUT]`` — убрать соседние повторы строк.

    Если указан OUTPUT, результат записывается в файл VFS (в памяти).
    """
    flags, operands = parse_options(args, UNIQ_OPTIONS)
    if not operands:
        raise CommandError("missing operand: input file")
    if len(operands) > MAX_UNIQ_OPERANDS:
        raise CommandError(f"extra operand '{operands[MAX_UNIQ_OPERANDS]}'")
    lines = read_text(shell, operands[0]).splitlines()
    result = [format_group(line, count, flags)
              for line, count in group_lines(lines, "i" in flags)
              if keep_group(count, flags)]
    if len(operands) < MAX_UNIQ_OPERANDS:
        for line in result:
            shell.write(line)
        return
    data = "".join(line + "\n" for line in result).encode("utf-8")
    try:
        shell.vfs.write_file(operands[1], data)
    except VfsError as error:
        raise CommandError(str(error)) from error


COMMANDS = {
    "uniq": cmd_uniq,
}
