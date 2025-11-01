from src.config import LOGGING_CONFIG
import logging.config
import sys
from pathlib import Path
import typer
from typer import Typer, Context
from src.container import Container
from src.enums import FileReadMode, FileDisplayMode
from src.services.windows_console import WindowsConsoleService

app = Typer()

def get_container(ctx: Context)->Container:
    """
    Функция получает контейнера зависимостей из контекста Typer и проверяет, что контейнер правильно инициализирован.
    :param ctx: Контекст Typer
    :return: Контейнер зависимостей
    :raises RuntimeError: Если контейнер не инициализирован
    """
    container = ctx.obj

    if not isinstance(container, Container):
        raise RuntimeError("Контейнер не инициализирован")

    return container


@app.callback()
def main(ctx: Context)->None:
    """
    Основная функция, которая выполняется перед каждой командой, инициализирует систему логирования и создает контейнер зависимостей
    :param ctx: Контекст typer
    """
    logging.config.dictConfig(LOGGING_CONFIG)

    logger = logging.getLogger(__name__)

    ctx.obj = Container(console_service=WindowsConsoleService(logger=logger))


@app.command()
def ls(ctx: Context, path: Path = typer.Argument(..., readable=False, help="Directory path to list"), long: bool = typer.Option(False, "-l", "--long", help="Show longЯ file information")) -> None:
    """
    Функция вызывает команду для отображения содержимого директории ls и обрабатывает ошибки
    :param ctx: контекст typer
    :param path: путь к директории
    :param long: True/False (показывать подробную информацию/нет)
    :return: функция ничего не возвращает
    """
    try:
        call: Container = get_container(ctx)
        dm = FileDisplayMode.simple

        if long:
            dm = FileDisplayMode.long

        cnt = call.console_service.ls(path, dm)
        out = list(cnt)
        sys.stdout.writelines(out)
    except OSError as e:
        typer.echo(e)
    except Exception as e:
        raise e


@app.command()
def cat(ctx: Context, path: Path = typer.Argument(..., exists=False, readable=False, help="File to print"), mode: bool = typer.Option(False, "--bytes", "-b", help="Read as bytes")) -> None:
    """
    Функция вызывает команду для отображения содержимого файла cat и обрабатывает ошибки
    :param ctx: контекст Typer
    :param path: путь к файлу
    :param mode: True/False (читать файл в бинарном режиме (байты)/как текст)
    :return: функция ничего не возвращает
    """
    try:
        c: Container = get_container(ctx)
        read_mode = FileReadMode.string

        if mode:
            read_mode = FileReadMode.bytes

        d = c.console_service.cat(path, mode=read_mode)

        if isinstance(d, bytes):
            sys.stdout.buffer.write(d)

        else:
            typer.echo(str(d))
    except OSError as e:
        typer.echo(e)
    except Exception as e:
        raise e


@app.command()
def cd(ctx: Context, path: str = typer.Argument(..., help="Directory path to change to"))->None:
    """
    Функция вызывает команду для смены текущей рабочей директории cd и обрабатывает ошибки
    :param ctx: контекст Typer
    :param path: путь к директории
    :return: функция ничего не возвращает
    """
    try:
        call: Container = get_container(ctx)
        new_path = call.console_service.cd(path)
        sys.stdout.write(f"{new_path}\n")
    except OSError as e:
        typer.echo(e)
    except Exception as e:
        raise e


@app.command()
def cp(ctx: Context, path1: Path = typer.Argument(..., help="Источник (файл или каталог)"), path2: Path = typer.Argument(..., help="Назначение (файл или каталог)"), r: bool = typer.Option(False, "-r", "-г", help="Рекурсивное копирование каталогов")) -> None:
    """
    Функция вызывает команду копирования файлов/каталогов cp и обрабатывает ошибки
    :param ctx: контекст Typer
    :param path1: путь к источнику
    :param path2: путь к назначению
    :param r: True/False (рекурсивно копировать каталоги/нет)
    :return: функция ничего не возвращает
    """
    try:
        c: Container = get_container(ctx)
        c.console_service.cp(path1, path2, recursive=r)

    except OSError as e:
        typer.echo(e)
    except Exception as e:
        raise e

@app.command()
def mv(ctx: Context, path1: Path = typer.Argument(..., help="Источник (файл или каталог)"), path2: Path = typer.Argument(..., help="Назначение (файл, каталог или новое имя)")) -> None:
    """
    Функция запускает команду перемещения/переименования файла/каталога mv и обрабатывает ошибки
    :param ctx: контекст Typer
    :param path1: источник
    :param path2: назначение
    :return: функция ничего не возвращает
    """
    try:
        c = get_container(ctx)
        c.console_service.mv(path1, path2)
    except OSError as e:
        typer.echo(e)
    except Exception as e:
        raise e

@app.command()
def rm(ctx: Context, path: Path = typer.Argument(..., help="Путь к удаляемому файлу или каталогу"), r: bool = typer.Option(False, "-r", help="Рекурсивное удаление каталога")) -> None:
    """
    Функция запускает команду удаления файла/каталога rm и обрабатывает ошибки
    :param ctx: контекст Typer
    :param path: путь к удаляемому файлу или каталогу
    :param r: True/False (рекурсивное удаление каталога/нет)
    :return: функция ничего не возвращает
    """
    try:
        c: Container = get_container(ctx)

        if path.is_dir() and not r:
            typer.echo(f"Ошибка: {path} — это директория. Укажите -r для рекурсивного удаления.")
            return

        if path.is_dir() and r:
            answer = typer.prompt("Вы уверены, что хотите удалить каталог рекурсивно? (да/нет)")
            if answer.strip().lower() not in {"да"}:
                typer.echo("Операция отменена")
                return

        if not path.exists():
            typer.echo(f"Файл или каталог не найден: {path}")
            return

        c.console_service.rm(path, recursive=r)

    except OSError as e:
        typer.echo(e)
    except Exception:
        raise


@app.command()
def zip(ctx: Context, path: Path = typer.Argument(..., help="Каталог для упаковки"), path_arch: Path = typer.Argument(..., help="Файл архива ZIP")) -> None:
    """
    Функция вызывает команду zip, которая создаёт архив формата zip из указанного каталога, и обрабатывает ошибки
    :param ctx: контекст Typer
    :param path: путь к каталогу
    :param path_arch: путь к итоговому zip-файлу
    :return: функция ничего не возвращает
    """
    try:
        c: Container = get_container(ctx)
        c.console_service.zip(path, path_arch)
        typer.echo(f"zip: Cоздан архив {path_arch}")

    except OSError as e:
        typer.echo(e)
    except Exception as e:
        raise e

@app.command()
def unzip(ctx: Context, path_arch: Path = typer.Argument(..., help="ZIP архив для распаковки"), res: Path = typer.Argument(None, help="Папка назначения (по умолчанию текущая)", show_default=False)) -> None:
    """
    Функция вызывает команду unzip, которая распаковывает zip-архив в указанную директорию (или текущую, если не задано) и обрабатывает ошибки
    :param ctx: Контекст Typer для доступа к контейнеру зависимостей
    :param path_arch: путь к zip-файлу
    :param res: папка назначения (если None — используется текущая рабочая директория)
    :return: функция ничего не возвращает
    """
    try:
        c: Container = get_container(ctx)
        c.console_service.unzip(path_arch, res)

        if res:
            typer.echo(f"unzip: распаковано в {res}")
        else:
            typer.echo(f"unzip: распаковано в {Path('.').resolve()}")
    except OSError as e:
        typer.echo(e)
    except Exception as e:
        raise e

@app.command()
def tar(ctx: Context, path: Path = typer.Argument(..., help="Каталог для упаковки"), path_arch: Path = typer.Argument(..., help="Файл архива TAR.GZ")) -> None:
    """
    Функция вызывает команду tar, которая создаёт архив формата tar.gz из указанного каталога и обрабатывает ошибки
    :param ctx: Контекст Typer для доступа к контейнеру зависимостей
    :param path: Путь к каталогу для упаковки
    :param path_arch: Путь к результирующему TAR.GZ файлу
    :return: функция ничего не возвращает
    """
    try:
        c: Container = get_container(ctx)
        c.console_service.tar_dir(path, path_arch)
        typer.echo(f"tar: Cоздан архив {path_arch}")
    except OSError as e:
        typer.echo(e)
    except Exception as e:
        raise e

@app.command()
def untar(ctx: Context, path_arch: Path = typer.Argument(..., help="TAR.GZ архив для распаковки"), res: Path = typer.Argument(None, help="Папка назначения (по умолчанию текущая)", show_default=False)) -> None:
    """
    Функция вызывает команду untar, которая распаковывает tar.gz архив в указанную директорию (или текущую, если не задано)
    :param ctx: контекст Typer
    :param path_arch: путь к tar архиву
    :param res: папка назначения (если None — используется текущая рабочая директория)
    :return: функция ничего не возвращает
    """
    try:
        c: Container = get_container(ctx)
        c.console_service.untar(path_arch, res)

        if res:
            typer.echo(f"untar: распаковано в {res}")
        else:
            typer.echo(f"untar: распаковано в {Path('.').resolve()}")
    except OSError as e:
        typer.echo(e)
    except Exception as e:
        raise e


@app.command()
def grep(ctx: Context, pattern: str = typer.Argument(..., help="Шаблон для поиска (регулярное выражение)"), path: Path = typer.Argument('.', help="Каталог или файл для поиска"), r: bool = typer.Option(False, '-р', '--recursive', help="Рекурсивный поиск в подкаталогах"), ignore_case: bool = typer.Option(False, '-і', '--ignore-case', help="Поиск без учёта регистра")) -> None:
    """
    Функция вызывает команду grep и проверяет на ошибку
    :param ctx: контекст Typer для доступа к контейнеру зависимостей
    :param pattern: регулярное выражение для поиска
    :param path: файл или каталог, в котором вести поиск
    :param r: True/False (рекурсивно обходить подкаталоги, если указан каталог/нет
    :param ignore_case: True/False (искать без учёта регистра/нет)
    :return: функция ничего не возвращает
    """
    try:
        c: Container = get_container(ctx)
        res = c.console_service.grep(pattern, path, r=r, ignore_case=ignore_case)
        for i in res:
            typer.echo(i)
    except Exception as e:
        typer.echo(e)


if __name__ == "__main__":
    app()
