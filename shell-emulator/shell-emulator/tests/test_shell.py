"""Тесты ядра оболочки и встроенных команд."""

import unittest

from emulator.errors import ExitRequest
from tests.helpers import make_shell, run


class ShellTest(unittest.TestCase):
    """Проверки выполнения команд и приглашения."""

    def setUp(self):
        """Создать оболочку с тестовым окружением."""
        self.shell, self.out = make_shell(env={"HOME": "/home/u"})

    def test_prompt_contains_user_and_host(self):
        """Приглашение строится из имени пользователя и хоста."""
        prompt = self.shell.prompt()
        self.assertTrue(prompt.startswith(
            f"{self.shell.user}@{self.shell.host}:"))
        self.assertTrue(prompt.endswith("$ "))

    def test_unknown_command(self):
        """Неизвестная команда даёт код 127."""
        status, output = run(self.shell, self.out, "foo bar")
        self.assertEqual(status, 127)
        self.assertIn("foo: command not found", output)

    def test_parse_error(self):
        """Ошибка разбора выводится и даёт код 1."""
        status, output = run(self.shell, self.out, "ls 'oops")
        self.assertEqual(status, 1)
        self.assertIn("parse error", output)

    def test_empty_line(self):
        """Пустая строка ничего не выводит."""
        _, output = run(self.shell, self.out, "")
        self.assertEqual(output, "")

    def test_exit_with_code(self):
        """exit N завершает работу с кодом N."""
        with self.assertRaises(ExitRequest) as context:
            self.shell.execute("exit 3")
        self.assertEqual(context.exception.code, 3)

    def test_exit_errors(self):
        """Ошибочные вызовы exit не завершают работу."""
        status, output = run(self.shell, self.out, "exit abc")
        self.assertEqual(status, 1)
        self.assertIn("numeric argument required", output)
        status, output = run(self.shell, self.out, "exit 1 2")
        self.assertIn("too many arguments", output)

    def test_interactive_loop(self):
        """REPL читает строки до exit."""
        lines = iter(["", "unknown", "exit 5"])
        code = self.shell.run_interactive(lambda prompt: next(lines))
        self.assertEqual(code, 5)

    def test_interactive_eof(self):
        """Конец ввода завершает REPL с последним кодом."""
        def read_line(prompt):
            """Имитировать конец ввода."""
            raise EOFError
        self.assertEqual(self.shell.run_interactive(read_line), 0)


if __name__ == "__main__":
    unittest.main()
