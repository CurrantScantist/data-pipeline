import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_logger():
    mock_logger = MagicMock()
    mock_logger.info = MagicMock(return_value=None)
    mock_logger.warn = MagicMock(return_value=None)
    mock_logger.warning = MagicMock(return_value=None)
    mock_logger.error = MagicMock(return_value=None)
    mock_logger.exception = MagicMock(return_value=None)
    mock_logger.debug = MagicMock(return_value=None)
    return mock_logger


@pytest.fixture
def repo_owner():
    return "test_repo_owner"


@pytest.fixture
def repo_name():
    return "test_repo_name"
