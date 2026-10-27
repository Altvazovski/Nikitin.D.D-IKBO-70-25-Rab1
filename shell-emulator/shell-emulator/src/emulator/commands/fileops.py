"""Команды, изменяющие VFS в памяти: ``rmdir`` и ``mv``."""

from emulator.commands.options import parse_options, report
from emulator.errors import CommandError, VfsError
from emulator.vfs import SEP, SPECIAL_NAMES

RMDIR_OPTIONS = "pv"
MV_OPTIONS = "nv"
MIN_MV_OPERANDS = 2
SINGLE_SOURCE = 1
BUSY = "Device or resource busy"


def check_removable(vfs, path, node):
    """Проверить, что каталог можно удалить командой ``rmdir``."""
    if path.rstrip(SEP).rpartition(SEP)[2] in SPECIAL_NAMES[1:]:
        raise VfsError(f"failed to remove '{path}': Invalid argument")
    if not node.is_dir:
        raise VfsError(f"failed to remove '{path}': Not a directory")
    if node is vfs.root or vfs.is_inside(vfs.cwd, node):
        raise VfsError(f"failed to remove '{path}': {BUSY}")
    if node.children:
        raise VfsError(f"failed to remove '{path}': Directory not empty")


def remove_dir(vfs, path):
    """Удалить один пустой каталог по пути ``path``."""
    try:
        node = vfs.resolve(path)
    except VfsError as error:
        raise VfsError(f"failed to remove {error}") from error
    check_removable(vfs, path, node)
    node.parent.remove(node.name)


def parent_paths(path):
    """Вернуть цепочку путей для ``rmdir -p``: a/b/c, a/b, a."""
    paths = []
    current = path.rstrip(SEP)
    while current and current not in SPECIAL_NAMES:
        paths.append(current)
        current = current.rpartition(SEP)[0]
    return paths or [path]


def cmd_rmdir(shell, args):
    """``rmdir [-p] [-v] DIR...`` — удалить пустые каталоги VFS."""
    flags, operands = parse_options(args, RMDIR_OPTIONS)
    if not operands:
        raise CommandError("missing operand")
    failed = False
    for operand in operands:
        paths = parent_paths(operand) if "p" in flags else [operand]
        try:
            for path in paths:
                remove_dir(shell.vfs, path)
                if "v" in flags:
                    shell.write(f"rmdir: removing directory, '{path}'")
        except VfsError as error:
            report(shell, "rmdir", str(error))
            failed = True
    if failed:
        raise CommandError("")


def existing_dir(vfs, path):
    """Вернуть каталог по пути или None, если это не каталог."""
    try:
        node = vfs.resolve(path)
    except VfsError:
        return None
    return node if node.is_dir else None


def resolve_source(vfs, source):
    """Найти перемещаемый узел ``mv``."""
    try:
        node = vfs.resolve(source)
    except VfsError as error:
        raise VfsError(f"cannot stat {error}") from error
    if node is vfs.root:
        raise VfsError(f"cannot move '{source}': {BUSY}")
    return node


def destination(vfs, node, dest, dest_dir):
    """Определить (каталог, имя, путь для сообщений) цели ``mv``."""
    if dest_dir is not None:
        return dest_dir, node.name, dest.rstrip(SEP) + SEP + node.name
    parent, name = vfs.split_parent(dest)
    if name in SPECIAL_NAMES:
        raise VfsError(f"cannot move to '{dest}': Invalid argument")
    return parent, name, dest


def check_overwrite(vfs, node, existing, source, target):
    """Проверить, можно ли заменить существующий узел ``existing``."""
    if existing.is_dir and not node.is_dir:
        raise VfsError(
            f"cannot overwrite directory '{target}' with non-directory")
    if node.is_dir and not existing.is_dir:
        raise VfsError(f"cannot overwrite non-directory '{target}' "
                       f"with directory '{source}'")
    if existing.is_dir and existing.children:
        raise VfsError(
            f"cannot move '{source}' to '{target}': Directory not empty")
    if existing.is_dir and vfs.is_inside(vfs.cwd, existing):
        raise VfsError(f"cannot move '{source}' to '{target}': {BUSY}")


def move_one(vfs, source, dest, dest_dir, no_clobber):
    """Переместить или переименовать один узел.

    :return: путь назначения или None, если перемещение пропущено.
    """
    node = resolve_source(vfs, source)
    parent, name, target = destination(vfs, node, dest, dest_dir)
    existing = parent.children.get(name)
    if existing is node:
        raise VfsError(f"'{source}' and '{target}' are the same file")
    if node.is_dir and vfs.is_inside(parent, node):
        raise VfsError(f"cannot move '{source}' to a subdirectory "
                       f"of itself, '{target}'")
    if existing is not None:
        if no_clobber:
            return None
        check_overwrite(vfs, node, existing, source, target)
        parent.remove(name)
    node.parent.remove(node.name)
    node.name = name
    parent.add(node)
    return target


def cmd_mv(shell, args):
    """``mv [-n] [-v] SOURCE... DEST`` — переместить или переименовать."""
    flags, operands = parse_options(args, MV_OPTIONS)
    if not operands:
        raise CommandError("missing file operand")
    if len(operands) < MIN_MV_OPERANDS:
        raise CommandError(
            f"missing destination file operand after '{operands[0]}'")
    *sources, dest = operands
    dest_dir = existing_dir(shell.vfs, dest)
    if dest_dir is None and len(sources) > SINGLE_SOURCE:
        raise CommandError(f"target '{dest}' is not a directory")
    failed = False
    for source in sources:
        try:
            target = move_one(shell.vfs, source, dest, dest_dir, "n" in flags)
        except VfsError as error:
            report(shell, "mv", str(error))
            failed = True
            continue
        if target is not None and "v" in flags:
            shell.write(f"renamed '{source}' -> '{target}'")
    if failed:
        raise CommandError("")


COMMANDS = {
    "rmdir": cmd_rmdir,
    "mv": cmd_mv,
}
