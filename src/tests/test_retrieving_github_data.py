from src.pipeline import pipeline
from unittest import mock


def test_get_repository_metadata(requests_mock):
    owner = "test_owner"
    name = "test_name"
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}", json={})
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/languages", json={})
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/topics", json={})
    resp = pipeline.get_repository_metadata(owner, name)
    assert resp == {
        'name': name,
        'owner': owner,
        'languages': {}
    }


def test_get_releases(requests_mock):
    owner = "test_owner"
    name = "test_name"
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/releases?per_page=100&page=1", json=[])
    resp = pipeline.get_releases(owner, name)
    assert resp == []
