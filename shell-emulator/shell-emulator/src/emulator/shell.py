"""Ядро эмулятора: приглашение, разбор и выполнение команд."""

import getpass
import os
import socket
import sys

from emulator.commands import COMMANDS
from emulator.errors import CommandError, ExitRequest, ParseError
from emulator.lexer import tokenize
from emulator.vfs import VFS

PROGRAM = "emulator"
STATUS_OK = 0
STATUS_ERROR = 1
STATUS_NOT_FOUND = 127


def current_user():
    """Вернуть имя пользователя реальной ОС."""
    try:
        return getpass.getuser()
    except (OSError, KeyError):
        return os.environ.get("USERNAME", "user")


class Shell:
    """Состояние сеанса оболочки и цикл обработки команд."""

    def __init__(self, out=None, env=None, vfs=None):
        """Создать сеанс.

        :param out: поток вывода (по умолчанию ``sys.stdout``).
        :param env: переменные окружения (по умолчанию — реальной ОС).
        :param vfs: виртуальная ФС (по умолчанию — пустая).
        """
        self.vfs = vfs if vfs is not None else VFS()
        self.out = out if out is not None else sys.stdout
        self.env = dict(os.environ) if env is None else env
        self.user = current_user()
        self.host = socket.gethostname()
        self.last_status = STATUS_OK

    def write(self, text=""):
        """Вывести строку текста."""
        self.out.write(text + "\n")
        self.out.flush()

    def cwd_display(self):
        """Вернуть текущий каталог VFS в виде для приглашения."""
        return self.vfs.display_cwd()

    def prompt(self):
        """Сформировать приглашение вида ``user@host:~$``."""
        return f"{self.user}@{self.host}:{self.cwd_display()}$ "

    def variables(self):
        """Вернуть переменные, доступные для подстановки."""
        return {**self.env, "?": self.last_status}

    def execute(self, line):
        """Разобрать и выполнить одну строку.

        :return: код возврата команды.
        :raises ExitRequest: если выполнена команда ``exit``.
        """
        try:
            words = tokenize(line, self.variables())
        except ParseError as error:
            self.write(f"{PROGRAM}: parse error: {error}")
            self.last_status = STATUS_ERROR
            return self.last_status
        if not words:
            return self.last_status
        self.last_status = self._run_command(words[0], words[1:])
        return self.last_status

    def _run_command(self, name, args):
        """Найти команду в реестре и выполнить её."""
        handler = COMMANDS.get(name)
        if handler is None:
            self.write(f"{name}: command not found")
            return STATUS_NOT_FOUND
        try:
            handler(self, args)
        except CommandError as error:
            if str(error):
                self.write(f"{name}: {error}")
            return STATUS_ERROR
        return STATUS_OK

    def run_script(self, lines):
        """Выполнить команды скрипта, имитируя диалог с пользователем.

        Пустые строки и комментарии пропускаются, ошибочные команды
        выводят сообщение, после чего выполнение продолжается.

        :param lines: строки скрипта.
        :return: код завершения, если встретился ``exit``, иначе None.
        """
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            self.out.write(self.prompt() + line + "\n")
            try:
                self.execute(line)
            except ExitRequest as request:
                return request.code
        return None

    def run_interactive(self, read_line=input):
        """Запустить интерактивный цикл REPL.

        :param read_line: функция чтения строки с приглашением.
        :return: код завершения эмулятора.
        """
        while True:
            try:
                line = read_line(self.prompt())
            except EOFError:
                self.write()
                return self.last_status
            except KeyboardInterrupt:
                self.write("^C")
                continue
            try:
                self.execute(line)
            except ExitRequest as request:
                return request.code
