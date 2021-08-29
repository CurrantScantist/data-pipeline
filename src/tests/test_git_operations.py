import pytest
# import sys
# sys.path.insert(1,'/data-pipeline/src/pipeline')
from src.pipeline import pipeline
from src.pipeline.exceptions import *
from unittest.mock import MagicMock
import json
import git


def test_check_remote_repo_exists_successful(requests_mock):
    owner = 'owner'
    repo = 'repo'
    requests_mock.get(f"https://api.github.com/repos/{owner}/{repo}", json={}, status_code=200)
    assert pipeline.check_remote_repo_exists(owner, repo) == (True, {})


def test_check_remote_repo_exists_unsuccessful(requests_mock):
    owner = 'owner'
    repo = 'repo'
    requests_mock.get(f"https://api.github.com/repos/{owner}/{repo}", json={}, status_code=404)
    assert pipeline.check_remote_repo_exists(owner, repo) == (False, {})


def test_check_remote_repo_exists_error(requests_mock):
    owner = 'owner'
    repo = 'repo'
    requests_mock.get(f"https://api.github.com/repos/{owner}/{repo}", json={}, status_code=400)
    with pytest.raises(HTTPError) as err:
        pipeline.check_remote_repo_exists(owner, repo)


def test_call_cloc_successful(mocker):
    test_data = {'key': 'val', 'header': 'data'}
    result_mock = MagicMock(returncode=0, stdout=json.dumps(test_data), stderr='')
    mocker.patch(
        'subprocess.run',
        return_value=result_mock
    )

    results = pipeline.call_cloc('', False)
    assert results == {'key': 'val'}


def test_call_cloc_error(mocker):
    test_data = {'key': 'val', 'header': 'data'}
    result_mock = MagicMock(returncode=1, stdout=json.dumps(test_data), stderr='')
    mocker.patch(
        'subprocess.run',
        return_value=result_mock
    )
    with pytest.raises(SystemError) as err:
        results = pipeline.call_cloc('', False)


def test_clone_repo(mocker):
    owner = 'owner'
    repo = 'repo'
    mocker.patch(
        'git.Repo.clone_from',
        return_value='return'
    )
    result = pipeline.clone_repo(owner, repo, print_progress=False)
    assert result == 'return'


def test_check_local_repo_exists_does_exist(mocker):
    # testing the function works when there is a local repo
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('git.Repo', return_value=MagicMock(git_dir=''))
    assert pipeline.check_local_repo_exists('repo')


def test_check_local_repo_exists_doesnt_exist(mocker):
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('git.Repo', return_value=MagicMock(git_dir=''), side_effect=git.exc.InvalidGitRepositoryError)
    assert not pipeline.check_local_repo_exists('repo')


def test_clean_up_repo(mocker):
    mocker.patch('src.pipeline.pipeline.check_local_repo_exists', return_value=True)
    mocker.patch('git.rmtree', return_value=None)
    assert pipeline.clean_up_repo('repo') is None

# def test_get_monthly_commit_data(mocker):
#     # go through each line of the function get_monthly_commit_data, and ensure that each line is mocked out.
#
#
#     # load my fake repo
#     with open('test_repo.json') as f:
#         fakerepo = json.load(f) # our fakerepo
#
#     # run my pipeline.py function get_monthly_commit_data(fakerepo)
#     result_mock = MagicMock
#
#     mocker.patch('src.pipeline.pipeline.get_monthly_commit_data', return_value=result_mock)
#
#     assert repo.references
