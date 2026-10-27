"""Разбор коротких опций команд в стиле POSIX (``-la``, ``--``)."""

from emulator.errors import CommandError

OPTION_PREFIX = "-"
END_OF_OPTIONS = "--"


def _is_option(arg):
    """Проверить, является ли аргумент группой коротких опций."""
    return arg.startswith(OPTION_PREFIX) and arg != OPTION_PREFIX


def parse_options(args, allowed):
    """Разделить аргументы на опции и операнды.

    :param args: аргументы команды.
    :param allowed: строка допустимых однобуквенных опций.
    :return: пара (множество опций, список операндов).
    :raises CommandError: при недопустимой опции.
    """
    flags = set()
    operands = []
    rest = list(args)
    while rest:
        arg = rest.pop(0)
        if arg == END_OF_OPTIONS:
            operands.extend(rest)
            break
        if not _is_option(arg):
            operands.append(arg)
            continue
        for letter in arg[1:]:
            if letter not in allowed:
                raise CommandError(f"invalid option -- '{letter}'")
            flags.add(letter)
    return flags, operands


def report(shell, name, message):
    """Вывести сообщение об ошибке команды, не прерывая её работу."""
    shell.write(f"{name}: {message}")
