from logging import Logger
from os import PathLike
from pathlib import Path
import shutil
import stat as stat_module
from datetime import datetime
import zipfile
import tarfile
import re
from src.enums import FileReadMode, FileDisplayMode
from src.services.base import OSConsoleServiceBase
import os

class WindowsConsoleService(OSConsoleServiceBase):
    def __init__(self, logger: Logger) -> None:
        """
        Функция инициализирует сервис консоли
        :param logger: логгер для записи информации о работе сервиса
        :return: функция ничего не возвращает
        """
        self._logger = logger


    def format_long(self, entry: PathLike[str] | str) -> str:
        """
        Функция форматирует подробную информацию о файле или директории и обрабатывает возможные ошибки
        :param entry: объект Path, представляющий файл или директорию
        :return: отформатированная строка с подробной информацией
        """
        entry_path = Path(entry)
        try:
            stat_info = entry_path.stat()

            mode = oct(stat_module.S_IMODE(stat_info.st_mode))[2:]
            permissions = mode

            size = stat_info.st_size

            mtime = datetime.fromtimestamp(stat_info.st_mtime)
            mtime_pretty = mtime.strftime("%Y-%m-%d %H:%M:%S")

            if entry_path.is_dir():
                entry_type = "d"
            else:
                entry_type = "-"

            form_l = f"{entry_type}{permissions} {size:>10} {mtime_pretty} {entry_path.name}\n"

            return form_l

        except OSError as e:
            self._logger.warning(f"Невозможно получить подробную информацию о {entry_path}: {e}")
            return f"- --------- {0:>10} 1970-01-01 00:00:00 {entry_path.name}\n"


    def ls(self, path: PathLike[str] | str, mode: FileDisplayMode = FileDisplayMode.simple) -> list[str]:
        """
        Функция отображает содержимое директории и обрабатывает возможные ошибки
        :param path: путь к директории для отображения
        :param mode: режим отображения (простой или подробный)
        :return: список строк с информацией о файлах и директориях
        """
        if hasattr(path, 'value'):
            path = path.value
        path = Path(path)

        if not path.exists():
            self._logger.error(f"ls: Директория не найдена: {path}")
            raise FileNotFoundError(path)

        if not path.is_dir():
            self._logger.error(f"ls: Введенное {path} не является директорией")
            raise NotADirectoryError(path)

        self._logger.info(f"ls: Отображение {path} в режиме {mode}")

        a = list(path.iterdir())

        result: list[str] = []
        if mode == FileDisplayMode.simple:
            for i in a:
                result.append(i.name + "\n")
        else:
            for i in a:
                formatted = self.format_long(i)
                if formatted:
                    result.append(formatted)
        return result


    def cat(self, path_file: PathLike[str] | str, mode: FileReadMode = FileReadMode.string)->str | bytes:
        """
        Функция отображает содержимое файла и обрабатывает возможные ошибки
        :param path_file: путь к файлу
        :param mode: режим чтения файла (FileReadMode.string или FileReadMode.bytes)
        :return: содержимое файла в виде строки или байтов
        """
        path = Path(path_file)
        self._logger.info(f"cat: Запуск чтения файла '{path_file}' в режиме {mode}")

        if not path.exists():
            err = f"cat: Файл не найден: '{path_file}' (path does not exist)"
            self._logger.error(err)
            raise FileNotFoundError(err)

        if path.is_dir():
            err = f"cat: Путь - это директория, а не файл: '{path_file}'"
            self._logger.error(err)
            raise IsADirectoryError(err)

        try:
            if mode == FileReadMode.string:
                self._logger.debug(f"cat: Чтение файла '{path_file}' в виде текста")
                file_content = path.read_text(encoding="utf-8")
                self._logger.info(f"cat: Успешное чтение '{path_file}' в виде текста, ({len(file_content)} символов)")
                return file_content

            if mode == FileReadMode.bytes:
                self._logger.debug(f"cat: Чтение файла '{path_file}' в виде байтов")
                content_bytes = path.read_bytes()
                self._logger.info(f"cat: Успешное чтение файла '{path_file}' в виде байтов, ({len(content_bytes)} байт)")
                return content_bytes

        except OSError as e:
            self._logger.exception(f"cat: Ошибка чтения файла '{path_file}': {e}")
            raise


    def cd(self, path: PathLike[str] | str) -> str:
        """
        Функция меняет рабочую директорию и обрабатывает возможные ошибки
        :param path: путь к директории
        :return: абсолютный путь к новой рабочей директории
        """
        current_dir = Path(os.getcwd())
        self._logger.info(f"cd: Попытка изменить каталог на '{path}'")
        path_str = str(path)

        if path_str == "~" or path_str.startswith("~/"):
            path_str = os.path.expanduser(path_str)
            self._logger.debug(f"cd: Путь преобразован до '{path_str}'")

        path = Path(path_str)

        if not path.is_absolute():
            path = current_dir/path
            self._logger.debug(f"cd: Относительный путь преобразован в абсолютный:   '{path}'")

        path = path.resolve()
        self._logger.debug(f"cd: Расширенный путь  '{path}'")

        if not path.exists():
            err = f"cd: Директория не найдена: '{path_str}' (resolved to '{path}')"
            self._logger.error(err)
            raise FileNotFoundError(err)

        if not path.is_dir():
            err = f"cd: Путь не является директорией: '{path_str}' (resolved to '{path}')"
            self._logger.error(err)
            raise NotADirectoryError(err)

        os.chdir(path)
        self._logger.info(f"cd: Успешная смена директории на '{path}' (из '{current_dir}')")
        return str(path)


    def cp(self, path1: PathLike[str] | str, path2: PathLike[str] | str, recursive: bool = False) -> None:
        """
        Функция копирует файл или каталог и обрабатывает возможные ошибки
        :param path1: путь к исходному файлу или каталогу
        :param path2: путь к месту назначения
        :param recursive: True/False (рекурсивно копировать каталоги/нет)
        :return: функция ничего не возвращает
        """
        src_path = Path(path1)
        dst_path = Path(path2)

        self._logger.info(f"cp: src='{src_path}', dst='{dst_path}', recursive={recursive}")

        if not src_path.exists():
            err = f"cp: Источник не найден: '{src_path}'"
            self._logger.error(err)
            raise FileNotFoundError(err)

        try:
            if src_path.is_dir():
                if not recursive:
                    err = f"cp: '{src_path}' это директория; используйте -r для рекурсивного копирования"
                    self._logger.error(err)
                    raise IsADirectoryError(err)

                if dst_path.exists() and dst_path.is_dir():
                    final_dst = dst_path / src_path.name

                else:
                    final_dst = dst_path

                self._logger.debug(f"cp: Копируем из '{src_path}' в '{final_dst}'")
                if final_dst.exists():
                    if final_dst.is_dir():
                        for i in src_path.iterdir():
                            target = final_dst /i.name
                            if i.is_dir():
                                shutil.copytree(i, target)
                            else:
                                shutil.copy2(i, target)
                    else:
                        raise FileExistsError(f"cp: Пункт назначения существует и не является каталогом: '{final_dst}'")
                else:
                    shutil.copytree(src_path, final_dst)
            else:

                if dst_path.exists() and dst_path.is_dir():
                    final_dst = dst_path / src_path.name
                else:
                    final_dst = dst_path

                self._logger.debug(f"cp: copy2 из '{src_path}' в '{final_dst}'")
                final_dst_parent = final_dst.parent

                if not final_dst_parent.exists():
                    final_dst_parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(src_path, final_dst)

            self._logger.info(f"cp: Успешная копия '{dst_path}'")

        except PermissionError as e:
            self._logger.exception(f"cp: Отказано в разрешении на копирование '{src_path}' -> '{dst_path}': {e}")
            raise
        except OSError as e:
            self._logger.exception(f"cp: Ошибка операционной системы при копировании '{src_path}' -> '{dst_path}': {e}")
            raise

    def mv(self, path1: PathLike[str] | str, path2: PathLike[str] | str) -> None:
        """
        Функция перемещает/переименовывает файл или каталог и обрабатывает возможные ошибки
        :param path1: источник (файл или каталог)
        :param path2: назначение (файл, каталог или новое имя)
        :return: функция ничего не возвращает
        """
        src_path = Path(path1)
        dst_path = Path(path2)

        self._logger.info(f"mv: src='{src_path}', dst='{dst_path}'")

        if not src_path.exists():
            err = f"mv: Источник не найден: '{src_path}'"
            self._logger.error(err)
            raise FileNotFoundError(err)

        try:
            final_dst: Path
            if dst_path.exists() and dst_path.is_dir():
                final_dst = dst_path / src_path.name
            else:
                final_dst = dst_path

            self._logger.debug(f"mv: Перемещение из '{src_path}' в '{final_dst}'")

            final_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(final_dst))
            self._logger.info(f"mv: Успешное перемещение в '{final_dst}'")

        except PermissionError as e:
            self._logger.exception(f"mv: Запрещено перемещение '{src_path}' -> '{dst_path}': {e}")
            raise

        except OSError as e:
            self._logger.exception(f"mv: Ошибка операционной системы во время перемещения '{src_path}' -> '{dst_path}': {e}")
            raise

    def rm(self, target: PathLike[str] | str, recursive: bool = False) -> None:
        """
        Функция удаляет файл или каталог и обрабатывает возможные ошибки
        :param target: путь к удаляемому файлу или каталогу
        :param recursive: True/False (рекурсивное удаление каталога/нет)
        :return: функция ничего не возвращает
        """
        path = Path(target)
        self._logger.info(f"rm: target='{path}', recursive={recursive}")

        path_str = str(target).strip()
        if path_str in {"..", "/"}:
            err = "rm: Удаление '..' или '/' запрещено"
            self._logger.error(err)
            raise PermissionError(err)

        res = path.resolve()

        if res == Path(res.anchor):
            err = f"rm: Удаление корня запрещено: '{res}'"
            self._logger.error(err)
            raise PermissionError(err)

        if not res.exists():
            err = f"rm: Путь не найден: '{path}'"
            self._logger.error(err)
            raise FileNotFoundError(err)

        try:
            if res.is_dir():
                if not recursive:
                    err = f"rm: '{path}' является директорией, используйте -r для рекурсивного удаления"
                    self._logger.error(err)
                    raise IsADirectoryError(err)
                self._logger.debug(f"rm: rmtree '{res}'")
                shutil.rmtree(res)

            else:
                self._logger.debug(f"rm: unlink '{res}'")
                res.unlink()

            self._logger.info(f"rm: Удалено '{res}'")
        except PermissionError as e:
            self._logger.exception(f"rm: Удаление запрещено '{res}': {e}")
            raise
        except OSError as e:
            self._logger.exception(f"rm: Ошибка операционной системы во время удаления '{res}': {e}")
            raise


    def zip(self, path: PathLike[str] | str, path_arch: PathLike[str] | str) -> None:
        """
        Функция создаёт zip-архив из указанного каталога средствами стандартной библиотеки и обрабатывает возможные ошибки
        :param path: путь к каталогу (источнику) для упаковки
        :param path_arch: путь к итоговому zip-файлу
        :return: функция ничего не возвращает
        """
        src_dir = Path(path)
        dst_zip = Path(path_arch)
        self._logger.info(f"zip: Изначальная папка: '{src_dir.resolve()}', архивированная: '{dst_zip.resolve()}'")
        try:
            if not src_dir.exists():
                err = f"zip: Источник не найден: '{src_dir}'"
                self._logger.error(err)
                raise FileNotFoundError(err)

            if not src_dir.is_dir():
                err = f"zip: Источник не каталог: '{src_dir}'"
                self._logger.error(err)
                raise NotADirectoryError(err)

            dst_zip.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(dst_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for path in src_dir.rglob("*"):
                    arcname = path.relative_to(src_dir)
                    if path.is_dir():
                        continue
                    self._logger.debug(f"zip: Добавляем '{path}' как '{arcname}'")
                    zf.write(path, arcname)
            self._logger.info(f"zip: Готово -> '{dst_zip.resolve()}'")
        except Exception:
            self._logger.exception("zip: Ошибка при создании архива")
            raise


    def unzip(self, path_arch: PathLike[str] | str, res: PathLike[str] | str | None = None) -> None:
        """
        Функция распаковывает zip-архив в указанную директорию и обрабатывает возможные ошибки
        :param path_arch: путь к zip-архиву
        :param res: папка назначения; если None — используется текущая рабочая директория
        :return: функция ничего не возвращает
        """
        src_zip = Path(path_arch)

        if res is not None:
            dst_dir = Path(res)
        else:
            dst_dir = Path.cwd()

        self._logger.info(f"unzip: Изначальный архив: '{src_zip.resolve()}', папка назначения: '{dst_dir.resolve()}'")

        try:
            if not src_zip.exists():
                err = f"unzip: Архив не найден: '{src_zip}'"
                self._logger.error(err)
                raise FileNotFoundError(err)

            dst_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(src_zip, mode="r") as zf:
                zf.extractall(dst_dir)
            self._logger.info(f"unzip: Готово -> '{dst_dir.resolve()}'")
        except Exception:
            self._logger.exception("unzip: Ошибка при распаковке архива")
            raise


    def tar_dir(self, path_file: PathLike[str] | str, path_arch: PathLike[str] | str) -> None:
        """
        Функция создаёт tar.gz архив из указанного каталога с помощью tarfile и обрабатывает возможные ошибки
        :param path_file: путь к каталогу‑источнику для упаковки
        :param path_arch: путь к результирующему tar.gz архиву (может быть относительным или абсолютным)
        :return: функция ничего не возвращает
        """

        src_dir = Path(path_file)
        dst_tar = Path(path_arch)
        self._logger.info(f"tar: Начальная папка: '{src_dir.resolve()}', архив: '{dst_tar.resolve()}'")

        try:
            if not src_dir.exists():
                err = f"tar: Источник не найден: '{src_dir}'"
                self._logger.error(err)
                raise FileNotFoundError(err)
            if not src_dir.is_dir():
                err = f"tar: Источник не каталог: '{src_dir}'"
                self._logger.error(err)
                raise NotADirectoryError(err)

            dst_tar.parent.mkdir(parents=True, exist_ok=True)
            with tarfile.open(dst_tar, mode="w:gz") as tf:
                tf.add(src_dir, arcname=src_dir.name)
                self._logger.info(f"tar: Готово -> '{dst_tar.resolve()}'")
        except Exception:
            self._logger.exception("tar: Ошибка при создании архива")
            raise


    def untar(self, path_archive_tar_gz: PathLike[str] | str, res: PathLike[str] | str | None = None) -> None:
        """
        Функция распаковывает tar.gz архив в указанную директорию и обрабатывает ошибки
        :param path_archive_tar_gz: путь к tar.gz архиву
        :param res: папка назначения; если None — используется текущая рабочая директория
        :return: функция ничего не возвращает
        """
        src_tar = Path(path_archive_tar_gz)
        if res is not None:
            dst_dir = Path(res)
        else:
            dst_dir = Path.cwd()
        self._logger.info(f"untar: Изначальный архив: '{src_tar.resolve()}', dest='{dst_dir.resolve()}'")
        try:
            if not src_tar.exists():
                err = f"untar: Архив не найден: '{src_tar}'"
                self._logger.error(err)
                raise FileNotFoundError(err)
            dst_dir.mkdir(parents=True, exist_ok=True)
            with tarfile.open(src_tar, mode="r:gz") as tf:
                tf.extractall(dst_dir)
            self._logger.info(f"untar: Готово -> '{dst_dir.resolve()}'")
        except Exception:
            self._logger.exception("untar: Ошибка при распаковке архива")
            raise


    def grep(self, pattern: str, path: PathLike[str] | str, r: bool, ignore_case: bool) -> list[str]:
        """
        Функция совершает поиск строк по регулярному выражению в файлах и обрабатывает возможные ошибки
        :param pattern: регулярное выражение для поиска
        :param path: файл или каталог, в котором будет производиться поиск
        :param r: True/False (рекурсивный обход подкаталогов, если указан каталог/нет)
        :param ignore_case: True/False (поиск без учёта регистра/нет)
        :return: список строк с найденными совпадениями
        """
        logger = self._logger
        flags: re.RegexFlag
        if ignore_case:
            flags = re.IGNORECASE
        else:
            flags = re.RegexFlag(0)
        try:
            rgx = re.compile(pattern, flags)
        except re.error as e:
            logger.error(f"grep: Ошибка компиляции regex: {e}")
            raise

        base = Path(path)
        files: list[Path] = []
        if base.is_file():
            files = [base]
        else:
            if r:
                for p in base.rglob('*'):
                    if p.is_file():
                        files.append(p)
            else:
                for p in base.glob('*'):
                    if p.is_file():
                        files.append(p)

        results: list[str] = []
        for file_path in files:
            try:
                with file_path.open(encoding='utf-8', errors='ignore') as fh:
                    for ln, line in enumerate(fh, 1):
                        if rgx.search(line):
                            results.append(f"{file_path}:{ln}:{line.strip()}")
            except Exception as e:
                logger.error(f"grep: Ошибка чтения файла {file_path}: {e}")
        logger.info(f"grep: pattern={pattern}, path={base}, recursive={r}, ignore_case={ignore_case}, results={len(results)}")
        return results
