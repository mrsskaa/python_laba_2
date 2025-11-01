from enum import Enum


class FileReadMode(str, Enum):
    string = ("string",)
    bytes = ("bytes",)


class FileDisplayMode(str, Enum):
    simple = "simple"
    long = "long"
