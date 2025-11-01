from logging import Logger
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from src.services.windows_console import WindowsConsoleService

@pytest.fixture
def logger(mocker: MockerFixture) -> Logger:
    return mocker.Mock()


@pytest.fixture
def service(logger: Logger):
    return WindowsConsoleService(logger)


@pytest.fixture
def fake_pathlib_path_class(mocker: MockerFixture) -> Mock:
    mock_path_cls = mocker.patch("src.services.windows_console.Path")
    return mock_path_cls
