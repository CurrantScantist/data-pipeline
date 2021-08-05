from src.pipeline import LOC_per_release
from unittest import mock


def test_get_repository_metadata(requests_mock):
    owner = "test_owner"
    name = "test_name"
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}", json={})
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/languages", json={})
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/topics", json={})
    resp = LOC_per_release.get_repository_metadata(owner, name)
    assert resp == {
        'name': name,
        'owner': owner,
        'languages': {}
    }


def test_get_releases(requests_mock):
    owner = "test_owner"
    name = "test_name"
    requests_mock.get(f"https://api.github.com/repos/{owner}/{name}/releases?per_page=100&page=1", json=[])
    resp = LOC_per_release.get_releases(owner, name)
    assert resp == []




"""
r = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}", auth=('user', secrets.ACCESS_TOKEN))
r = r.json()

r = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}/languages", auth=('user', secrets.ACCESS_TOKEN))
data["languages"] = r.json()

headers_for_topics = {
    'Accept': 'application/vnd.github.mercy-preview+json'
}
try:
    r = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}/topics", headers=headers_for_topics,
                     auth=('user', secrets.ACCESS_TOKEN))
    data["topics"] = r.json()["names"]
"""
