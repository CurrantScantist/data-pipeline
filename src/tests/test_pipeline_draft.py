import unittest
from src.pipeline import LOC_per_release


class TestPipeline(unittest.TestCase):
    def setUp(self) -> None:
        return

    def test_repository_string(self):
        valid = ["f/r", "facebook/react", "ABC/defg", "a-hyphen/a-hyphen", "a.dot/a.dot"]
        invalid = ["f//r", "facebook/", "/react", "vue js/vue", "vuejs /vue", "vuejs/ vue", "vuejs/vue/"]

        for repo_str in valid:
            self.assertTrue(LOC_per_release.is_valid_repo_name(repo_str), msg=f"{repo_str} is a valid name")

        for repo_str in invalid:
            self.assertFalse(LOC_per_release.is_valid_repo_name(repo_str), msg=f"{repo_str} is an invalid name")

    def tearDown(self) -> None:
        pass
