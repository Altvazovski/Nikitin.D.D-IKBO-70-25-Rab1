"""Тесты параметров командной строки и стартового скрипта."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from emulator.app import main, parse_args
from tests.helpers import make_shell


class ParseArgsTest(unittest.TestCase):
    """Разбор параметров командной строки."""

    def test_defaults(self):
        """Без параметров пути не заданы."""
        config = parse_args([])
        self.assertIsNone(config.vfs)
        self.assertIsNone(config.script)

    def test_all_params(self):
        """Оба параметра разбираются."""
        config = parse_args(["--vfs", "a.zip", "--script", "s.txt"])
        self.assertEqual((config.vfs, config.script), ("a.zip", "s.txt"))

    def test_unknown_param(self):
        """Неизвестный параметр приводит к ошибке argparse."""
        with redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit):
            parse_args(["--bad"])


class ScriptTest(unittest.TestCase):
    """Выполнение стартового скрипта."""

    def test_script_echoes_and_skips_errors(self):
        """Скрипт показывает ввод и продолжает работу после ошибок."""
        shell, out = make_shell()
        code = shell.run_script(["# comment", "", "bad", "ls x", "exit 4"])
        self.assertEqual(code, 4)
        lines = out.getvalue().splitlines()
        self.assertTrue(lines[0].endswith("$ bad"))
        self.assertEqual(lines[1], "bad: command not found")
        self.assertTrue(lines[2].endswith("$ ls x"))
        self.assertEqual(lines[3],
                         "ls: cannot access x: No such file or directory")

    def test_script_without_exit(self):
        """Скрипт без exit возвращает None."""
        shell, _ = make_shell()
        self.assertIsNone(shell.run_script(["ls"]))

    def test_main_runs_script_and_prints_config(self):
        """main выводит параметры и выполняет скрипт."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "start.txt")
            with open(path, "w", encoding="utf-8") as script:
                script.write("ls a\nexit 2\n")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = main(["--script", path])
        self.assertEqual(code, 2)
        self.assertIn("start script = " + path, buffer.getvalue())
        self.assertIn("vfs path     = <not set>", buffer.getvalue())

    def test_main_missing_script(self):
        """Несуществующий скрипт даёт код 1."""
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["--script", "/nonexistent/start.txt"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read script", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
