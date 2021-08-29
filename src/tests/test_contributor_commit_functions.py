import json
from unittest.mock import MagicMock
import unittest
from src.pipeline import pipeline
import datetime
import os
import time


def test_get_commits_per_author():
    # go through each line of the function get_monthly_commit_data, and ensure that each line is mocked out.
    current_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(current_dir, 'test_repo2.json'), 'r') as f:
        fakerepo = json.load(f)  # our fakerepo

    def iter_commits(branch_name):
        commits = fakerepo[branch_name]
        commit_objs = []
        date_format = "%Y-%m-%d %H:%M:%S%z"
        for commit in commits:
            c_mock = MagicMock()
            c_mock.hexsha = commit["hexsha"]
            c_mock.committed_datetime = datetime.datetime.strptime(commit["committed_datetime"], date_format)
            c_mock.author.name = commit["author"]["name"]
            commit_objs.append(c_mock)

        return commit_objs

    branches = []
    for branch in ["branch1", "branch2"]:
        mock = MagicMock()
        mock.name = branch
        branches.append(mock)

    repo = MagicMock(references=branches, iter_commits=iter_commits)

    # mocker.patch(
    #     'datetime.datetime.now(datetime.timezone.utc) - commit.committed_datetime) < datetime.timedelta(days=30)',
    #     return_value="True"
    # )
    # Change if (datetime.datetime.now(datetime.timezone.utc) - commit.committed_datetime) < datetime.timedelta(
    # days=30):
    # Ensure that datetime.now is 29/08/2021

    expected_result = {
        "all_time": {
            "top_25": [
                {
                    "name": "A",
                    "all_time": 3,
                    "last_30_days": 2,
                },
                {
                    "name": "B",
                    "all_time": 2,
                    "last_30_days": 2,
                }
            ],
            "total": 5
        },
        "last_30_days": {
            "top_25": [
                {
                    "name": "A",
                    "all_time": 3,
                    "last_30_days": 2,
                },
                {
                    "name": "B",
                    "all_time": 2,
                    "last_30_days": 2,
                }
            ],
            "total": 4
        }
    }
    result = pipeline.get_commits_per_author(repo)

    assert expected_result == result


def test_get_monthly_commit_data():
    # go through each line of the function get_monthly_commit_data, and ensure that each line is mocked out.
    current_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(current_dir, 'test_repo.json'), 'r') as f:
        fakerepo = json.load(f)  # our fakerepo

    def iter_commits(branch_name):
        commits = fakerepo[branch_name]
        commit_objs = []
        date_format = "%Y-%m-%d %H:%M:%S%z"
        for commit in commits:
            c_mock = MagicMock()
            c_mock.hexsha = commit["hexsha"]
            c_mock.committed_datetime = datetime.datetime.strptime(commit["committed_datetime"], date_format)
            c_mock.author.name = commit["author"]["name"]
            commit_objs.append(c_mock)

        return commit_objs

    branches = []
    for branch in ["branch1", "branch2"]:
        mock = MagicMock()
        mock.name = branch
        branches.append(mock)

    repo = MagicMock(references=branches, iter_commits=iter_commits)

    expected_result = {
        "month_data": [
            {
                "month": "2020-06",
                "commits": 1,
                "contributor_count": 1,
            },
            {
                "month": "2020-05",
                "commits": 2,
                "contributor_count": 2,
            },
            {
                "month": "2020-02",
                "commits": 1,
                "contributor_count": 1,
            },
            {
                "month": "2020-01",
                "commits": 1,
                "contributor_count": 1,
            }
        ]
    }

    result = pipeline.get_monthly_commit_data(repo)

    assert expected_result == result
