import pytest
# import sys
# sys.path.insert(1,'/data-pipeline/src/pipeline')
from src.pipeline import sca_helpers
from src.pipeline.exceptions import *
from unittest.mock import MagicMock
import json
import git
import os
from unittest.mock import patch, mock_open


def test_download_scantist_bom_detector_downloaded(mocker, requests_mock):
    test_url = "http://test_url.test"
    mocker.patch(
        'os.path.exists',
        return_value=False
    )
    requests_mock.get(test_url, content=bytes('test_content', 'utf-8'), status_code=200)

    open_mock = mock_open()
    with patch("src.pipeline.sca_helpers.open", open_mock, create=False):
        result = sca_helpers.download_scantist_bom_detector('test', url=test_url)
        assert result == (True, os.path.join("test", "test_url.test"))

    open_mock.assert_called_with(os.path.join("test", "test_url.test"), "wb")
    open_mock.return_value.write.assert_called_once_with(bytes("test_content", 'utf-8'))


def test_download_scantist_bom_detector_not_downloaded(mocker):
    mocker.patch(
        'os.path.exists',
        return_value=True
    )
    result = sca_helpers.download_scantist_bom_detector('test')
    assert result == (False, os.path.join("test", "scantist-bom-detect.jar"))


def test_download_scantist_bom_detector_error(requests_mock):
    test_url = "http://test_url.test"
    requests_mock.get(test_url, json={}, status_code=404)
    with pytest.raises(HTTPError) as err:
        sca_helpers.download_scantist_bom_detector('', url=test_url)


def test_call_scantist_sca():
    pass


def test_generate_node_link_data():
    pass


# push scantist sca data to mongodb

def test_collect_scantist_sca_data():
    pass
