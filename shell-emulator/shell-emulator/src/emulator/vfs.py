"""Виртуальная файловая система (VFS), хранящаяся целиком в памяти.

Источником VFS служит ZIP-архив. Архив только читается: все изменения
выполняются в памяти и попадают на диск лишь по команде ``vfs-save``.
Текстовое содержимое файлов хранится строкой UTF-8, а двоичное —
в кодировке base64.
"""

import base64
import os
import time
import zipfile

from emulator.errors import VfsError

SEP = "/"
HOME = "~"
CURRENT_DIR = "."
PARENT_DIR = ".."
SPECIAL_NAMES = ("", CURRENT_DIR, PARENT_DIR)
DATE_FIELDS = 6
ZIP_MIN_YEAR = 1980


def now_stamp():
    """Вернуть текущее время в формате ``date_time`` ZIP-архива."""
    stamp = time.localtime()[:DATE_FIELDS]
    if stamp[0] < ZIP_MIN_YEAR:
        return (ZIP_MIN_YEAR, 1, 1, 0, 0, 0)
    return stamp


class Node:
    """Общая часть файла и каталога VFS."""

    is_dir = False

    def __init__(self, name, mtime=None):
        """Создать узел с именем ``name`` и временем изменения ``mtime``."""
        self.name = name
        self.parent = None
        self.mtime = tuple(mtime) if mtime else now_stamp()


class FileNode(Node):
    """Файл VFS."""

    def __init__(self, name, data=b"", mtime=None):
        """Создать файл с содержимым ``data`` (bytes)."""
        super().__init__(name, mtime)
        self.binary = False
        self.content = ""
        self.set_data(data)

    def set_data(self, data):
        """Сохранить содержимое: текст как есть, двоичное — в base64."""
        try:
            self.content = data.decode("utf-8")
            self.binary = False
        except UnicodeDecodeError:
            self.content = base64.b64encode(data).decode("ascii")
            self.binary = True

    def data(self):
        """Вернуть содержимое файла в виде bytes."""
        if self.binary:
            return base64.b64decode(self.content)
        return self.content.encode("utf-8")

    def text(self):
        """Вернуть содержимое файла в виде текста."""
        return self.data().decode("utf-8", errors="replace")

    @property
    def size(self):
        """Размер файла в байтах."""
        return len(self.data())


class DirNode(Node):
    """Каталог VFS."""

    is_dir = True

    def __init__(self, name, mtime=None):
        """Создать пустой каталог."""
        super().__init__(name, mtime)
        self.children = {}

    def add(self, node):
        """Добавить дочерний узел."""
        node.parent = self
        self.children[node.name] = node

    def remove(self, name):
        """Удалить и вернуть дочерний узел."""
        node = self.children.pop(name)
        node.parent = None
        return node

    def sorted_children(self):
        """Вернуть дочерние узлы, отсортированные по имени."""
        return [self.children[name] for name in sorted(self.children)]


def split_entry_name(name):
    """Разбить имя элемента ZIP-архива на компоненты пути."""
    parts = [part for part in name.replace("\\", SEP).split(SEP)
             if part not in ("", CURRENT_DIR)]
    if PARENT_DIR in parts:
        raise VfsError(f"unsafe path in archive: {name}")
    return parts


class VFS:
    """Дерево каталогов и файлов с текущим рабочим каталогом."""

    def __init__(self, name="vfs"):
        """Создать пустую VFS с именем ``name``."""
        self.name = name
        self.root = DirNode("")
        self.cwd = self.root
        self.previous = self.root

    @classmethod
    def from_zip(cls, path):
        """Загрузить VFS из ZIP-архива в память.

        :raises VfsError: если архив не найден или повреждён.
        """
        name = os.path.splitext(os.path.basename(path))[0] or "vfs"
        vfs = cls(name)
        try:
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    vfs._load_entry(archive, info)
        except zipfile.BadZipFile as error:
            raise VfsError(f"{path}: not a valid ZIP archive") from error
        except OSError as error:
            raise VfsError(f"{path}: {error.strerror or error}") from error
        return vfs

    def _load_entry(self, archive, info):
        """Добавить в дерево один элемент архива."""
        parts = split_entry_name(info.filename)
        if not parts:
            return
        if info.is_dir():
            self._ensure_dirs(parts, info.date_time)
            return
        parent = self._ensure_dirs(parts[:-1], info.date_time)
        node = FileNode(parts[-1], archive.read(info), info.date_time)
        parent.add(node)

    def _ensure_dirs(self, parts, mtime):
        """Создать (при необходимости) цепочку каталогов ``parts``."""
        node = self.root
        for part in parts:
            child = node.children.get(part)
            if child is None:
                child = DirNode(part, mtime)
                node.add(child)
            elif not child.is_dir:
                raise VfsError(f"archive conflict: {part} is a file")
            node = child
        return node

    def _start_node(self, path):
        """Определить узел, от которого разрешается путь."""
        if path == HOME or path.startswith(HOME + SEP):
            return self.root, path[len(HOME):]
        if path.startswith(SEP):
            return self.root, path
        return self.cwd, path

    def resolve(self, path):
        """Найти узел по абсолютному или относительному пути.

        :raises VfsError: если путь не существует.
        """
        node, rest = self._start_node(path)
        for part in rest.split(SEP):
            if part in ("", CURRENT_DIR):
                continue
            if not node.is_dir:
                raise VfsError(f"{path}: Not a directory")
            if part == PARENT_DIR:
                node = node.parent or self.root
                continue
            child = node.children.get(part)
            if child is None:
                raise VfsError(f"{path}: No such file or directory")
            node = child
        if path.endswith(SEP) and not node.is_dir:
            raise VfsError(f"{path}: Not a directory")
        return node

    def resolve_dir(self, path):
        """Найти каталог по пути.

        :raises VfsError: если путь не существует или это не каталог.
        """
        node = self.resolve(path)
        if not node.is_dir:
            raise VfsError(f"{path}: Not a directory")
        return node

    def split_parent(self, path):
        """Вернуть пару (родительский каталог, имя) для пути."""
        stripped = path.rstrip(SEP)
        head, sep, name = stripped.rpartition(SEP)
        if not sep:
            head = CURRENT_DIR
        elif not head:
            head = SEP
        if name == HOME:
            name = ""
        return self.resolve_dir(head), name

    def write_file(self, path, data):
        """Создать или перезаписать файл с содержимым ``data``.

        :raises VfsError: если путь указывает на каталог.
        """
        parent, name = self.split_parent(path)
        if name in SPECIAL_NAMES:
            raise VfsError(f"{path}: Is a directory")
        node = parent.children.get(name)
        if node is None:
            parent.add(FileNode(name, data))
            return
        if node.is_dir:
            raise VfsError(f"{path}: Is a directory")
        node.set_data(data)
        node.mtime = now_stamp()

    def change_dir(self, node):
        """Сделать каталог ``node`` текущим, запомнив предыдущий."""
        self.previous = self.cwd
        self.cwd = node

    def is_inside(self, node, ancestor):
        """Проверить, лежит ли ``node`` внутри ``ancestor`` (или совпадает)."""
        while node is not None:
            if node is ancestor:
                return True
            node = node.parent
        return False

    def path_of(self, node):
        """Вернуть абсолютный путь узла внутри VFS."""
        names = []
        while node is not None and node is not self.root:
            names.append(node.name)
            node = node.parent
        return SEP + SEP.join(reversed(names))

    def display_cwd(self):
        """Вернуть текущий каталог для приглашения (корень — ``~``)."""
        if self.cwd is self.root:
            return HOME
        return HOME + self.path_of(self.cwd)

    def walk(self, node=None):
        """Обойти дерево в глубину, выдавая пары (путь, узел)."""
        start = node or self.root
        for child in start.sorted_children():
            yield self.path_of(child), child
            if child.is_dir:
                yield from self.walk(child)

    def count(self):
        """Вернуть количество (каталогов, файлов) в VFS."""
        nodes = [node for _, node in self.walk()]
        dirs = sum(1 for node in nodes if node.is_dir)
        return dirs, len(nodes) - dirs

    def save(self, path):
        """Сохранить VFS на диск в виде ZIP-архива.

        :raises VfsError: если файл не удалось записать.
        """
        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                for name, node in self.walk():
                    self._save_entry(archive, name.lstrip(SEP), node)
        except OSError as error:
            raise VfsError(f"{path}: {error.strerror or error}") from error

    @staticmethod
    def _save_entry(archive, name, node):
        """Записать в архив один узел."""
        if node.is_dir:
            info = zipfile.ZipInfo(name + SEP, node.mtime)
            archive.writestr(info, b"")
            return
        info = zipfile.ZipInfo(name, node.mtime)
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, node.data())
