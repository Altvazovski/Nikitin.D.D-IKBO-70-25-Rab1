# Эмулятор командной оболочки UNIX (вариант 14)

## 1. Общее описание

Консольный (CLI) эмулятор языка оболочки UNIX-подобной ОС, написанный на
Python 3.8+ без сторонних зависимостей. Работа максимально похожа на сеанс в
терминале: приглашение `пользователь@хост:~$` строится по данным реальной ОС,
поддерживаются кавычки и переменные окружения, команды выводят сообщения об
ошибках в стиле GNU coreutils.

Эмулятор работает с виртуальной файловой системой (VFS), которая загружается
из ZIP-архива целиком в память. Архив никогда не распаковывается и не
изменяется: команды `mv`, `rmdir` и `uniq ... OUTPUT` меняют только данные в
памяти, а записать результат на диск можно командой `vfs-save`.

Структура репозитория:

```
src/emulator/            исходный код
  app.py                 параметры командной строки, запуск
  shell.py               приглашение, REPL, выполнение скриптов
  lexer.py               разбор строки, раскрытие переменных
  vfs.py                 виртуальная файловая система в памяти
  commands/              реализация команд
tests/                   модульные тесты (unittest)
examples/                стартовые скрипты эмулятора для этапов 2-5
scripts/                 скрипты ОС для проверки (.sh и .bat),
                         генератор образов VFS make_vfs.py
run.sh, run.bat          запуск эмулятора
Makefile                 цели run, test, lint, vfs, demo
```

## 2. Функции и настройки

### Параметры командной строки

* `--vfs PATH` — путь к ZIP-архиву с VFS. Без параметра используется
  пустая VFS. Если архив отсутствует или повреждён, эмулятор сообщает об
  ошибке и завершается с кодом 1.
* `--script PATH` — стартовый скрипт с командами эмулятора.
* `-h`, `--help` — справка по параметрам.

При запуске выводится отладочная информация обо всех параметрах и о
загруженной VFS (число каталогов и файлов).

### Стартовый скрипт

Команды выполняются последовательно. Для каждой строки выводятся
приглашение, сама команда и её результат — как в диалоге с пользователем.
Ошибочные строки выводят сообщение об ошибке и пропускаются, выполнение
продолжается. Пустые строки и строки-комментарии (`# ...`) игнорируются.
Команда `exit` завершает работу эмулятора; если её нет, после скрипта
начинается интерактивный режим.

### Разбор командной строки

* слова разделяются пробелами и табуляцией;
* `'...'` — строка без подстановок, `"..."` — строка с подстановками;
* `\` экранирует следующий символ;
* `$NAME`, `${NAME}` — переменные окружения реальной ОС (неизвестная
  переменная раскрывается в пустую строку), `$?` — код возврата последней
  команды;
* `#` в начале слова начинает комментарий;
* незакрытые кавычки и ошибки `${...}` дают сообщение `parse error`.

Короткие опции команд можно объединять (`ls -la`), `--` завершает опции.

### VFS

* источник — ZIP-архив, загружаемый в память без распаковки;
* текстовые файлы хранятся строкой UTF-8, двоичные — в base64;
* пути: абсолютные (`/a/b`), относительные (`a/b`), `.`, `..`, `~`
  (корень VFS); в приглашении корень показывается как `~`.

### Команды

* `ls [-a] [-l] [-R] [PATH...]` — содержимое каталогов. `-a` — показать
  скрытые файлы и `.`/`..`; `-l` — подробный формат (права, владелец,
  размер, дата; для каталога размер — число элементов); `-R` — рекурсивно.
* `cd [PATH | -]` — сменить каталог. Без аргумента — в корень `~`,
  `cd -` — в предыдущий каталог.
* `date [-u] [-I] [+FORMAT]` — текущие дата и время ОС. `-u` — UTC,
  `-I` — дата ISO 8601, `+FORMAT` — формат strftime (`date +%H:%M`).
* `uniq [-c] [-d] [-u] [-i] INPUT [OUTPUT]` — убрать соседние повторы строк
  файла. `-c` — число повторов, `-d` — только повторяющиеся строки,
  `-u` — только уникальные, `-i` — без учёта регистра. Если указан
  `OUTPUT`, результат записывается в файл VFS.
* `du [-a] [-s] [-h] [-c] [PATH...]` — объём в килобайтных блоках
  (по сумме размеров файлов). `-a` — выводить и файлы, `-s` — только итог
  по каждому аргументу, `-h` — в единицах K/M/G, `-c` — общий итог.
* `rmdir [-p] [-v] DIR...` — удалить пустые каталоги. `-p` — удалить и
  родительские каталоги из пути, `-v` — сообщать о каждом удалении.
  Нельзя удалить корень, текущий каталог и его предков.
* `mv [-n] [-v] SOURCE... DEST` — переименовать или переместить файлы и
  каталоги. Если `DEST` — существующий каталог, источники перемещаются в
  него. `-n` — не перезаписывать существующие файлы, `-v` — сообщать о
  каждом перемещении. Проверяются перемещение каталога в самого себя,
  замена каталога файлом и наоборот, непустой каталог назначения.
* `help [COMMAND...]` — список команд или подробная справка.
* `vfs-save PATH` — сохранить текущее состояние VFS в ZIP-архив на диске.
* `exit [N]` — завершить работу с кодом `N` (по умолчанию — код
  последней команды).

Коды возврата команд: 0 — успех, 1 — ошибка, 127 — команда не найдена.

## 3. Сборка и тесты

Сборка не требуется, нужен только Python 3.8+.

```sh
./run.sh [--vfs PATH] [--script PATH]     # Linux / macOS
run.bat [--vfs PATH] [--script PATH]      # Windows

python3 scripts/make_vfs.py               # создать тестовые образы в vfs/
make test                                 # тесты
python3 -m unittest discover -s tests -t .   # тесты без make
make lint                                 # flake8 и radon (если установлены)
```

Тестовые образы VFS не хранятся в репозитории и создаются скриптом
`scripts/make_vfs.py`: `minimal.zip` (один файл), `multi.zip` (несколько
файлов, включая двоичный), `deep.zip` (не менее 3 уровней вложенности),
`empty.zip` (пустой архив) и `broken.zip` (не ZIP-архив).

Скрипты проверки по этапам (у каждого `.sh` есть аналог `.bat`):

* этап 2: `scripts/config_no_args.sh`, `scripts/config_vfs.sh`,
  `scripts/config_script.sh` — все параметры командной строки;
* этап 3: `scripts/vfs_minimal.sh`, `scripts/vfs_multi.sh`,
  `scripts/vfs_deep.sh`, `scripts/vfs_errors.sh` — разные варианты VFS;
* этап 4: `scripts/stage4.sh` — `ls`, `cd`, `date`, `uniq`, `du`;
* этап 5: `scripts/stage5.sh` — `rmdir`, `mv`, `help`.

## 4. Примеры использования

```
$ ./run.sh --vfs vfs/deep.zip
[debug] emulator configuration:
[debug]   vfs path     = /home/student/shell-emulator/vfs/deep.zip
[debug]   start script = <not set>
[debug]   vfs loaded   = 'deep': 12 directories, 7 files
student@laptop:~$ ls
bin  etc  home  tmp  var
student@laptop:~$ cd home/user/docs
student@laptop:~/home/user/docs$ ls -l
drwxr-xr-x student student        2 Sep 01 12:00 drafts
-rw-r--r-- student student       24 Sep 01 12:00 report.txt
student@laptop:~/home/user/docs$ cd
student@laptop:~$ uniq -c var/log/syslog
      2 boot ok
      3 net up
      1 disk full
      ...
student@laptop:~$ du -sh bin etc
2.0K    bin
22      etc
student@laptop:~$ mv -v etc/config bin
renamed 'etc/config' -> 'bin/config'
student@laptop:~$ rmdir etc home
rmdir: failed to remove 'home': Directory not empty
student@laptop:~$ echo $HOME
echo: command not found
student@laptop:~$ ls "$HOME
emulator: parse error: unexpected EOF while looking for matching `"'
student@laptop:~$ vfs-save out/result.zip
VFS 'deep' saved to /home/student/shell-emulator/out/result.zip
student@laptop:~$ exit
```

Выполнение стартового скрипта:

```
$ ./run.sh --vfs vfs/deep.zip --script examples/stage5.txt
```

## 5. Исходный код

### `src/emulator/__init__.py`

```python
"""Эмулятор командной оболочки UNIX-подобной ОС."""

__version__ = "1.0.0"
```

### `src/emulator/__main__.py`

```python
"""Точка входа: ``python -m emulator``."""

import sys

from emulator.app import main

sys.exit(main())
```

### `src/emulator/app.py`

```python
"""Запуск эмулятора из командной строки."""

import argparse
import os

from emulator.errors import VfsError
from emulator.shell import PROGRAM, STATUS_ERROR, Shell
from emulator.vfs import VFS

try:
    import readline  # noqa: F401  (история и редактирование ввода)
except ImportError:
    readline = None

NOT_SET = "<not set>"


def parse_args(argv=None):
    """Разобрать параметры командной строки эмулятора."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Эмулятор командной оболочки UNIX-подобной ОС.")
    parser.add_argument(
        "--vfs", metavar="PATH",
        help="путь к физическому расположению VFS (ZIP-архив)")
    parser.add_argument(
        "--script", metavar="PATH",
        help="путь к стартовому скрипту с командами эмулятора")
    return parser.parse_args(argv)


def describe_path(path):
    """Вернуть путь в виде для отладочного вывода."""
    if path is None:
        return NOT_SET
    return os.path.abspath(path)


def print_config(config, write):
    """Вывести отладочную информацию о всех параметрах запуска."""
    write("[debug] emulator configuration:")
    write(f"[debug]   vfs path     = {describe_path(config.vfs)}")
    write(f"[debug]   start script = {describe_path(config.script)}")


def read_script(path):
    """Прочитать стартовый скрипт и вернуть список строк."""
    with open(path, encoding="utf-8") as script:
        return script.read().splitlines()


def run_start_script(shell, path):
    """Выполнить стартовый скрипт.

    :return: код завершения, если скрипт завершил работу, иначе None.
    """
    try:
        lines = read_script(path)
    except (OSError, UnicodeDecodeError) as error:
        reason = getattr(error, "strerror", None) or error
        shell.write(f"{PROGRAM}: cannot read script '{path}': {reason}")
        return STATUS_ERROR
    return shell.run_script(lines)


def load_vfs(path):
    """Загрузить VFS из архива или создать пустую, если путь не задан."""
    if path is None:
        return VFS()
    return VFS.from_zip(path)


def print_vfs_info(vfs, write):
    """Вывести отладочную информацию о загруженной VFS."""
    dirs, files = vfs.count()
    write(f"[debug]   vfs loaded   = '{vfs.name}': "
          f"{dirs} directories, {files} files")


def main(argv=None):
    """Запустить эмулятор и вернуть код завершения."""
    config = parse_args(argv)
    shell = Shell()
    print_config(config, shell.write)
    try:
        shell.vfs = load_vfs(config.vfs)
    except VfsError as error:
        shell.write(f"{PROGRAM}: cannot load VFS: {error}")
        return STATUS_ERROR
    print_vfs_info(shell.vfs, shell.write)
    if config.script is not None:
        code = run_start_script(shell, config.script)
        if code is not None:
            return code
    return shell.run_interactive()
```

### `src/emulator/shell.py`

```python
"""Ядро эмулятора: приглашение, разбор и выполнение команд."""

import getpass
import os
import socket
import sys

from emulator.commands import COMMANDS
from emulator.errors import CommandError, ExitRequest, ParseError
from emulator.lexer import tokenize
from emulator.vfs import VFS

PROGRAM = "emulator"
STATUS_OK = 0
STATUS_ERROR = 1
STATUS_NOT_FOUND = 127


def current_user():
    """Вернуть имя пользователя реальной ОС."""
    try:
        return getpass.getuser()
    except (OSError, KeyError):
        return os.environ.get("USERNAME", "user")


class Shell:
    """Состояние сеанса оболочки и цикл обработки команд."""

    def __init__(self, out=None, env=None, vfs=None):
        """Создать сеанс.

        :param out: поток вывода (по умолчанию ``sys.stdout``).
        :param env: переменные окружения (по умолчанию — реальной ОС).
        :param vfs: виртуальная ФС (по умолчанию — пустая).
        """
        self.vfs = vfs if vfs is not None else VFS()
        self.out = out if out is not None else sys.stdout
        self.env = dict(os.environ) if env is None else env
        self.user = current_user()
        self.host = socket.gethostname()
        self.last_status = STATUS_OK

    def write(self, text=""):
        """Вывести строку текста."""
        self.out.write(text + "\n")
        self.out.flush()

    def cwd_display(self):
        """Вернуть текущий каталог VFS в виде для приглашения."""
        return self.vfs.display_cwd()

    def prompt(self):
        """Сформировать приглашение вида ``user@host:~$``."""
        return f"{self.user}@{self.host}:{self.cwd_display()}$ "

    def variables(self):
        """Вернуть переменные, доступные для подстановки."""
        return {**self.env, "?": self.last_status}

    def execute(self, line):
        """Разобрать и выполнить одну строку.

        :return: код возврата команды.
        :raises ExitRequest: если выполнена команда ``exit``.
        """
        try:
            words = tokenize(line, self.variables())
        except ParseError as error:
            self.write(f"{PROGRAM}: parse error: {error}")
            self.last_status = STATUS_ERROR
            return self.last_status
        if not words:
            return self.last_status
        self.last_status = self._run_command(words[0], words[1:])
        return self.last_status

    def _run_command(self, name, args):
        """Найти команду в реестре и выполнить её."""
        handler = COMMANDS.get(name)
        if handler is None:
            self.write(f"{name}: command not found")
            return STATUS_NOT_FOUND
        try:
            handler(self, args)
        except CommandError as error:
            if str(error):
                self.write(f"{name}: {error}")
            return STATUS_ERROR
        return STATUS_OK

    def run_script(self, lines):
        """Выполнить команды скрипта, имитируя диалог с пользователем.

        Пустые строки и комментарии пропускаются, ошибочные команды
        выводят сообщение, после чего выполнение продолжается.

        :param lines: строки скрипта.
        :return: код завершения, если встретился ``exit``, иначе None.
        """
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            self.out.write(self.prompt() + line + "\n")
            try:
                self.execute(line)
            except ExitRequest as request:
                return request.code
        return None

    def run_interactive(self, read_line=input):
        """Запустить интерактивный цикл REPL.

        :param read_line: функция чтения строки с приглашением.
        :return: код завершения эмулятора.
        """
        while True:
            try:
                line = read_line(self.prompt())
            except EOFError:
                self.write()
                return self.last_status
            except KeyboardInterrupt:
                self.write("^C")
                continue
            try:
                self.execute(line)
            except ExitRequest as request:
                return request.code
```

### `src/emulator/lexer.py`

```python
"""Лексический разбор командной строки.

Поддерживаются одинарные и двойные кавычки, экранирование обратной
косой чертой, комментарии ``#`` и раскрытие переменных окружения
реальной ОС в формах ``$NAME``, ``${NAME}``, а также ``$?`` (код
возврата последней команды).
"""

import re

from emulator.errors import ParseError

NOT_FOUND = -1
_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SPECIAL_VARS = frozenset("?")
_DQUOTE_ESCAPABLE = '"\\$`'


def tokenize(line, env):
    """Разбить строку на слова, раскрыв переменные окружения.

    Неизвестная переменная раскрывается в пустую строку, как в bash.

    :param line: исходная строка команды.
    :param env: отображение имён переменных в их значения.
    :return: список слов (имя команды и аргументы).
    :raises ParseError: при незакрытой кавычке или ошибке подстановки.
    """
    return _Lexer(line, env).run()


class _Lexer:
    """Конечный автомат разбора одной строки."""

    def __init__(self, line, env):
        """Подготовить разбор строки ``line`` с переменными ``env``."""
        self._line = line
        self._env = env
        self._pos = 0
        self._words = []
        self._chars = []
        self._started = False

    def run(self):
        """Выполнить разбор и вернуть список слов."""
        while self._pos < len(self._line):
            char = self._line[self._pos]
            if char == "#" and not self._started:
                break
            self._dispatch(char)
        self._finish_word()
        return self._words

    def _dispatch(self, char):
        """Обработать очередной символ вне кавычек."""
        if char.isspace():
            self._finish_word()
            self._pos += 1
        elif char == "'":
            self._read_single_quoted()
        elif char == '"':
            self._read_double_quoted()
        elif char == "\\":
            self._read_escape()
        elif char == "$":
            value = self._read_variable()
            if value:
                self._add(value)
        else:
            self._add(char)
            self._pos += 1

    def _add(self, text):
        """Добавить текст к текущему слову."""
        self._chars.append(text)
        self._started = True

    def _finish_word(self):
        """Завершить текущее слово, если оно начато."""
        if self._started:
            self._words.append("".join(self._chars))
        self._chars = []
        self._started = False

    def _read_single_quoted(self):
        """Прочитать строку в одинарных кавычках без подстановок."""
        end = self._line.find("'", self._pos + 1)
        if end == NOT_FOUND:
            raise ParseError("unexpected EOF while looking for matching `''")
        self._add(self._line[self._pos + 1:end])
        self._pos = end + 1

    def _read_double_quoted(self):
        """Прочитать строку в двойных кавычках с подстановками."""
        self._pos += 1
        self._started = True
        while self._pos < len(self._line):
            char = self._line[self._pos]
            if char == '"':
                self._pos += 1
                return
            self._read_in_double_quotes(char)
        raise ParseError("unexpected EOF while looking for matching `\"'")

    def _read_in_double_quotes(self, char):
        """Обработать один символ внутри двойных кавычек."""
        following = self._line[self._pos + 1:self._pos + 2]
        if char == "\\" and following and following in _DQUOTE_ESCAPABLE:
            self._chars.append(following)
            self._pos += 2
        elif char == "$":
            self._chars.append(self._read_variable())
        else:
            self._chars.append(char)
            self._pos += 1

    def _read_escape(self):
        """Обработать экранирование вне кавычек."""
        following = self._line[self._pos + 1:self._pos + 2]
        self._add(following or "\\")
        self._pos += 2

    def _read_variable(self):
        """Прочитать подстановку после ``$`` и вернуть её значение."""
        start = self._pos + 1
        rest = self._line[start:]
        if rest.startswith("{"):
            return self._read_braced(start)
        if rest[:1] and rest[0] in _SPECIAL_VARS:
            self._pos = start + 1
            return self._lookup(rest[0])
        match = _NAME_RE.match(rest)
        if match is None:
            self._pos = start
            return "$"
        self._pos = start + match.end()
        return self._lookup(match.group())

    def _read_braced(self, start):
        """Прочитать подстановку вида ``${NAME}``."""
        end = self._line.find("}", start)
        if end == NOT_FOUND:
            raise ParseError("bad substitution: missing `}'")
        name = self._line[start + 1:end]
        if not (_NAME_RE.fullmatch(name) or name in _SPECIAL_VARS):
            raise ParseError(f"${{{name}}}: bad substitution")
        self._pos = end + 1
        return self._lookup(name)

    def _lookup(self, name):
        """Вернуть значение переменной или пустую строку."""
        return str(self._env.get(name, ""))
```

### `src/emulator/errors.py`

```python
"""Исключения, используемые эмулятором."""


class ShellError(Exception):
    """Базовая ошибка эмулятора."""


class ParseError(ShellError):
    """Ошибка синтаксического разбора командной строки."""


class CommandError(ShellError):
    """Ошибка выполнения команды (выводится как ``имя: сообщение``).

    Пустое сообщение означает, что команда уже сообщила об ошибках сама
    и нужно лишь вернуть ненулевой код.
    """


class ExitRequest(Exception):
    """Запрос на завершение работы эмулятора с заданным кодом."""

    def __init__(self, code):
        """Сохранить код завершения.

        :param code: код возврата процесса.
        """
        super().__init__(code)
        self.code = code


class VfsError(ShellError):
    """Ошибка работы с виртуальной файловой системой."""
```

### `src/emulator/vfs.py`

```python
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
```

### `src/emulator/commands/__init__.py`

```python
"""Реестр команд эмулятора.

Каждая команда — функция ``handler(shell, args)``, которая пишет вывод
через ``shell.write`` и сообщает об ошибках исключением
:class:`emulator.errors.CommandError`.
"""

from emulator.commands import (
    builtins, fileops, help, navigation, system, text, vfs_commands)

COMMANDS = {}
for _module in (builtins, fileops, help, navigation, system, text,
                vfs_commands):
    COMMANDS.update(_module.COMMANDS)
```

### `src/emulator/commands/options.py`

```python
"""Разбор коротких опций команд в стиле POSIX (``-la``, ``--``)."""

from emulator.errors import CommandError

OPTION_PREFIX = "-"
END_OF_OPTIONS = "--"


def _is_option(arg):
    """Проверить, является ли аргумент группой коротких опций."""
    return arg.startswith(OPTION_PREFIX) and arg != OPTION_PREFIX


def parse_options(args, allowed):
    """Разделить аргументы на опции и операнды.

    :param args: аргументы команды.
    :param allowed: строка допустимых однобуквенных опций.
    :return: пара (множество опций, список операндов).
    :raises CommandError: при недопустимой опции.
    """
    flags = set()
    operands = []
    rest = list(args)
    while rest:
        arg = rest.pop(0)
        if arg == END_OF_OPTIONS:
            operands.extend(rest)
            break
        if not _is_option(arg):
            operands.append(arg)
            continue
        for letter in arg[1:]:
            if letter not in allowed:
                raise CommandError(f"invalid option -- '{letter}'")
            flags.add(letter)
    return flags, operands


def report(shell, name, message):
    """Вывести сообщение об ошибке команды, не прерывая её работу."""
    shell.write(f"{name}: {message}")
```

### `src/emulator/commands/builtins.py`

```python
"""Встроенные команды управления самим эмулятором."""

from emulator.errors import CommandError, ExitRequest

MAX_EXIT_ARGS = 1
EXIT_CODE_MODULO = 256


def cmd_exit(shell, args):
    """``exit [n]`` — завершить работу эмулятора с кодом ``n``.

    Без аргумента используется код возврата последней команды.
    """
    if len(args) > MAX_EXIT_ARGS:
        raise CommandError("too many arguments")
    if not args:
        raise ExitRequest(shell.last_status)
    try:
        code = int(args[0])
    except ValueError as error:
        raise CommandError(
            f"{args[0]}: numeric argument required") from error
    raise ExitRequest(code % EXIT_CODE_MODULO)


COMMANDS = {
    "exit": cmd_exit,
}
```

### `src/emulator/commands/navigation.py`

```python
"""Команды навигации по VFS: ``ls`` и ``cd``."""

import time

from emulator.commands.options import parse_options, report
from emulator.errors import CommandError, VfsError

LS_OPTIONS = "alR"
CD_MAX_ARGS = 1
SINGLE_OPERAND = 1
PREVIOUS_DIR = "-"
HIDDEN_PREFIX = "."
DIR_MODE = "drwxr-xr-x"
FILE_MODE = "-rw-r--r--"
SIZE_WIDTH = 8
TIME_FORMAT = "%b %d %H:%M"
TIME_PADDING = (0, 0, -1)


def format_mtime(mtime):
    """Отформатировать время изменения узла в стиле ``ls -l``."""
    return time.strftime(TIME_FORMAT, tuple(mtime) + TIME_PADDING)


def format_long(shell, node, name):
    """Сформировать строку длинного формата ``ls -l``."""
    mode = DIR_MODE if node.is_dir else FILE_MODE
    size = len(node.children) if node.is_dir else node.size
    owner = shell.user
    return (f"{mode} {owner} {owner} {size:>{SIZE_WIDTH}} "
            f"{format_mtime(node.mtime)} {name}")


def directory_entries(directory, flags):
    """Вернуть пары (имя, узел) содержимого каталога для ``ls``."""
    entries = []
    if "a" in flags:
        entries.append((".", directory))
        entries.append(("..", directory.parent or directory))
    for child in directory.sorted_children():
        if "a" in flags or not child.name.startswith(HIDDEN_PREFIX):
            entries.append((child.name, child))
    return entries


def print_entries(shell, entries, flags):
    """Вывести список элементов в кратком или длинном формате."""
    if not entries:
        return
    if "l" in flags:
        for name, node in entries:
            shell.write(format_long(shell, node, name))
    else:
        shell.write("  ".join(name for name, _ in entries))


def list_directory(shell, path, node, flags):
    """Вывести содержимое каталога (рекурсивно при ``-R``)."""
    entries = directory_entries(node, flags)
    print_entries(shell, entries, flags)
    if "R" not in flags:
        return
    for name, child in entries:
        if child.is_dir and name not in (".", ".."):
            sub_path = path.rstrip("/") + "/" + name
            shell.write()
            shell.write(f"{sub_path}:")
            list_directory(shell, sub_path, child, flags)


def resolve_operands(shell, operands):
    """Разрешить операнды ``ls``; вернуть (файлы, каталоги, ошибки)."""
    files, dirs, failed = [], [], False
    for path in operands:
        try:
            node = shell.vfs.resolve(path)
        except VfsError as error:
            report(shell, "ls", f"cannot access {error}")
            failed = True
            continue
        (dirs if node.is_dir else files).append((path, node))
    return files, dirs, failed


def cmd_ls(shell, args):
    """``ls [-alR] [PATH...]`` — вывести содержимое каталогов VFS."""
    flags, operands = parse_options(args, LS_OPTIONS)
    files, dirs, failed = resolve_operands(shell, operands or ["."])
    print_entries(shell, files, flags)
    show_headers = len(operands) > SINGLE_OPERAND or "R" in flags
    for index, (path, node) in enumerate(dirs):
        if index or files:
            shell.write()
        if show_headers:
            shell.write(f"{path}:")
        list_directory(shell, path, node, flags)
    if failed:
        raise CommandError("")


def cmd_cd(shell, args):
    """``cd [PATH | -]`` — сменить текущий каталог VFS.

    Без аргумента выполняется переход в корень VFS (``~``),
    ``cd -`` возвращает в предыдущий каталог.
    """
    if len(args) > CD_MAX_ARGS:
        raise CommandError("too many arguments")
    path = args[0] if args else "~"
    try:
        if path == PREVIOUS_DIR:
            target = shell.vfs.previous
            shell.write(shell.vfs.path_of(target))
        else:
            target = shell.vfs.resolve_dir(path)
    except VfsError as error:
        raise CommandError(str(error)) from error
    shell.vfs.change_dir(target)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
}
```

### `src/emulator/commands/system.py`

```python
"""Системные команды: ``date`` и ``du``."""

import datetime
import math

from emulator.commands.options import parse_options, report
from emulator.errors import CommandError, VfsError

DATE_OPTIONS = "uI"
DEFAULT_DATE_FORMAT = "%a %b %d %H:%M:%S %Z %Y"
ISO_DATE_FORMAT = "%Y-%m-%d"
FORMAT_PREFIX = "+"
MAX_DATE_OPERANDS = 1

DU_OPTIONS = "ashc"
BLOCK_SIZE = 1024
HUMAN_UNITS = ("K", "M", "G", "T")
ONE_DECIMAL_LIMIT = 10


def current_time(utc):
    """Вернуть текущее время реальной ОС (местное или UTC)."""
    if utc:
        return datetime.datetime.now(datetime.timezone.utc)
    return datetime.datetime.now().astimezone()


def date_format(flags, operands):
    """Определить формат вывода ``date`` по опциям и операндам."""
    if len(operands) > MAX_DATE_OPERANDS:
        raise CommandError(f"extra operand '{operands[MAX_DATE_OPERANDS]}'")
    if operands:
        if not operands[0].startswith(FORMAT_PREFIX):
            raise CommandError(f"invalid date '{operands[0]}'")
        return operands[0][len(FORMAT_PREFIX):]
    if "I" in flags:
        return ISO_DATE_FORMAT
    return DEFAULT_DATE_FORMAT


def cmd_date(shell, args):
    """``date [-u] [-I] [+FORMAT]`` — вывести текущие дату и время."""
    flags, operands = parse_options(args, DATE_OPTIONS)
    fmt = date_format(flags, operands)
    shell.write(current_time("u" in flags).strftime(fmt))


def disk_usage(node):
    """Вернуть занимаемый узлом объём в байтах (рекурсивно)."""
    if not node.is_dir:
        return node.size
    return sum(disk_usage(child) for child in node.children.values())


def blocks(size):
    """Перевести байты в килобайтные блоки с округлением вверх."""
    return math.ceil(size / BLOCK_SIZE)


def human_size(size):
    """Отформатировать размер в стиле ``du -h`` (``0``, ``1.5K``, ``12M``)."""
    if size < BLOCK_SIZE:
        return str(size)
    value = float(size)
    for unit in HUMAN_UNITS:
        value /= BLOCK_SIZE
        if value < BLOCK_SIZE or unit == HUMAN_UNITS[-1]:
            break
    if value < ONE_DECIMAL_LIMIT:
        return f"{math.ceil(value * ONE_DECIMAL_LIMIT) / ONE_DECIMAL_LIMIT}" \
            f"{unit}"
    return f"{math.ceil(value)}{unit}"


def format_size(size, flags):
    """Отформатировать размер согласно опции ``-h``."""
    return human_size(size) if "h" in flags else str(blocks(size))


def du_lines(node, path, flags):
    """Вернуть строки ``(размер, путь)`` для узла в порядке обхода du."""
    lines = []
    if node.is_dir and "s" not in flags:
        for child in node.sorted_children():
            child_path = path.rstrip("/") + "/" + child.name
            if child.is_dir or "a" in flags:
                lines.extend(du_lines(child, child_path, flags))
    lines.append((disk_usage(node), path))
    return lines


def cmd_du(shell, args):
    """``du [-ashc] [PATH...]`` — оценить объём, занимаемый в VFS."""
    flags, operands = parse_options(args, DU_OPTIONS)
    if {"a", "s"} <= flags:
        raise CommandError("cannot both summarize and show all entries")
    total, failed = 0, False
    for path in operands or ["."]:
        try:
            node = shell.vfs.resolve(path)
        except VfsError as error:
            report(shell, "du", f"cannot access {error}")
            failed = True
            continue
        for size, line_path in du_lines(node, path, flags):
            shell.write(f"{format_size(size, flags)}\t{line_path}")
        total += disk_usage(node)
    if "c" in flags:
        shell.write(f"{format_size(total, flags)}\ttotal")
    if failed:
        raise CommandError("")


COMMANDS = {
    "date": cmd_date,
    "du": cmd_du,
}
```

### `src/emulator/commands/text.py`

```python
"""Команды обработки текста: ``uniq``."""

import itertools

from emulator.commands.options import parse_options
from emulator.errors import CommandError, VfsError

UNIQ_OPTIONS = "cdui"
MAX_UNIQ_OPERANDS = 2
SINGLE = 1
COUNT_WIDTH = 7


def read_text(shell, path):
    """Прочитать текстовый файл VFS."""
    try:
        node = shell.vfs.resolve(path)
    except VfsError as error:
        raise CommandError(str(error)) from error
    if node.is_dir:
        raise CommandError(f"{path}: Is a directory")
    return node.text()


def group_lines(lines, ignore_case):
    """Сгруппировать соседние одинаковые строки: [(строка, число)]."""
    key = str.lower if ignore_case else None
    return [(group[0], len(group)) for group in
            (list(items) for _, items in itertools.groupby(lines, key))]


def keep_group(count, flags):
    """Проверить, нужно ли выводить группу строк с учётом -d и -u."""
    if "d" in flags and count == SINGLE:
        return False
    return not ("u" in flags and count > SINGLE)


def format_group(line, count, flags):
    """Отформатировать группу строк (с числом повторов при ``-c``)."""
    if "c" in flags:
        return f"{count:>{COUNT_WIDTH}} {line}"
    return line


def cmd_uniq(shell, args):
    """``uniq [-cdui] INPUT [OUTPUT]`` — убрать соседние повторы строк.

    Если указан OUTPUT, результат записывается в файл VFS (в памяти).
    """
    flags, operands = parse_options(args, UNIQ_OPTIONS)
    if not operands:
        raise CommandError("missing operand: input file")
    if len(operands) > MAX_UNIQ_OPERANDS:
        raise CommandError(f"extra operand '{operands[MAX_UNIQ_OPERANDS]}'")
    lines = read_text(shell, operands[0]).splitlines()
    result = [format_group(line, count, flags)
              for line, count in group_lines(lines, "i" in flags)
              if keep_group(count, flags)]
    if len(operands) < MAX_UNIQ_OPERANDS:
        for line in result:
            shell.write(line)
        return
    data = "".join(line + "\n" for line in result).encode("utf-8")
    try:
        shell.vfs.write_file(operands[1], data)
    except VfsError as error:
        raise CommandError(str(error)) from error


COMMANDS = {
    "uniq": cmd_uniq,
}
```

### `src/emulator/commands/fileops.py`

```python
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
```

### `src/emulator/commands/help.py`

```python
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
```

### `src/emulator/commands/vfs_commands.py`

```python
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
```

### `scripts/make_vfs.py`

```python
"""Сгенерировать тестовые образы VFS в каталоге ``vfs/``.

Архивы не хранятся в репозитории: они создаются этим скриптом.
Запуск: ``python3 scripts/make_vfs.py [каталог]``.
"""

import os
import sys
import zipfile

STAMP = (2026, 9, 1, 12, 0, 0)
BINARY_DATA = bytes(range(256))
LOG_LINES = "boot ok\nboot ok\nnet up\nnet up\nnet up\ndisk full\nboot ok\n"

MINIMAL = {
    "hello.txt": "Hello, VFS!\n",
}

MULTI = {
    "notes.txt": "first note\nsecond note\n",
    "todo.txt": "buy milk\nbuy milk\nwrite report\n",
    "data.csv": "id,name\n1,alpha\n2,beta\n",
    "log.txt": LOG_LINES,
    "image.bin": BINARY_DATA,
}

DEEP = {
    "home/user/.profile": "export PATH=/bin\n",
    "home/user/docs/report.txt": "Report\n======\nAll good.\n",
    "home/user/docs/drafts/v1.txt": "draft one\n",
    "home/user/docs/drafts/old/v0.txt": "very old draft\n",
    "home/user/music/": None,
    "etc/config/app.conf": "debug=false\nport=8080\n",
    "var/log/syslog": LOG_LINES * 3,
    "bin/tool.bin": BINARY_DATA * 8,
    "tmp/": None,
}


def write_archive(path, entries):
    """Записать словарь ``имя -> содержимое`` в ZIP-архив."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            if isinstance(content, str):
                content = content.encode("utf-8")
            archive.writestr(info, content or b"")


def main(target):
    """Создать все тестовые образы VFS в каталоге ``target``."""
    os.makedirs(target, exist_ok=True)
    write_archive(os.path.join(target, "empty.zip"), {})
    write_archive(os.path.join(target, "minimal.zip"), MINIMAL)
    write_archive(os.path.join(target, "multi.zip"), MULTI)
    write_archive(os.path.join(target, "deep.zip"), DEEP)
    with open(os.path.join(target, "broken.zip"), "w",
              encoding="utf-8") as broken:
        broken.write("this is not a zip archive\n")
    print(f"VFS images created in {os.path.abspath(target)}")


if __name__ == "__main__":
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main((sys.argv[1:] or [os.path.join(ROOT, "vfs")])[0])
```

### `run.sh`

```sh
#!/bin/sh
# Запуск эмулятора. Все аргументы передаются эмулятору.
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$DIR/src${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m emulator "$@"
```

### `run.bat`

```bat
@echo off
rem Запуск эмулятора. Все аргументы передаются эмулятору.
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
python -m emulator %*
```
