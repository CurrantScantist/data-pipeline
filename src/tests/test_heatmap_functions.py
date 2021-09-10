import pytest
import datetime
from src.pipeline import generate_heatmap_data
from unittest.mock import MagicMock
import json
import git
import os
from unittest.mock import patch, mock_open


def test_date_span():
    pass


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

    data = generate_heatmap_data.retrieve_issues(repo, 1)
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
    pass


def test_retrieve_commits():
    pass


def test_generate_heatmap_data():
    pass
