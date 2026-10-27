"""Тесты виртуальной файловой системы и команды vfs-save."""

import os
import tempfile
import unittest
import zipfile

from emulator.errors import VfsError
from emulator.vfs import VFS
from tests.helpers import SAMPLE_ENTRIES, make_shell, make_vfs, run, write_zip


class LoadTest(unittest.TestCase):
    """Загрузка VFS из ZIP-архива."""

    def test_tree_is_loaded_in_memory(self):
        """Файлы и каталоги всех уровней попадают в дерево."""
        vfs = make_vfs()
        self.assertEqual(vfs.resolve("/dir/sub/deep/c.txt").text(), "sea\n")
        self.assertTrue(vfs.resolve("/dir/empty").is_dir)
        self.assertEqual(vfs.count(), (4, 4))

    def test_binary_data_is_base64(self):
        """Двоичный файл хранится в base64 и восстанавливается точно."""
        node = make_vfs().resolve("/bin.dat")
        self.assertTrue(node.binary)
        self.assertEqual(node.data(), bytes(range(256)))
        self.assertEqual(node.size, 256)

    def test_empty_archive(self):
        """Пустой архив даёт пустую VFS."""
        self.assertEqual(make_vfs({}).count(), (0, 0))

    def test_load_errors(self):
        """Отсутствующий и повреждённый архивы вызывают VfsError."""
        with tempfile.TemporaryDirectory() as tmp:
            broken = os.path.join(tmp, "broken.zip")
            with open(broken, "w", encoding="utf-8") as file:
                file.write("not a zip")
            for path in (os.path.join(tmp, "missing.zip"), broken, tmp):
                with self.subTest(path=path), self.assertRaises(VfsError):
                    VFS.from_zip(path)

    def test_unsafe_names_rejected(self):
        """Элементы с '..' в пути отклоняются."""
        with self.assertRaises(VfsError):
            make_vfs({"../evil.txt": "x"})

    def test_archive_is_not_modified(self):
        """Загрузка не изменяет исходный архив."""
        with tempfile.TemporaryDirectory() as tmp:
            path = write_zip(os.path.join(tmp, "t.zip"))
            before = os.path.getmtime(path), os.path.getsize(path)
            VFS.from_zip(path)
            self.assertEqual(before,
                             (os.path.getmtime(path), os.path.getsize(path)))


class ResolveTest(unittest.TestCase):
    """Разрешение путей."""

    def setUp(self):
        """Загрузить тестовую VFS."""
        self.vfs = make_vfs()

    def test_relative_and_special(self):
        """Работают относительные пути, '.', '..' и '~'."""
        self.vfs.cwd = self.vfs.resolve("/dir/sub")
        self.assertEqual(self.vfs.resolve("deep/c.txt").name, "c.txt")
        self.assertEqual(self.vfs.resolve("../b.txt").name, "b.txt")
        self.assertIs(self.vfs.resolve("~"), self.vfs.root)
        self.assertIs(self.vfs.resolve("/../.."), self.vfs.root)
        self.assertEqual(self.vfs.resolve("~/a.txt").name, "a.txt")

    def test_errors(self):
        """Несуществующие пути и путь через файл — ошибки."""
        for path in ("/nope", "a.txt/x", "a.txt/"):
            with self.subTest(path=path), self.assertRaises(VfsError):
                self.vfs.resolve(path)

    def test_display_cwd(self):
        """Корень VFS показывается как '~'."""
        self.assertEqual(self.vfs.display_cwd(), "~")
        self.vfs.cwd = self.vfs.resolve("/dir/sub")
        self.assertEqual(self.vfs.display_cwd(), "~/dir/sub")
        self.assertEqual(self.vfs.path_of(self.vfs.cwd), "/dir/sub")


class SaveTest(unittest.TestCase):
    """Команда vfs-save."""

    def test_round_trip(self):
        """Сохранённый архив содержит те же данные."""
        shell, out = make_shell(vfs=make_vfs())
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "saved.zip")
            status, output = run(shell, out, f"vfs-save {target}")
            self.assertEqual(status, 0)
            self.assertIn("saved to", output)
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(archive.read("bin.dat"),
                                 SAMPLE_ENTRIES["bin.dat"])
                self.assertIn("dir/empty/", archive.namelist())
            reloaded = VFS.from_zip(target)
        self.assertEqual(reloaded.count(), (4, 4))

    def test_errors(self):
        """Ошибки аргументов и записи."""
        shell, out = make_shell()
        for line, message in (("vfs-save", "missing operand"),
                              ("vfs-save a b", "too many arguments"),
                              ("vfs-save /no/such/dir/x.zip", "No such")):
            with self.subTest(line=line):
                status, output = run(shell, out, line)
                self.assertEqual(status, 1)
                self.assertIn(message, output)


if __name__ == "__main__":
    unittest.main()
