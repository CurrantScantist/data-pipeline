from unittest.mock import MagicMock
from src.pipeline import pipeline


def test_repository_name_validation():
    valid = ["f/r", "facebook/react", "ABC/defg", "a-hyphen/a-hyphen", "a.dot/a.dot", "Mix.ed/Ab.c"]
    invalid = ["/", "", "a/", "f//r", "facebook/", "/react", "vue js/vue", "vuejs /vue", "vuejs/ vue", "vuejs/vue/",
               "a", "", " "]

    for repo_str in valid:
        assert pipeline.is_valid_repo_name(repo_str), f"{repo_str} is a valid name"

    for repo_str in invalid:
        assert not pipeline.is_valid_repo_name(repo_str), f"{repo_str} is an invalid name"


def test_pushing_release_data_to_db():
    mock_collection = MagicMock()
    mock_collection.update_one = MagicMock(return_value={})
    mock_client = {
        'test_db': {
            'repositories': mock_collection
        }
    }
    owner = "owner"
    repo = "repo"
    pipeline.push_repository_to_mongodb(owner, repo, {}, mock_client)
    assert mock_client['test_db']['repositories'].update_one.called


def test_pushing_repository_data_to_db():
    pass
