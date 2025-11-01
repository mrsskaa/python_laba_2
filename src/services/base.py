from abc import ABC, abstractmethod
from os import PathLike
from typing import Literal

from src.enums import FileReadMode, FileDisplayMode

class OSConsoleServiceBase(ABC):
    @abstractmethod
    def ls(self, path: PathLike[str] | str, display_mode: FileDisplayMode = FileDisplayMode.simple) -> list[str]:
        ...

    @abstractmethod
    def format_long(self, entry: PathLike[str] | str) -> str:
        ...

    @abstractmethod
    def cat(self, filename: PathLike | str, mode: Literal[FileReadMode.string, FileReadMode.bytes] = FileReadMode.string)->str | bytes:
        ...

    @abstractmethod
    def cd(self, path: PathLike[str] | str)->str:
        ...

    @abstractmethod
    def cp(self, src: PathLike[str] | str, dst: PathLike[str] | str, recursive: bool = False) -> None:
        ...

    @abstractmethod
    def mv(self, src: PathLike[str] | str, dst: PathLike[str] | str) -> None:
        ...

    @abstractmethod
    def rm(self, target: PathLike[str] | str, recursive: bool = False) -> None:
        ...

    @abstractmethod
    def zip(self, path: PathLike[str] | str, path_arch: PathLike[str] | str) -> None:
        ...

    @abstractmethod
    def unzip(self, path_arch: PathLike[str] | str, res: PathLike[str] | str | None = None) -> None:
        ...

    @abstractmethod
    def tar_dir(self, path_file: PathLike[str] | str, path_arch: PathLike[str] | str) -> None:
        ...

    @abstractmethod
    def untar(self, path_archive_tar_gz: PathLike[str] | str, res: PathLike[str] | str | None = None) -> None:
        ...

    @abstractmethod
    def grep(self, pattern: str, path: PathLike[str] | str, r: bool, ignore_case: bool) -> list[str]:
        ...
