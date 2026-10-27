"""Системные команды: ``date`` и ``du``."""

import datetime
import math

from emulator.commands.options import parse_options, report
from emulator.errors import CommandError, VfsError

DATE_OPTIONS = "uI"
DEFAULT_DATE_FORMAT = "%a %b %d %H:%M:%S %Z %Y"
ISO_DATE_FORMAT = "%Y-%m-%d"
FORMAT_PREFIX = "+"
MAX_DATE_OPERANDS = 1

DU_OPTIONS = "ashc"
BLOCK_SIZE = 1024
HUMAN_UNITS = ("K", "M", "G", "T")
ONE_DECIMAL_LIMIT = 10


def current_time(utc):
    """Вернуть текущее время реальной ОС (местное или UTC)."""
    if utc:
        return datetime.datetime.now(datetime.timezone.utc)
    return datetime.datetime.now().astimezone()


def date_format(flags, operands):
    """Определить формат вывода ``date`` по опциям и операндам."""
    if len(operands) > MAX_DATE_OPERANDS:
        raise CommandError(f"extra operand '{operands[MAX_DATE_OPERANDS]}'")
    if operands:
        if not operands[0].startswith(FORMAT_PREFIX):
            raise CommandError(f"invalid date '{operands[0]}'")
        return operands[0][len(FORMAT_PREFIX):]
    if "I" in flags:
        return ISO_DATE_FORMAT
    return DEFAULT_DATE_FORMAT


def cmd_date(shell, args):
    """``date [-u] [-I] [+FORMAT]`` — вывести текущие дату и время."""
    flags, operands = parse_options(args, DATE_OPTIONS)
    fmt = date_format(flags, operands)
    shell.write(current_time("u" in flags).strftime(fmt))


def disk_usage(node):
    """Вернуть занимаемый узлом объём в байтах (рекурсивно)."""
    if not node.is_dir:
        return node.size
    return sum(disk_usage(child) for child in node.children.values())


def blocks(size):
    """Перевести байты в килобайтные блоки с округлением вверх."""
    return math.ceil(size / BLOCK_SIZE)


def human_size(size):
    """Отформатировать размер в стиле ``du -h`` (``0``, ``1.5K``, ``12M``)."""
    if size < BLOCK_SIZE:
        return str(size)
    value = float(size)
    for unit in HUMAN_UNITS:
        value /= BLOCK_SIZE
        if value < BLOCK_SIZE or unit == HUMAN_UNITS[-1]:
            break
    if value < ONE_DECIMAL_LIMIT:
        return f"{math.ceil(value * ONE_DECIMAL_LIMIT) / ONE_DECIMAL_LIMIT}" \
            f"{unit}"
    return f"{math.ceil(value)}{unit}"


def format_size(size, flags):
    """Отформатировать размер согласно опции ``-h``."""
    return human_size(size) if "h" in flags else str(blocks(size))


def du_lines(node, path, flags):
    """Вернуть строки ``(размер, путь)`` для узла в порядке обхода du."""
    lines = []
    if node.is_dir and "s" not in flags:
        for child in node.sorted_children():
            child_path = path.rstrip("/") + "/" + child.name
            if child.is_dir or "a" in flags:
                lines.extend(du_lines(child, child_path, flags))
    lines.append((disk_usage(node), path))
    return lines


def cmd_du(shell, args):
    """``du [-ashc] [PATH...]`` — оценить объём, занимаемый в VFS."""
    flags, operands = parse_options(args, DU_OPTIONS)
    if {"a", "s"} <= flags:
        raise CommandError("cannot both summarize and show all entries")
    total, failed = 0, False
    for path in operands or ["."]:
        try:
            node = shell.vfs.resolve(path)
        except VfsError as error:
            report(shell, "du", f"cannot access {error}")
            failed = True
            continue
        for size, line_path in du_lines(node, path, flags):
            shell.write(f"{format_size(size, flags)}\t{line_path}")
        total += disk_usage(node)
    if "c" in flags:
        shell.write(f"{format_size(total, flags)}\ttotal")
    if failed:
        raise CommandError("")


COMMANDS = {
    "date": cmd_date,
    "du": cmd_du,
}
