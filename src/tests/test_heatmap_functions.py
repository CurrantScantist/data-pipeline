import datetime
from src.pipeline import generate_heatmap_data
from unittest.mock import MagicMock
import json
import os
from src.tests.test_contributor_commit_functions import generate_fake_repo


def test_date_span():
    date_format = "%Y-%m-%dT%H:%M:%S%z"
    start = datetime.datetime.strptime("2020-01-12T12:00:00Z", date_format) - datetime.timedelta(weeks=2)
    end = datetime.datetime.strptime("2020-01-12T12:00:00Z", date_format)
    actual = list(generate_heatmap_data.date_span(start, end))
    expected = [
        (datetime.datetime(2019, 12, 29, 12, 0, tzinfo=datetime.timezone.utc),
         datetime.datetime(2020, 1, 5, 12, 0, tzinfo=datetime.timezone.utc)),
        (datetime.datetime(2020, 1, 5, 12, 0, tzinfo=datetime.timezone.utc),
         datetime.datetime(2020, 1, 12, 12, 0, tzinfo=datetime.timezone.utc))
    ]
    assert expected == actual


def test_issue_is_open_in_week_true():
    str_format = "%Y-%m-%dT%H:%M:%S%z"
    issue = {
        "created_at": "2020-01-02T12:00:00Z",
        "state": "closed",
        "closed_at": "2020-01-15T12:00:00Z"
    }

    start = datetime.datetime.strptime("2020-01-04T12:00:00Z", str_format)
    end = datetime.datetime.strptime("2020-01-12T12:00:00Z", str_format)
    assert generate_heatmap_data.issue_is_open_in_week(issue, start, end)

    issue["state"] = "open"
    issue["closed_at"] = None
    assert generate_heatmap_data.issue_is_open_in_week(issue, start, end)


def test_issue_is_open_in_week_false():
    str_format = "%Y-%m-%dT%H:%M:%S%z"
    issue = {
        "created_at": "2020-01-02T12:00:00Z",
        "state": "closed",
        "closed_at": "2020-01-10T12:00:00Z"
    }

    start = datetime.datetime.strptime("2020-01-04T12:00:00Z", str_format)
    end = datetime.datetime.strptime("2020-01-12T12:00:00Z", str_format)
    assert not generate_heatmap_data.issue_is_open_in_week(issue, start, end)

    issue["state"] = "open"
    issue["closed_at"] = None
    issue["created_at"] = "2020-01-07T12:00:00Z"
    assert not generate_heatmap_data.issue_is_open_in_week(issue, start, end)


def test_pull_request_is_modified_in_week():
    str_format = "%Y-%m-%dT%H:%M:%S%z"

    for option in ['created', 'closed', 'merged']:
        pr = {f"{option}_at": "2020-01-02T12:00:00Z"}

        start = datetime.datetime.strptime("2020-01-04T12:00:00Z", str_format)
        end = datetime.datetime.strptime("2020-01-12T12:00:00Z", str_format)
        assert not generate_heatmap_data.pull_request_is_modified_in_week(pr, start, end, option)

        pr[f"{option}_at"] = "2020-01-07T12:00:00Z"
        assert generate_heatmap_data.pull_request_is_modified_in_week(pr, start, end, option)

        pr[f"{option}_at"] = "2020-01-20T12:00:00Z"
        assert not generate_heatmap_data.pull_request_is_modified_in_week(pr, start, end, option)


def test_commit_is_in_week():
    str_format = "%Y-%m-%dT%H:%M:%S%z"
    commit = MagicMock()
    commit.committed_datetime = datetime.datetime.strptime("2020-01-04T12:00:00Z", str_format)

    start = datetime.datetime.strptime("2020-01-04T12:00:00Z", str_format)
    end = datetime.datetime.strptime("2020-01-12T12:00:00Z", str_format)
    assert not generate_heatmap_data.commit_is_in_week(commit, start, end)

    commit.committed_datetime = datetime.datetime.strptime("2020-01-07T12:00:00Z", str_format)
    assert generate_heatmap_data.commit_is_in_week(commit, start, end)

    commit.committed_datetime = datetime.datetime.strptime("2020-01-20T12:00:00Z", str_format)
    assert not generate_heatmap_data.commit_is_in_week(commit, start, end)


def test_retrieve_issues():
    issues = [
        {
            "data": {"number": "1",
                     "user": {"login": "user_a"},
                     "created_at": "2020-01-12T12:00:00Z",
                     "updated_at": "2020-01-14T12:00:00Z",
                     "closed_at": None,
                     "state": "open",
                     "comments_data": [
                         {"user": {"login": "user_b"}, "created_at": "2020-01-14T12:00:00Z"}
                     ]
                     }
        },
        {
            "data": {"number": "2",
                     "user": {"login": "user_b"},
                     "created_at": "2020-01-12T12:00:00Z",
                     "updated_at": "2020-01-12T12:00:00Z",
                     "closed_at": "2020-01-12T12:00:00Z",
                     "state": "closed",
                     "comments_data": [
                         {"user": {"login": "user_c"}, "created_at": "2020-01-20T12:00:00Z"},
                         {"user": {"login": "user_d"}, "created_at": "2020-01-21T12:00:00Z"}
                     ]
                     }
        }
    ]

    repo = MagicMock()
    repo.fetch = MagicMock(return_value=issues)

    mock_collection = MagicMock()
    mock_collection.find = MagicMock(return_value={})
    mock_collection.update_one = MagicMock(return_value={})
    mock_client = {
        'test_db': {
            'issues': mock_collection
        }
    }
    owner = "owner"
    name = "name"

    data = generate_heatmap_data.retrieve_issues(owner, name, repo, 1, mock_client)

    mock_client['test_db']['issues'].find.assert_called_once()

    assert data == {
        "1": {
            "user": "user_a",
            "created_at": "2020-01-12T12:00:00Z",
            "updated_at": "2020-01-14T12:00:00Z",
            "closed_at": None,
            "state": "open",
            "comments": [
                {"user": "user_b", "created_at": "2020-01-14T12:00:00Z"}
            ]
        },
        "2": {
            "user": "user_b",
            "created_at": "2020-01-12T12:00:00Z",
            "updated_at": "2020-01-12T12:00:00Z",
            "closed_at": "2020-01-12T12:00:00Z",
            "state": "closed",
            "comments": [
                {"user": "user_c", "created_at": "2020-01-20T12:00:00Z"},
                {"user": "user_d", "created_at": "2020-01-21T12:00:00Z"},
            ]
        },
    }


def test_retrieve_pull_requests():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, 'github_pull_request.json'), 'r') as file:
        pull_requests = json.load(file)["data"]

    pull_requests = [{"data": pr} for pr in pull_requests]

    repo = MagicMock()
    repo.fetch = MagicMock(return_value=pull_requests)

    with open(os.path.join(current_dir, 'pull_request_results.json'), 'r') as file:
        expected_data = json.load(file)

    mock_collection = MagicMock()
    mock_collection.find = MagicMock(return_value={})
    mock_collection.update_one = MagicMock(return_value={})
    mock_client = {
        'test_db': {
            'pull_requests': mock_collection
        }
    }
    owner = "owner"
    name = "name"

    actual_data = generate_heatmap_data.retrieve_pull_requests(owner, name, repo, 1, mock_client)

    mock_client['test_db']['pull_requests'].find.assert_called_once()

    assert actual_data == expected_data


def test_retrieve_commits():
    repo = generate_fake_repo('test_repo.json')

    actual_result = generate_heatmap_data.retrieve_commits(repo)
    expected_result = [
        {
            "hexsha": "abcdef",
            "committed_datetime": "2020-01-09 15:38:43+01:00",
            "author": {"name": "Stephen A"}
        },
        {
            "hexsha": "abcde",
            "committed_datetime": "2020-02-09 15:38:43+01:00",
            "author": {"name": "Stephen B"}
        },
        {
            "hexsha": "abcd",
            "committed_datetime": "2020-05-09 15:38:43+01:00",
            "author": {"name": "Stephen C"}
        },
        {
            "hexsha": "ab",
            "committed_datetime": "2020-05-09 15:38:43+01:00",
            "author": {"name": "Stephen E"}
        },
        {
            "hexsha": "a",
            "committed_datetime": "2020-06-09 15:38:43+01:00",
            "author": {"name": "Stephen F"}
        }
    ]
    date_format = "%Y-%m-%d %H:%M:%S%z"

    assert len(expected_result) == len(actual_result)

    for i, _ in enumerate(expected_result):
        assert expected_result[i]["hexsha"] == actual_result[i].hexsha
        c_date = datetime.datetime.strptime(expected_result[i]["committed_datetime"], date_format)
        assert c_date == actual_result[i].committed_datetime
        assert expected_result[i]["author"]["name"] == actual_result[i].author.name
