from dagster import DagsterType
from dagster.core.instance import MayHaveInstanceWeakref


def repo_check(repo):
    if isinstance(repo, str):
        repo_split = repo.split("/")
        if len(repo_split) == 2:
            owner, repository = repo_split
            # TODO: check the naming conventions for invalid characters
            
            return True
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
    for key, type in expected:
        if key not in metadata:
            return False
        else:
            if not isinstance(metadata[key], type):
                return False
    
    # TODO: check ranges for integers, and check dates, version numbers, etc
    return True
     
Metadata = DagsterType(
    name="Metadata",
    description="",
    type_check_fn=lambda _, value: metadata_check(value),
)
