"""Встроенные команды управления самим эмулятором."""

from emulator.errors import CommandError, ExitRequest

MAX_EXIT_ARGS = 1
EXIT_CODE_MODULO = 256


def cmd_exit(shell, args):
    """``exit [n]`` — завершить работу эмулятора с кодом ``n``.

    Без аргумента используется код возврата последней команды.
    """
    if len(args) > MAX_EXIT_ARGS:
        raise CommandError("too many arguments")
    if not args:
        raise ExitRequest(shell.last_status)
    try:
        code = int(args[0])
    except ValueError as error:
        raise CommandError(
            f"{args[0]}: numeric argument required") from error
    raise ExitRequest(code % EXIT_CODE_MODULO)


COMMANDS = {
    "exit": cmd_exit,
}
