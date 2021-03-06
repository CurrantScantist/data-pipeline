import pytest

from src.pipeline import pipeline
from src.pipeline.exceptions import *


def test_get_repository_metadata_successful(requests_mock):
    owner = "test_owner"
    name = "test_name"
    owner_obj = {
        'login': 'test',
        'avatar_url': 'a',
        'gravatar_id': 'b',
        'html_url': 'c',
        'type': 'd'
    }
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}", json={'forks': 10, 'owner': owner_obj}, status_code=200)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/languages", json={}, status_code=200)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/topics", json={"names": ['web-framework']},
                      status_code=200)
    resp = pipeline.get_repository_metadata(owner, name)
    assert resp == {
        'name': name,
        'owner': owner,
        'forks': 10,
        'owner_obj': owner_obj,
        'languages': {},
        'topics': ['web-framework']
    }


def test_get_repository_metadata_not_found(requests_mock):
    owner = "test_owner"
    name = "test_name"
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}", json={'forks': 10}, status_code=404)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/languages", json={}, status_code=200)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/topics", json={"names": ['web-framework']},
                      status_code=200)
    with pytest.raises(RemoteRepoNotFoundError) as err:
        pipeline.get_repository_metadata(owner, name)


def test_get_repository_metadata_http_error(requests_mock):
    owner = "test_owner"
    name = "test_name"
    owner_obj = {
        'login': 'test',
        'avatar_url': 'a',
        'gravatar_id': 'b',
        'html_url': 'c',
        'type': 'd'
    }
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}", json={'forks': 10, 'owner': owner_obj}, status_code=400)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/languages", json={}, status_code=200)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/topics", json={"names": ['web-framework']},
                      status_code=200)
    with pytest.raises(HTTPError) as err:
        pipeline.get_repository_metadata(owner, name)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}", json={'forks': 10, 'owner': owner_obj}, status_code=200)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/languages", json={}, status_code=400)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/topics", json={"names": ['web-framework']},
                      status_code=200)
    with pytest.raises(HTTPError) as err:
        pipeline.get_repository_metadata(owner, name)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}", json={'forks': 10, 'owner': owner_obj}, status_code=200)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/languages", json={}, status_code=200)
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/topics", json={"names": ['web-framework']},
                      status_code=400)
    with pytest.raises(HTTPError) as err:
        pipeline.get_repository_metadata(owner, name)


def test_get_releases_successful(requests_mock):
    owner = "test_owner"
    name = "test_name"
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/releases?per_page=100&page=1", json=[])
    resp = pipeline.get_releases(owner, name)
    assert resp == []


def test_get_releases_http_error(requests_mock):
    owner = "test_owner"
    name = "test_name"
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/releases?per_page=100&page=1", json=[],
                      status_code=400)
    with pytest.raises(HTTPError) as err:
        pipeline.get_releases(owner, name)
