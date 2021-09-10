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
    format = "%Y-%m-%dT%H:%M:%S%z"
    issue = {
        "created_at": "2020-01-02T12:00:00Z",
        "state": "closed",
        "closed_at": "2020-01-15T12:00:00Z"
    }

    start = datetime.datetime.strptime("2020-01-04T12:00:00Z", format)
    end = datetime.datetime.strptime("2020-01-12T12:00:00Z", format)
    assert generate_heatmap_data.issue_is_open_in_week(issue, start, end)

    issue["state"] = "open"
    issue["closed_at"] = None
    assert generate_heatmap_data.issue_is_open_in_week(issue, start, end)


def test_issue_is_open_in_week_false():
    format = "%Y-%m-%dT%H:%M:%S%z"
    issue = {
        "created_at": "2020-01-02T12:00:00Z",
        "state": "closed",
        "closed_at": "2020-01-10T12:00:00Z"
    }

    start = datetime.datetime.strptime("2020-01-04T12:00:00Z", format)
    end = datetime.datetime.strptime("2020-01-12T12:00:00Z", format)
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
    pass


def test_retrieve_pull_requests():
    pass


def test_retrieve_commits():
    pass


def test_generate_heatmap_data():
    pass
