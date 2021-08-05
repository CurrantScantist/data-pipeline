import pytest
from unittest import mock
from src.pipeline import LOC_per_release


def test_repository_name_validation():
    valid = ["f/r", "facebook/react", "ABC/defg", "a-hyphen/a-hyphen", "a.dot/a.dot"]
    invalid = ["/", "", "a/", "f//r", "facebook/", "/react", "vue js/vue", "vuejs /vue", "vuejs/ vue", "vuejs/vue/"]

    for repo_str in valid:
        assert LOC_per_release.is_valid_repo_name(repo_str), f"{repo_str} is a valid name"

    for repo_str in invalid:
        assert not LOC_per_release.is_valid_repo_name(repo_str), f"{repo_str} is an invalid name"
