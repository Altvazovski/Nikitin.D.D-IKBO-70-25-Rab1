"""Тесты основных команд этапа 4: ls, cd, date, uniq, du."""

import re
import unittest

from emulator.commands.system import human_size
from tests.helpers import make_shell, make_vfs, run


class CommandTestCase(unittest.TestCase):
    """База: оболочка с тестовой VFS."""

    def setUp(self):
        """Создать оболочку с тестовой VFS."""
        self.shell, self.out = make_shell(vfs=make_vfs())

    def run_line(self, line):
        """Выполнить строку и вернуть (код, вывод)."""
        return run(self.shell, self.out, line)


class LsTest(CommandTestCase):
    """Команда ls."""

    def test_root(self):
        """ls без аргументов выводит текущий каталог."""
        self.assertEqual(self.run_line("ls"), (0, "a.txt  bin.dat  dir\n"))

    def test_all_and_long(self):
        """-a добавляет . и .., -l выводит подробности."""
        _, output = self.run_line("ls -la dir")
        lines = output.splitlines()
        self.assertTrue(lines[0].startswith("drwxr-xr-x"))
        self.assertTrue(lines[0].endswith(" ."))
        self.assertTrue(lines[2].startswith("-rw-r--r--"))
        self.assertTrue(lines[2].endswith(" b.txt"))

    def test_recursive(self):
        """-R обходит подкаталоги."""
        _, output = self.run_line("ls -R dir")
        self.assertIn("dir/sub/deep:\nc.txt\n", output)

    def test_file_and_errors(self):
        """Файл выводится по имени, ошибки не прерывают вывод."""
        status, output = self.run_line("ls a.txt nope")
        self.assertEqual(status, 1)
        self.assertIn("ls: cannot access nope: No such file", output)
        self.assertIn("a.txt\n", output)
        status, output = self.run_line("ls -z")
        self.assertIn("invalid option -- 'z'", output)


class CdTest(CommandTestCase):
    """Команда cd."""

    def test_navigation(self):
        """Переход по относительным путям, .., ~ и -."""
        self.run_line("cd dir/sub")
        self.assertEqual(self.shell.prompt()[-len("~/dir/sub$ "):],
                         "~/dir/sub$ ")
        self.run_line("cd ..")
        self.assertEqual(self.shell.vfs.display_cwd(), "~/dir")
        _, output = self.run_line("cd -")
        self.assertEqual(output, "/dir/sub\n")
        self.run_line("cd")
        self.assertEqual(self.shell.vfs.display_cwd(), "~")

    def test_errors(self):
        """Ошибки cd не меняют текущий каталог."""
        for line, message in (("cd nope", "No such file"),
                              ("cd a.txt", "Not a directory"),
                              ("cd a b", "too many arguments")):
            with self.subTest(line=line):
                status, output = self.run_line(line)
                self.assertEqual(status, 1)
                self.assertIn(message, output)
        self.assertEqual(self.shell.vfs.display_cwd(), "~")


class DateTest(CommandTestCase):
    """Команда date."""

    def test_formats(self):
        """Формат по умолчанию, -I, -u и +FORMAT."""
        _, output = self.run_line("date")
        self.assertRegex(output, r"^\w{3} \w{3} \d{2} \d\d:\d\d:\d\d .+ \d{4}")
        _, output = self.run_line("date -I")
        self.assertRegex(output, r"^\d{4}-\d{2}-\d{2}\n$")
        _, output = self.run_line("date -u +%Z")
        self.assertEqual(output, "UTC\n")
        _, output = self.run_line("date '+year %Y'")
        self.assertTrue(re.fullmatch(r"year \d{4}\n", output))

    def test_errors(self):
        """Ошибочные аргументы date."""
        for line, message in (("date x", "invalid date 'x'"),
                              ("date +%Y y", "extra operand 'y'"),
                              ("date -q", "invalid option")):
            with self.subTest(line=line):
                self.assertIn(message, self.run_line(line)[1])


class UniqTest(CommandTestCase):
    """Команда uniq."""

    def test_modes(self):
        """Обычный режим и опции -c, -d, -u."""
        self.assertEqual(self.run_line("uniq a.txt")[1], "line\nother\n")
        self.assertEqual(self.run_line("uniq -c a.txt")[1],
                         "      2 line\n      1 other\n")
        self.assertEqual(self.run_line("uniq -d a.txt")[1], "line\n")
        self.assertEqual(self.run_line("uniq -u a.txt")[1], "other\n")

    def test_ignore_case(self):
        """-i сравнивает строки без учёта регистра."""
        self.shell.vfs.write_file("/case.txt", b"A\na\nb\n")
        self.assertEqual(self.run_line("uniq -i case.txt")[1], "A\nb\n")

    def test_output_file(self):
        """Результат записывается в файл VFS."""
        self.assertEqual(self.run_line("uniq a.txt dir/out.txt")[0], 0)
        self.assertEqual(self.shell.vfs.resolve("dir/out.txt").text(),
                         "line\nother\n")

    def test_errors(self):
        """Ошибки uniq."""
        for line, message in (("uniq", "missing operand"),
                              ("uniq dir", "Is a directory"),
                              ("uniq nope", "No such file"),
                              ("uniq a.txt dir", "Is a directory"),
                              ("uniq a b c", "extra operand 'c'")):
            with self.subTest(line=line):
                status, output = self.run_line(line)
                self.assertEqual(status, 1)
                self.assertIn(message, output)


class DuTest(CommandTestCase):
    """Команда du."""

    def test_default(self):
        """du выводит каталоги в порядке обхода, корень последним."""
        _, output = self.run_line("du dir")
        self.assertEqual(output.splitlines(), [
            "0\tdir/empty", "1\tdir/sub/deep", "1\tdir/sub", "1\tdir"])

    def test_options(self):
        """-a, -s, -h, -c."""
        _, output = self.run_line("du -a dir/sub")
        self.assertIn("1\tdir/sub/deep/c.txt", output)
        self.assertEqual(self.run_line("du -s dir")[1], "1\tdir\n")
        self.assertEqual(self.run_line("du -sh bin.dat")[1], "256\tbin.dat\n")
        _, output = self.run_line("du -sc a.txt dir")
        self.assertTrue(output.endswith("\ttotal\n"))

    def test_errors(self):
        """Ошибки du."""
        status, output = self.run_line("du nope")
        self.assertEqual(status, 1)
        self.assertIn("cannot access nope", output)
        self.assertIn("cannot both", self.run_line("du -as")[1])

    def test_human_size(self):
        """Форматирование размеров для -h."""
        self.assertEqual(human_size(0), "0")
        self.assertEqual(human_size(1536), "1.5K")
        self.assertEqual(human_size(20 * 1024 * 1024), "20M")


if __name__ == "__main__":
    unittest.main()
