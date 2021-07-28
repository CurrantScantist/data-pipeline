import unittest
import LOC_per_release

class TestPipeline(unittest.TestCase):
    def setUp(self) -> None:
        return

    def test_repository_string(self):
        self.assertTrue(LOC_per_release.is_valid_repo_name('facebook/react'), msg="'facebook/react' is a valid name")
        self.assertFalse(LOC_per_release.is_valid_repo_name('facebook//react'), msg="'facebook//react' is an invalid name")

    def tearDown(self) -> None:
        pass
