"""Лексический разбор командной строки.

Поддерживаются одинарные и двойные кавычки, экранирование обратной
косой чертой, комментарии ``#`` и раскрытие переменных окружения
реальной ОС в формах ``$NAME``, ``${NAME}``, а также ``$?`` (код
возврата последней команды).
"""

import re

from emulator.errors import ParseError

NOT_FOUND = -1
_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SPECIAL_VARS = frozenset("?")
_DQUOTE_ESCAPABLE = '"\\$`'


def tokenize(line, env):
    """Разбить строку на слова, раскрыв переменные окружения.

    Неизвестная переменная раскрывается в пустую строку, как в bash.

    :param line: исходная строка команды.
    :param env: отображение имён переменных в их значения.
    :return: список слов (имя команды и аргументы).
    :raises ParseError: при незакрытой кавычке или ошибке подстановки.
    """
    return _Lexer(line, env).run()


class _Lexer:
    """Конечный автомат разбора одной строки."""

    def __init__(self, line, env):
        """Подготовить разбор строки ``line`` с переменными ``env``."""
        self._line = line
        self._env = env
        self._pos = 0
        self._words = []
        self._chars = []
        self._started = False

    def run(self):
        """Выполнить разбор и вернуть список слов."""
        while self._pos < len(self._line):
            char = self._line[self._pos]
            if char == "#" and not self._started:
                break
            self._dispatch(char)
        self._finish_word()
        return self._words

    def _dispatch(self, char):
        """Обработать очередной символ вне кавычек."""
        if char.isspace():
            self._finish_word()
            self._pos += 1
        elif char == "'":
            self._read_single_quoted()
        elif char == '"':
            self._read_double_quoted()
        elif char == "\\":
            self._read_escape()
        elif char == "$":
            value = self._read_variable()
            if value:
                self._add(value)
        else:
            self._add(char)
            self._pos += 1

    def _add(self, text):
        """Добавить текст к текущему слову."""
        self._chars.append(text)
        self._started = True

    def _finish_word(self):
        """Завершить текущее слово, если оно начато."""
        if self._started:
            self._words.append("".join(self._chars))
        self._chars = []
        self._started = False

    def _read_single_quoted(self):
        """Прочитать строку в одинарных кавычках без подстановок."""
        end = self._line.find("'", self._pos + 1)
        if end == NOT_FOUND:
            raise ParseError("unexpected EOF while looking for matching `''")
        self._add(self._line[self._pos + 1:end])
        self._pos = end + 1

    def _read_double_quoted(self):
        """Прочитать строку в двойных кавычках с подстановками."""
        self._pos += 1
        self._started = True
        while self._pos < len(self._line):
            char = self._line[self._pos]
            if char == '"':
                self._pos += 1
                return
            self._read_in_double_quotes(char)
        raise ParseError("unexpected EOF while looking for matching `\"'")

    def _read_in_double_quotes(self, char):
        """Обработать один символ внутри двойных кавычек."""
        following = self._line[self._pos + 1:self._pos + 2]
        if char == "\\" and following and following in _DQUOTE_ESCAPABLE:
            self._chars.append(following)
            self._pos += 2
        elif char == "$":
            self._chars.append(self._read_variable())
        else:
            self._chars.append(char)
            self._pos += 1

    def _read_escape(self):
        """Обработать экранирование вне кавычек."""
        following = self._line[self._pos + 1:self._pos + 2]
        self._add(following or "\\")
        self._pos += 2

    def _read_variable(self):
        """Прочитать подстановку после ``$`` и вернуть её значение."""
        start = self._pos + 1
        rest = self._line[start:]
        if rest.startswith("{"):
            return self._read_braced(start)
        if rest[:1] and rest[0] in _SPECIAL_VARS:
            self._pos = start + 1
            return self._lookup(rest[0])
        match = _NAME_RE.match(rest)
        if match is None:
            self._pos = start
            return "$"
        self._pos = start + match.end()
        return self._lookup(match.group())

    def _read_braced(self, start):
        """Прочитать подстановку вида ``${NAME}``."""
        end = self._line.find("}", start)
        if end == NOT_FOUND:
            raise ParseError("bad substitution: missing `}'")
        name = self._line[start + 1:end]
        if not (_NAME_RE.fullmatch(name) or name in _SPECIAL_VARS):
            raise ParseError(f"${{{name}}}: bad substitution")
        self._pos = end + 1
        return self._lookup(name)

    def _lookup(self, name):
        """Вернуть значение переменной или пустую строку."""
        return str(self._env.get(name, ""))
