import json
import os
import re
import subprocess
from operator import itemgetter

import git
import requests
from tqdm.auto import tqdm

import secrets

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPOS_DIR = os.path.join(CURRENT_DIR, "tmp")

if not os.path.exists(REPOS_DIR):
    os.mkdir(REPOS_DIR)

data = {}


def get_releases(repo_owner, repo_name):
    """
    Retrieves a list of releases for a github repository
    :return: an array of release objects returned by the github REST API
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases?per_page=100&page=1"
    res = requests.get(url, auth=("user", secrets.ACCESS_TOKEN))
    releases = res.json()
    while 'next' in res.links.keys():
        res = requests.get(res.links['next']['url'], auth=("user", secrets.ACCESS_TOKEN))
        releases.extend(res.json())
    return releases


def check_repo(repo_name):
    """
    Checks if the local repository has already been cloned from github
    :param repo_name: the name of the repository. Eg, 'react'
    :return:
    """
    # TODO: check the directory is not empty and is a git repository
    if os.path.exists(os.path.join(REPOS_DIR, repo_name)):
        if os.path.isdir(os.path.join(REPOS_DIR, repo_name)):
            return True
    return False


def is_valid_repo_name(repo_str):
    """
    Checks if a repository url string is valid
    :param repo_str: repository name, containing the owner and repo separated by a /. eg. 'facebook/react'
    :return: True if valid, False otherwise
    """
    repo_url_pattern = r"[a-zA-Z0-9\-\_\.]+/[a-zA-Z0-9\-\_\.]+"
    return bool(re.fullmatch(repo_url_pattern, repo_str))


def clone_repo(repo_owner, repo_name):
    """
    Clones a github repository locally
    :param repo_name: the name of the repository. Eg, 'react'
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :return: None
    """
    p1 = subprocess.run(f"git clone https://github.com/{repo_owner}/{repo_name}.git", capture_output=True, text=True,
                        cwd=REPOS_DIR)
    if p1.returncode != 0:
        raise SystemError(p1.stderr)


def clean_up_repo(repo_name):
    """
    Removes a local repository that has been cloned by the pipeline
    :param repo_name: the name of the repository. Eg, 'react'
    :return: None
    """
    if check_repo(repo_name):
        git.rmtree(os.path.join(REPOS_DIR, repo_name))


def process_repository(repo_str):

    if not is_valid_repo_name(repo_str):
        tqdm.write("Invalid repository!")
        return

    repo_owner, repo_name = repo_str.split("/")

    # check if repository is already there
    if check_repo(repo_name):
        tqdm.write("using cached repository")
        pass
    else:
        tqdm.write("cloning repository...")
        clone_repo(repo_owner, repo_name)

    releases = get_releases(repo_owner, repo_name)
    assert len(releases) > 0, "There must be at least one release"

    # sorting the releases for slightly better efficiency
    releases = sorted(releases, key=itemgetter('tag_name'))

    release_loop = tqdm(releases, desc="calculating LOC for each release")

    for release in release_loop:
        tag = release["tag_name"]

        release_loop.set_description(f"processing release: {tag}")
        release_loop.refresh()

        tqdm.write(f"checking out tag: {tag}")
        p2 = subprocess.run(f"git checkout {tag}", cwd=f"{REPOS_DIR}/{repo_name}", capture_output=True)
        if p2.returncode == 0:
            pass
        else:
            raise SystemError(p2.stderr)
        tqdm.write(f"counting LOC for tag: {tag}")
        p3 = subprocess.run(f"cloc . --vcs=git --json", cwd=f"{REPOS_DIR}/{repo_name}", capture_output=True)
        if p3.returncode == 0:
            pass
        else:
            raise SystemError(p3.stderr)
        release_data = json.loads(p3.stdout)
        header_data = release_data.pop('header')
        data[tag] = release_data

    with open(os.path.join(CURRENT_DIR, f'loc_for_{repo_owner}/{repo_name}.json'), 'w') as file:
        file.write(json.dumps(data))

    tqdm.write("deleting local repository...")
    clean_up_repo(repo_name)


if __name__ == '__main__':
    process_repository("facebook/react")
