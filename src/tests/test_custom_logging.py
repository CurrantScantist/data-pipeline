import logging

from src.pipeline import pipeline
import datetime


def test_get_logger_returns_correct_class(tmpdir, mocker, repo_owner, repo_name):
    mocker.patch('src.pipeline.pipeline.get_current_repo_log_directory', return_value=tmpdir)
    logger = pipeline.get_logger("", "", datetime.datetime.now())
    assert isinstance(logger, pipeline.CustomLogger)
    assert isinstance(logger, logging.Logger)

    # checking that the logger has the correct handlers (and only 1 of each type)
    assert sum(1 for h in logger.handlers if isinstance(h, pipeline.CustomFileHandler)) == 1
    assert sum(1 for h in logger.handlers if isinstance(h, pipeline.TqdmLoggingHandler)) == 1
