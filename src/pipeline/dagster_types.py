from dagster import DagsterType
from dagster.core.instance import MayHaveInstanceWeakref
import pipeline


def repo_check(repo):
    if isinstance(repo, str):
        return pipeline.is_valid_repo_name(repo)
    return False

Repository = DagsterType(
    name="Repository",
    description="The combination of the owner and repository name separated by a '/'. Example: ```Microsoft/vscode```",
    type_check_fn=lambda _, value: repo_check(value),
)


def metadata_check(metadata):
    if not isinstance(metadata, dict):
        return False
    expected = [
        ("projectUrl", str),
        ("versionNo", str),
        ("versionLastUpdatedDate", str),
        ("versionLastCVEDate", str),
        ("versionPackageManager", str),
        ("versionLanguages", str),
        ("versionLinesOfCode", int),
        ("versionSize", int),
        ("versionNumberOfCommits", int)
    ]
    for key, val_type in expected:
        if key not in metadata:
            return False
        if not isinstance(metadata[key], val_type):
            return False
    return True
     
Metadata = DagsterType(
    name="Metadata",
    description="",
    type_check_fn=lambda _, value: metadata_check(value),
)
