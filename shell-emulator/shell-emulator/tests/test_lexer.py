"""Тесты разбора командной строки."""

import unittest

from emulator.errors import ParseError
from emulator.lexer import tokenize

ENV = {"HOME": "/home/user", "EMPTY": "", "?": 0}


class TokenizeTest(unittest.TestCase):
    """Проверки функции tokenize."""

    def test_splits_on_whitespace(self):
        """Слова разделяются пробелами и табуляцией."""
        self.assertEqual(tokenize("ls  -l\t/tmp", ENV), ["ls", "-l", "/tmp"])

    def test_empty_line(self):
        """Пустая строка даёт пустой список."""
        self.assertEqual(tokenize("   ", ENV), [])

    def test_expands_variable(self):
        """$NAME заменяется значением."""
        self.assertEqual(tokenize("cd $HOME/docs", ENV),
                         ["cd", "/home/user/docs"])

    def test_expands_braced_variable(self):
        """${NAME} заменяется значением."""
        self.assertEqual(tokenize("ls ${HOME}x", ENV), ["ls", "/home/userx"])

    def test_unknown_variable_is_dropped(self):
        """Неизвестная переменная вне кавычек исчезает."""
        self.assertEqual(tokenize("ls $NOPE", ENV), ["ls"])

    def test_empty_variable_in_quotes(self):
        """Пустая переменная в кавычках даёт пустой аргумент."""
        self.assertEqual(tokenize('ls "$EMPTY"', ENV), ["ls", ""])

    def test_single_quotes_disable_expansion(self):
        """В одинарных кавычках подстановки нет."""
        self.assertEqual(tokenize("ls '$HOME a'", ENV), ["ls", "$HOME a"])

    def test_double_quotes_keep_spaces(self):
        """Двойные кавычки сохраняют пробелы и раскрывают переменные."""
        self.assertEqual(tokenize('cd "$HOME/my dir"', ENV),
                         ["cd", "/home/user/my dir"])

    def test_escape(self):
        """Обратная косая черта экранирует символ."""
        self.assertEqual(tokenize(r"ls a\ b \$HOME", ENV),
                         ["ls", "a b", "$HOME"])

    def test_status_variable(self):
        """$? раскрывается в код возврата."""
        self.assertEqual(tokenize("ls $?", ENV), ["ls", "0"])

    def test_lone_dollar(self):
        """Одиночный $ остаётся как есть."""
        self.assertEqual(tokenize("ls $ 5$", ENV), ["ls", "$", "5$"])

    def test_comment(self):
        """Текст после # в начале слова игнорируется."""
        self.assertEqual(tokenize("ls a#b # comment", ENV), ["ls", "a#b"])

    def test_unclosed_quotes(self):
        """Незакрытые кавычки — ошибка разбора."""
        for line in ("ls 'abc", 'ls "abc'):
            with self.subTest(line=line):
                with self.assertRaises(ParseError):
                    tokenize(line, ENV)

    def test_bad_substitution(self):
        """Ошибочные подстановки ${...}."""
        for line in ("ls ${HOME", "ls ${1x}", "ls ${}"):
            with self.subTest(line=line):
                with self.assertRaises(ParseError):
                    tokenize(line, ENV)


if __name__ == "__main__":
    unittest.main()
