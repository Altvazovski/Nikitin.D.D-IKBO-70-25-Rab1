"""Команда ``help``: справка по командам эмулятора."""

from emulator.errors import CommandError

HELP_TOPICS = {
    "cd": ("cd [PATH | -]",
           "Сменить текущий каталог VFS. Без аргумента — переход в корень "
           "(~), '-' — в предыдущий каталог."),
    "date": ("date [-u] [-I] [+FORMAT]",
             "Вывести текущие дату и время ОС. -u — время UTC, -I — дата "
             "в формате ISO 8601, +FORMAT — формат strftime."),
    "du": ("du [-a] [-s] [-h] [-c] [PATH...]",
           "Оценить объём файлов VFS в килобайтных блоках. -a — показывать "
           "и файлы, -s — только итог по каждому аргументу, -h — в "
           "единицах K/M/G, -c — вывести общий итог."),
    "exit": ("exit [N]",
             "Завершить работу эмулятора с кодом N (по умолчанию — код "
             "последней команды)."),
    "help": ("help [COMMAND...]",
             "Вывести список команд или подробную справку по командам."),
    "ls": ("ls [-a] [-l] [-R] [PATH...]",
           "Вывести содержимое каталогов VFS. -a — включая скрытые и "
           "./.., -l — подробный формат, -R — рекурсивно."),
    "mv": ("mv [-n] [-v] SOURCE... DEST",
           "Переименовать SOURCE в DEST или переместить источники в "
           "каталог DEST (в памяти). -n — не перезаписывать, -v — "
           "сообщать о каждом перемещении."),
    "rmdir": ("rmdir [-p] [-v] DIR...",
              "Удалить пустые каталоги VFS (в памяти). -p — удалить и "
              "родительские каталоги из пути, -v — сообщать о каждом."),
    "uniq": ("uniq [-c] [-d] [-u] [-i] INPUT [OUTPUT]",
             "Убрать соседние повторяющиеся строки файла INPUT. -c — "
             "число повторов, -d — только повторяющиеся, -u — только "
             "уникальные, -i — без учёта регистра. OUTPUT — файл VFS."),
    "vfs-save": ("vfs-save PATH",
                 "Сохранить текущее состояние VFS в ZIP-архив на диске."),
}


def short_description(text):
    """Вернуть первое предложение описания."""
    return text.split(". ")[0].rstrip(".") + "."


def cmd_help(shell, args):
    """``help [COMMAND...]`` — вывести справку по командам."""
    if not args:
        width = max(len(usage) for usage, _ in HELP_TOPICS.values())
        for usage, text in HELP_TOPICS.values():
            shell.write(f"  {usage:<{width}}  {short_description(text)}")
        return
    unknown = [name for name in args if name not in HELP_TOPICS]
    if unknown:
        raise CommandError(f"no help topics match '{unknown[0]}'")
    for name in args:
        usage, text = HELP_TOPICS[name]
        shell.write(f"{name}: {usage}")
        shell.write(f"    {text}")


COMMANDS = {
    "help": cmd_help,
}
