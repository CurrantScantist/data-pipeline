import json
from unittest.mock import MagicMock
import unittest
# from src.pipeline import pipeline


def test_get_monthly_commit_data():
    # go through each line of the function get_monthly_commit_data, and ensure that each line is mocked out.
    with open('test_repo.json') as f:
        fakerepo = json.load(f)  # our fakerepo

    def iter_commits(branch_name):
        return fakerepo[branch_name]

    # make an object with attribute "references"
    repo = MagicMock(references=[MagicMock(name="branch1"), MagicMock(name="branch2")], iter_commits=iter_commits)




    # magic_repo = MagicMock()
    #
    # magic_repo.__getitem__.side_effect = fakerepo.__getitem__
    # print(magic_repo['branch1'])
    # for a in magic_repo.:
    #     print(a)

    # magic_repo = MagicMock()
    # dict = {'key_1': 'value'}
    # magic_repo.__getitem__.side_effect = dict.__getitem__
    #
    # # dict behaviour
    # print(magic_repo['key_1'])  # => 'value'
    # # magic_repo['key_2']  # => raise KeyError
    # #
    # # # mock behaviour
    # # magic_repo.foo(42)
    # # magic_repo.foo.assert_called_once_with(43)  # => raise AssertionError













    commits = []
    # print(repo.references) # [<MagicMock name='branch1' id='2070959730448'>, <MagicMock name='branch2' id='2070982233056'>]
    # for branch in repo.references:
    #     print(branch)

        # repo.iter_commits(branch)



        # for b in a.name:
        #     commits = repo.iter_commits(b)
    # print(commits)

    # commit_objs = [MagicMock(author=commit["author"]) for commit in commits]
    #
    # data_objs = [MagicMock(key=data["key"]) for data in dataset]
    #
    # print(repo.iter_commits("branch1"))


def test_split(self):
    s = 'hello world'
    self.assertEqual(s.split(), ['hello', 'world'])
    # check that s.split fails when the separator is not a string
    with self.assertRaises(TypeError):
        s.split(2)


# test_split()

test_get_monthly_commit_data()
