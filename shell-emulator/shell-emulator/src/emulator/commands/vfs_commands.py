"""Служебные команды работы с VFS."""

import os

from emulator.errors import CommandError, VfsError

SAVE_ARGS = 1


def cmd_vfs_save(shell, args):
    """``vfs-save PATH`` — сохранить состояние VFS в ZIP-архив на диске."""
    if not args:
        raise CommandError("missing operand: path to archive")
    if len(args) > SAVE_ARGS:
        raise CommandError("too many arguments")
    try:
        shell.vfs.save(args[0])
    except VfsError as error:
        raise CommandError(str(error)) from error
    shell.write(f"VFS '{shell.vfs.name}' saved to {os.path.abspath(args[0])}")


COMMANDS = {
    "vfs-save": cmd_vfs_save,
}
