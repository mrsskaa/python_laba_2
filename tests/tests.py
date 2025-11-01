from pathlib import Path
from unittest.mock import Mock
import os
import zipfile
import tarfile
import re

import pytest

from pytest_mock import MockerFixture

from src.services.base import OSConsoleServiceBase
from src.enums import FileReadMode, FileDisplayMode

#тестим ls
def test_ls_nonexisted_folder(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    fake_path_object: Mock = mocker.create_autospec(Path, instance=True, spec_set=True)
    fake_path_object.exists.return_value = False
    nonexistent_path: str = "/nonexistent"
    fake_pathlib_path_class.return_value = fake_path_object

    with pytest.raises(FileNotFoundError):
        service.ls(nonexistent_path)

    fake_pathlib_path_class.assert_called_with(nonexistent_path)
    fake_path_object.exists.assert_called_once()

def test_ls_file(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_object: Mock = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_object.exists.return_value = True
    path_object.is_dir.return_value = False
    not_a_directory_file: str = "file.txt"
    fake_pathlib_path_class.return_value = path_object

    with pytest.raises(NotADirectoryError):
        service.ls(not_a_directory_file)

    fake_pathlib_path_class.assert_called_with(not_a_directory_file)
    path_object.exists.assert_called_once()

def test_ls_existing_directory(service: OSConsoleServiceBase,fake_pathlib_path_class: Mock,mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = True
    path_obj.is_dir.return_value = True
    entry = mocker.Mock()
    entry.name = "file.txt"
    path_obj.iterdir.return_value = [entry]
    fake_pathlib_path_class.return_value = path_obj
    result = service.ls("/fake/dir")

    fake_pathlib_path_class.assert_called_once_with("/fake/dir")
    path_obj.exists.assert_called_once_with()
    path_obj.is_dir.assert_called_once_with()
    path_obj.iterdir.assert_called_once_with()
    assert result == ["file.txt\n"]


def test_ls_long_mode(service: OSConsoleServiceBase,fake_pathlib_path_class: Mock,mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = True
    path_obj.is_dir.return_value = True
    entry = mocker.create_autospec(Path, instance=True, spec_set=True)
    entry.name = "file.txt"
    entry.is_dir.return_value = False
    entry.stat.return_value = mocker.Mock(st_mode=0o100644, st_size=1024, st_mtime=1000000.0)
    path_obj.iterdir.return_value = [entry]
    fake_pathlib_path_class.return_value = path_obj
    result = service.ls("/fake/dir", FileDisplayMode.long)

    assert len(result) == 1
    assert "file.txt" in result[0]
    entry.stat.assert_called_once()


def test_ls_path_with_value_attribute(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_with_value = mocker.Mock()
    path_with_value.value = "/fake/dir"
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = True
    path_obj.is_dir.return_value = True
    entry = mocker.Mock()
    entry.name = "file.txt"
    path_obj.iterdir.return_value = [entry]
    fake_pathlib_path_class.return_value = path_obj
    result = service.ls(path_with_value)

    assert result == ["file.txt\n"]


#тестим cat
def test_cat_file_not_found(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = False
    fake_pathlib_path_class.return_value = path_obj
    with pytest.raises(FileNotFoundError):
        service.cat("nonexistent.txt")

    path_obj.exists.assert_called_once()


def test_cat_directory_error(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = True
    path_obj.is_dir.return_value = True
    fake_pathlib_path_class.return_value = path_obj
    with pytest.raises(IsADirectoryError):
        service.cat("some_dir")

    path_obj.exists.assert_called_once()
    path_obj.is_dir.assert_called_once()


def test_cat_string_mode(service: OSConsoleServiceBase, mocker: MockerFixture, tmp_path: Path,):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!", encoding="utf-8")
    result = service.cat(str(test_file), FileReadMode.string)

    assert result == "Hello, World!"
    assert isinstance(result, str)


def test_cat_bytes_mode(service: OSConsoleServiceBase, tmp_path: Path):
    test_file = tmp_path / "test.bin"
    test_content = b"\x00\x01\x02\x03"
    test_file.write_bytes(test_content)
    result = service.cat(str(test_file), FileReadMode.bytes)

    assert result == test_content
    assert isinstance(result, bytes)


#тестим cd
def test_cd_nonexistent_directory(service: OSConsoleServiceBase,fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = False
    path_obj.is_absolute.return_value = True
    path_obj.resolve.return_value = path_obj
    fake_pathlib_path_class.return_value = path_obj
    with pytest.raises(FileNotFoundError):
        service.cd("/nonexistent")

    path_obj.exists.assert_called_once()


def test_cd_file_not_directory(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture,):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = True
    path_obj.is_dir.return_value = False
    path_obj.is_absolute.return_value = True
    path_obj.resolve.return_value = path_obj
    fake_pathlib_path_class.return_value = path_obj

    with pytest.raises(NotADirectoryError):
        service.cd("/some_file.txt")


def test_cd_success(service: OSConsoleServiceBase,tmp_path: Path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    current_dir = Path.cwd()
    try:
        result = service.cd(str(test_dir))
        assert Path(result) == test_dir.resolve()
        assert Path.cwd() == test_dir.resolve()
    finally:
        os.chdir(current_dir)


def test_cd_relative_path(service: OSConsoleServiceBase, tmp_path: Path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir()
    current_dir = Path.cwd()
    try:
        os.chdir(test_dir)
        result = service.cd("subdir")
        assert Path(result) == sub_dir.resolve()
        assert Path.cwd() == sub_dir.resolve()
    finally:
        os.chdir(current_dir)


def test_cd_home_directory(service: OSConsoleServiceBase, mocker: MockerFixture):
    mock_expanduser = mocker.patch("src.services.windows_console.os.path.expanduser")
    mock_getcwd = mocker.patch("src.services.windows_console.os.getcwd")
    home_dir = Path.home()
    mock_expanduser.return_value = str(home_dir)
    mock_getcwd.return_value = str(Path.cwd())
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = True
    path_obj.is_dir.return_value = True
    path_obj.is_absolute.return_value = True
    path_obj.resolve.return_value = home_dir
    mocker.patch("src.services.windows_console.Path", return_value=path_obj)

    result = service.cd("~")
    assert result == str(home_dir)
    mock_expanduser.assert_called_once_with("~")


#тестим cp
def test_cp_file_not_found( service: OSConsoleServiceBase, fake_pathlib_path_class: Mock,mocker: MockerFixture):
    src_path = mocker.create_autospec(Path, instance=True, spec_set=True)
    src_path.exists.return_value = False
    fake_pathlib_path_class.side_effect = [src_path, mocker.Mock()]

    with pytest.raises(FileNotFoundError):
        service.cp("nonexistent.txt", "dest.txt")

    src_path.exists.assert_called_once()


def test_cp_directory_without_recursive(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture,):
    src_path = mocker.create_autospec(Path, instance=True, spec_set=True)
    src_path.exists.return_value = True
    src_path.is_dir.return_value = True
    fake_pathlib_path_class.side_effect = [src_path, mocker.Mock()]

    with pytest.raises(IsADirectoryError):
        service.cp("source_dir", "dest_dir", recursive=False)


def test_cp_file_success(service: OSConsoleServiceBase, tmp_path: Path):
    src_file = tmp_path / "source.txt"
    src_file.write_text("test content")
    dst_file = tmp_path / "dest.txt"
    service.cp(str(src_file), str(dst_file))

    assert dst_file.exists()
    assert dst_file.read_text() == "test content"


def test_cp_directory_recursive(service: OSConsoleServiceBase, tmp_path: Path):
    src_dir = tmp_path / "source_dir"
    src_dir.mkdir()
    (src_dir / "file1.txt").write_text("file1")
    subdir = src_dir / "subdir"
    subdir.mkdir()
    (subdir / "file2.txt").write_text("file2")
    dst_dir = tmp_path / "dest_dir"
    service.cp(str(src_dir), str(dst_dir), recursive=True)

    assert dst_dir.exists()
    assert (dst_dir / "file1.txt").read_text() == "file1"
    assert (dst_dir / "subdir" / "file2.txt").read_text() == "file2"


def test_cp_to_existing_directory(service: OSConsoleServiceBase, tmp_path: Path):
    src_file = tmp_path / "source.txt"
    src_file.write_text("content")
    dst_dir = tmp_path / "dest_dir"
    dst_dir.mkdir()
    service.cp(str(src_file), str(dst_dir))

    assert (dst_dir / "source.txt").exists()
    assert (dst_dir / "source.txt").read_text() == "content"


def test_cp_directory_to_existing_directory(service: OSConsoleServiceBase, tmp_path: Path):
    src_dir = tmp_path / "source_dir"
    src_dir.mkdir()
    (src_dir / "file1.txt").write_text("file1")
    dst_dir = tmp_path / "dest_dir"
    dst_dir.mkdir()
    service.cp(str(src_dir), str(dst_dir), recursive=True)

    assert (dst_dir / "source_dir").exists()
    assert (dst_dir / "source_dir" / "file1.txt").read_text() == "file1"


def test_cp_directory_to_existing_nested(service: OSConsoleServiceBase, tmp_path: Path):
    src_dir = tmp_path / "source_dir"
    src_dir.mkdir()
    (src_dir / "file1.txt").write_text("file1")
    subdir = src_dir / "subdir"
    subdir.mkdir()
    (subdir / "file2.txt").write_text("file2")

    dst_dir = tmp_path / "dest_dir"
    dst_dir.mkdir()
    existing_subdir = dst_dir / "source_dir"
    existing_subdir.mkdir()
    service.cp(str(src_dir), str(dst_dir), recursive=True)

    assert (dst_dir / "source_dir" / "file1.txt").read_text() == "file1"
    assert (dst_dir / "source_dir" / "subdir" / "file2.txt").read_text() == "file2"


def test_cp_file_new_directory_parent(service: OSConsoleServiceBase,tmp_path: Path):
    src_file = tmp_path / "source.txt"
    src_file.write_text("content")
    dst_file = tmp_path / "new_dir" / "subdir" / "dest.txt"
    service.cp(str(src_file), str(dst_file))

    assert dst_file.exists()
    assert dst_file.read_text() == "content"


#тестим mv
def test_mv_file_not_found(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    src_path = mocker.create_autospec(Path, instance=True, spec_set=True)
    src_path.exists.return_value = False
    fake_pathlib_path_class.side_effect = [src_path, mocker.Mock()]

    with pytest.raises(FileNotFoundError):
        service.mv("nonexistent.txt", "dest.txt")


def test_mv_file_success(service: OSConsoleServiceBase, tmp_path: Path):
    src_file = tmp_path / "source.txt"
    src_file.write_text("content")
    dst_file = tmp_path / "dest.txt"
    service.mv(str(src_file), str(dst_file))

    assert not src_file.exists()
    assert dst_file.exists()
    assert dst_file.read_text() == "content"


def test_mv_to_existing_directory(service: OSConsoleServiceBase, tmp_path: Path):
    src_file = tmp_path / "source.txt"
    src_file.write_text("content")
    dst_dir = tmp_path / "dest_dir"
    dst_dir.mkdir()
    service.mv(str(src_file), str(dst_dir))

    assert not src_file.exists()
    assert (dst_dir / "source.txt").exists()
    assert (dst_dir / "source.txt").read_text() == "content"


def test_mv_directory(service: OSConsoleServiceBase, tmp_path: Path):
    src_dir = tmp_path / "source_dir"
    src_dir.mkdir()
    (src_dir / "file.txt").write_text("content")
    dst_dir = tmp_path / "dest_dir"
    service.mv(str(src_dir), str(dst_dir))

    assert not src_dir.exists()
    assert dst_dir.exists()
    assert (dst_dir / "file.txt").read_text() == "content"


#тестим rm
def test_rm_file_not_found(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.strip.return_value = "nonexistent.txt"
    path_obj.exists.return_value = False
    path_obj.resolve.return_value = path_obj
    mock_path = mocker.patch("src.services.windows_console.Path")
    mock_path.return_value = path_obj

    with pytest.raises(FileNotFoundError):
        service.rm("nonexistent.txt")


def test_rm_directory_without_recursive(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.strip.return_value = "some_dir"
    path_obj.exists.return_value = True
    path_obj.is_dir.return_value = True
    path_obj.resolve.return_value = path_obj
    path_obj.anchor = "C:\\"
    mock_path = mocker.patch("src.services.windows_console.Path")
    mock_path.return_value = path_obj

    with pytest.raises(IsADirectoryError):
        service.rm("some_dir", recursive=False)


def test_rm_protected_paths(service: OSConsoleServiceBase, mocker: MockerFixture):
    with pytest.raises(PermissionError):
        service.rm("..", recursive=True)
    with pytest.raises(PermissionError):
        service.rm("/", recursive=True)


def test_rm_file_success(service: OSConsoleServiceBase,tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    service.rm(str(test_file), recursive=False)

    assert not test_file.exists()


def test_rm_directory_recursive(service: OSConsoleServiceBase, tmp_path: Path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("content")
    subdir = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "file2.txt").write_text("content2")
    service.rm(str(test_dir), recursive=True)

    assert not test_dir.exists()


def test_rm_root_protection(service: OSConsoleServiceBase, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.strip.return_value = "C:\\"
    path_obj.exists.return_value = True
    path_obj.resolve.return_value = Path("C:\\")
    path_obj.anchor = "C:\\"
    mock_path = mocker.patch("src.services.windows_console.Path")
    mock_path.return_value = path_obj
    path_obj.__eq__ = lambda self, other: str(self) == str(other)

    with pytest.raises(PermissionError):
        service.rm("C:\\", recursive=True)


#тестим zip
def test_zip_directory_not_found(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = False
    fake_pathlib_path_class.side_effect = [path_obj, mocker.Mock()]

    with pytest.raises(FileNotFoundError):
        service.zip("nonexistent_dir", "archive.zip")


def test_zip_not_directory(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = True
    path_obj.is_dir.return_value = False
    fake_pathlib_path_class.side_effect = [path_obj, mocker.Mock()]
    with pytest.raises(NotADirectoryError):
        service.zip("file.txt", "archive.zip")


def test_zip_success(service: OSConsoleServiceBase, tmp_path: Path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "file2.txt").write_text("content2")
    subdir = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("content3")
    archive = tmp_path / "archive.zip"
    service.zip(str(test_dir), str(archive))
    assert archive.exists()
    with zipfile.ZipFile(archive) as zf:
        assert "file1.txt" in zf.namelist()
        assert "file2.txt" in zf.namelist()
        assert "subdir/file3.txt" in zf.namelist()


#тестим unzip
def test_unzip_file_not_found(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = False
    fake_pathlib_path_class.return_value = path_obj

    with pytest.raises(FileNotFoundError):
        service.unzip("nonexistent.zip", None)


def test_unzip_success(service: OSConsoleServiceBase, tmp_path: Path):
    # Создаем архив
    test_dir = tmp_path / "source_dir"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("content")
    archive = tmp_path / "archive.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.write(test_dir / "file.txt", "file.txt")
    extract_dir = tmp_path / "extract_dir"
    service.unzip(str(archive), str(extract_dir))

    assert (extract_dir / "file.txt").exists()
    assert (extract_dir / "file.txt").read_text() == "content"


def test_unzip_to_none(service: OSConsoleServiceBase, tmp_path: Path):
    current_dir = Path.cwd()
    try:
        os.chdir(tmp_path)
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        archive = tmp_path / "archive.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(test_file, "file.txt")

        service.unzip(str(archive), None)
        assert (tmp_path / "file.txt").exists()
    finally:
        os.chdir(current_dir)


#тестим tar
def test_tar_dir_directory_not_found(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = False

    fake_pathlib_path_class.side_effect = [path_obj, mocker.Mock()]

    with pytest.raises(FileNotFoundError):
        service.tar_dir("nonexistent_dir", "archive.tar.gz")


def test_tar_dir_not_directory(service: OSConsoleServiceBase,fake_pathlib_path_class: Mock,mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = True
    path_obj.is_dir.return_value = False

    fake_pathlib_path_class.side_effect = [path_obj, mocker.Mock()]

    with pytest.raises(NotADirectoryError):
        service.tar_dir("file.txt", "archive.tar.gz")


def test_tar_dir_success(service: OSConsoleServiceBase, tmp_path: Path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "file2.txt").write_text("content2")

    archive = tmp_path / "archive.tar.gz"

    service.tar_dir(str(test_dir), str(archive))

    assert archive.exists()
    with tarfile.open(archive, "r:gz") as tf:
        names = tf.getnames()
        assert any("file1.txt" in name for name in names)
        assert any("file2.txt" in name for name in names)


#тестим untar
def test_untar_file_not_found(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = False

    fake_pathlib_path_class.return_value = path_obj

    with pytest.raises(FileNotFoundError):
        service.untar("nonexistent.tar.gz", None)


def test_untar_success(service: OSConsoleServiceBase, tmp_path: Path):
    test_dir = tmp_path / "source_dir"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("content")
    archive = tmp_path / "archive.tar.gz"

    with tarfile.open(archive, "w:gz") as tf:
        tf.add(test_dir / "file.txt", arcname="file.txt")

    extract_dir = tmp_path / "extract_dir"
    service.untar(str(archive), str(extract_dir))

    assert (extract_dir / "file.txt").exists()
    assert (extract_dir / "file.txt").read_text() == "content"


def test_untar_to_none(service: OSConsoleServiceBase, tmp_path: Path):
    current_dir = Path.cwd()
    try:
        os.chdir(tmp_path)
        # Создаем архив
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        archive = tmp_path / "archive.tar.gz"

        with tarfile.open(archive, "w:gz") as tf:
            tf.add(test_file, arcname="file.txt")

        # Распаковываем в None (текущую директорию)
        service.untar(str(archive), None)

        assert (tmp_path / "file.txt").exists()
    finally:
        os.chdir(current_dir)


#тестим grep
def test_grep_invalid_regex(service: OSConsoleServiceBase, tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    with pytest.raises(re.error):
        service.grep("[invalid regex", str(test_file), r=False, ignore_case=False)


def test_grep_file_not_recursive(service: OSConsoleServiceBase, tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2 with pattern\nline3")

    results = service.grep("pattern", str(test_file), r=False, ignore_case=False)

    assert len(results) == 1
    assert "pattern" in results[0]
    assert "line2" in results[0]


def test_grep_file_ignore_case(service: OSConsoleServiceBase, tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("LINE1\nLINE2 WITH PATTERN\nline3")

    results = service.grep("pattern", str(test_file), r=False, ignore_case=True)

    assert len(results) == 1
    assert "PATTERN" in results[0]


def test_grep_directory_recursive(service: OSConsoleServiceBase, tmp_path: Path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("line1\nline2 with pattern\nline3")
    (test_dir / "file2.txt").write_text("no pattern here")
    subdir = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("another pattern here")

    results = service.grep("pattern", str(test_dir), r=True, ignore_case=False)

    assert len(results) == 2
    assert any("file1.txt" in r for r in results)
    assert any("file3.txt" in r for r in results)


def test_grep_directory_not_recursive(service: OSConsoleServiceBase, tmp_path: Path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("line with pattern")
    (test_dir / "file2.txt").write_text("no pattern")
    subdir = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("pattern in subdir")

    results = service.grep("pattern", str(test_dir), r=False, ignore_case=False)

    assert len(results) == 1
    assert "file1.txt" in results[0]
    assert not any("file3.txt" in r for r in results)


def test_grep_no_matches(service: OSConsoleServiceBase, tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\nline3")

    results = service.grep("nonexistent", str(test_file), r=False, ignore_case=False)

    assert len(results) == 0


def test_format_long_file(service: OSConsoleServiceBase, tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    result = service.format_long(test_file)

    assert test_file.name in result
    assert "-" in result  # тип файла
    assert isinstance(result, str)


def test_format_long_directory(service: OSConsoleServiceBase, tmp_path: Path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    result = service.format_long(test_dir)

    assert test_dir.name in result
    assert "d" in result  # тип директории
    assert isinstance(result, str)


def test_format_long_error_handling(service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture):
    entry = mocker.create_autospec(Path, instance=True, spec_set=True)
    entry.name = "test.txt"
    entry.stat.side_effect = OSError("Permission denied")
    result = service.format_long(entry)

    assert entry.name in result
    assert isinstance(result, str)
