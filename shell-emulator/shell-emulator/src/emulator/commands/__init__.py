"""Реестр команд эмулятора.

Каждая команда — функция ``handler(shell, args)``, которая пишет вывод
через ``shell.write`` и сообщает об ошибках исключением
:class:`emulator.errors.CommandError`.
"""

from emulator.commands import (
    builtins, fileops, help, navigation, system, text, vfs_commands)

COMMANDS = {}
for _module in (builtins, fileops, help, navigation, system, text,
                vfs_commands):
    COMMANDS.update(_module.COMMANDS)
