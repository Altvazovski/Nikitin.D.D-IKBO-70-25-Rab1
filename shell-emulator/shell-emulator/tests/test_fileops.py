"""Тесты команд этапа 5: rmdir, mv, help."""

import unittest

from emulator.commands import COMMANDS
from emulator.commands.fileops import parent_paths
from emulator.commands.help import HELP_TOPICS
from emulator.vfs import DirNode
from tests.helpers import make_shell, make_vfs, run


class FileOpsTestCase(unittest.TestCase):
    """База: оболочка с тестовой VFS."""

    def setUp(self):
        """Создать оболочку с тестовой VFS."""
        self.shell, self.out = make_shell(vfs=make_vfs())
        self.vfs = self.shell.vfs

    def run_line(self, line):
        """Выполнить строку и вернуть (код, вывод)."""
        return run(self.shell, self.out, line)

    def exists(self, path):
        """Проверить существование пути в VFS."""
        return not self.run_line(f"ls {path}")[0]


class RmdirTest(FileOpsTestCase):
    """Команда rmdir."""

    def test_removes_empty_dir(self):
        """Пустой каталог удаляется, -v сообщает об этом."""
        status, output = self.run_line("rmdir -v dir/empty")
        self.assertEqual(status, 0)
        self.assertIn("removing directory, 'dir/empty'", output)
        self.assertFalse(self.exists("dir/empty"))

    def test_parents(self):
        """-p удаляет цепочку, пока каталоги пустые."""
        self.vfs.resolve("/dir/sub/deep").remove("c.txt")
        status, output = self.run_line("rmdir -p dir/sub/deep")
        self.assertEqual(status, 1)
        self.assertIn("'dir': Directory not empty", output)
        self.assertFalse(self.exists("dir/sub"))
        self.assertEqual(parent_paths("a/b/c/"), ["a/b/c", "a/b", "a"])

    def test_errors(self):
        """Все ошибочные случаи rmdir."""
        self.run_line("cd dir/empty")
        cases = (("rmdir", "missing operand"),
                 ("rmdir /nope", "No such file"),
                 ("rmdir /dir/sub", "Directory not empty"),
                 ("rmdir /a.txt", "Not a directory"),
                 ("rmdir .", "Invalid argument"),
                 ("rmdir /dir/empty", "busy"),
                 ("rmdir /", "busy"),
                 ("rmdir -q x", "invalid option"))
        for line, message in cases:
            with self.subTest(line=line):
                status, output = self.run_line(line)
                self.assertEqual(status, 1)
                self.assertIn(message, output)


class MvTest(FileOpsTestCase):
    """Команда mv."""

    def test_rename_file(self):
        """Файл переименовывается, содержимое сохраняется."""
        _, output = self.run_line("mv -v a.txt dir/renamed.txt")
        self.assertEqual(output, "renamed 'a.txt' -> 'dir/renamed.txt'\n")
        self.assertEqual(self.vfs.resolve("/dir/renamed.txt").text(),
                         "line\nline\nother\n")
        self.assertFalse(self.exists("a.txt"))

    def test_move_many_into_dir(self):
        """Несколько источников перемещаются в каталог."""
        self.assertEqual(self.run_line("mv a.txt bin.dat dir/sub")[0], 0)
        self.assertEqual(self.run_line("ls dir/sub")[1],
                         "a.txt  bin.dat  deep\n")

    def test_move_dir_and_cwd(self):
        """Каталог перемещается вместе с содержимым, cwd сохраняется."""
        self.run_line("cd dir/sub/deep")
        self.run_line("mv /dir/sub /moved")
        self.assertEqual(self.vfs.display_cwd(), "~/moved/deep")
        self.assertEqual(self.vfs.resolve("/moved/deep/c.txt").text(),
                         "sea\n")

    def test_replace_empty_dir(self):
        """Каталог перемещается внутрь и может заменить пустой каталог."""
        self.vfs.resolve("/dir/empty").add(DirNode("sub"))
        self.assertEqual(self.run_line("mv dir/sub dir/empty")[0], 0)
        self.assertTrue(self.exists("dir/empty/sub/deep/c.txt"))

    def test_overwrite_and_no_clobber(self):
        """Файл перезаписывается, с -n — нет."""
        self.run_line("mv -n a.txt dir/b.txt")
        self.assertEqual(self.vfs.resolve("/dir/b.txt").text(), "bee\n")
        self.run_line("mv a.txt dir/b.txt")
        self.assertTrue(self.vfs.resolve("/dir/b.txt").text()
                        .startswith("line"))

    def test_errors(self):
        """Все ошибочные случаи mv."""
        cases = (("mv", "missing file operand"),
                 ("mv a.txt", "missing destination"),
                 ("mv nope dir", "cannot stat"),
                 ("mv a.txt bin.dat dir/b.txt", "is not a directory"),
                 ("mv dir dir/sub/x", "subdirectory of itself"),
                 ("mv a.txt a.txt", "are the same file"),
                 ("mv dir/sub a.txt", "cannot overwrite non-directory"),
                 ("mv / dir", "busy"),
                 ("mv a.txt nope/x", "No such file"))
        for line, message in cases:
            with self.subTest(line=line):
                status, output = self.run_line(line)
                self.assertEqual(status, 1)
                self.assertIn(message, output)

    def test_overwrite_dir_errors(self):
        """Нельзя заменить каталог файлом или непустым каталогом."""
        target = self.vfs.resolve("/dir/empty")
        target.add(DirNode("a.txt"))
        target.add(DirNode("sub"))
        self.vfs.write_file("/dir/empty/sub/f.txt", b"x")
        status, output = self.run_line("mv a.txt dir/empty")
        self.assertEqual(status, 1)
        self.assertIn("cannot overwrite directory", output)
        status, output = self.run_line("mv dir/sub dir/empty")
        self.assertEqual(status, 1)
        self.assertIn("Directory not empty", output)


class HelpTest(FileOpsTestCase):
    """Команда help."""

    def test_all_commands_documented(self):
        """У каждой команды есть справка, и help выводит их все."""
        self.assertEqual(set(HELP_TOPICS), set(COMMANDS))
        _, output = self.run_line("help")
        self.assertEqual(len(output.splitlines()), len(COMMANDS))

    def test_topics(self):
        """Справка по отдельным командам и ошибка для неизвестной."""
        _, output = self.run_line("help mv")
        self.assertTrue(output.startswith("mv: mv [-n] [-v]"))
        status, output = self.run_line("help mv nope")
        self.assertEqual(status, 1)
        self.assertIn("no help topics match 'nope'", output)


if __name__ == "__main__":
    unittest.main()
