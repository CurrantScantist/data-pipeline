import subprocess
import json
import requests
from tqdm import tqdm
import os
import re

import secrets

BASE_DIR = "./repositories"

repo_name = "react"
repo_owner = "facebook"
data = {}

# releases = ["v17.0.2", "v17.0.1", "v17.0.0"]


def get_releases():
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases?per_page=100&page=1"
    res = requests.get(url, auth=("user", secrets.ACCESS_TOKEN))
    releases = res.json()
    while 'next' in res.links.keys():
        res = requests.get(res.links['next']['url'], auth=("user", secrets.ACCESS_TOKEN))
        releases.extend(res.json())
    return releases


def check_repo(repo_name):
    # TODO: check the directory is not empty and is a git repository
    if os.path.exists(f"{BASE_DIR}/{repo_name}"):
        if os.path.isdir(f"{BASE_DIR}/{repo_name}"):
            return True
    return False


def is_valid_repo_name(name):
    """
    Function for checking repository url string is valid
    :param name: repository name, containing the owner and repo separated by a /. eg. 'facebook/react'
    :return: True if valid, False otherwise
    """
    repo_url_pattern = r"[a-zA-Z0-9\-\_\.]+/[a-zA-Z0-9\-\_\.]+"
    return bool(re.fullmatch(repo_url_pattern, name))


def clone_repo(repo_name, repo_owner):
    p1 = subprocess.run(f"git clone https://github.com/{repo_owner}/{repo_name}.git", capture_output=True, text=True,
                        cwd=BASE_DIR)
    if p1.returncode != 0:
        raise SystemError(p1.stderr)


def process_repository(repo_name, repo_owner):

    # check if repository is already there
    if check_repo(repo_name):
        print("using cached repository")
        pass
    else:
        print("there must be an error")
        exit(-1)
        clone_repo(repo_name, repo_owner)

    releases = get_releases()
    assert len(releases) > 0, "There must be at least one release"

    for release in tqdm(releases, desc="calculating LOC for each release"):
        tag = release["tag_name"]
        print(f"checking out tag: {tag}")
        p2 = subprocess.run(f"git checkout {tag}", cwd=f"{BASE_DIR}/{repo_name}", capture_output=True)
        if p2.returncode == 0:
            pass
        else:
            print("error")
            break
        print(f"count LOC for tag: {tag}")
        p3 = subprocess.run(f"cloc . --vcs=git --json", cwd=f"{BASE_DIR}/{repo_name}", capture_output=True)
        if p3.returncode == 0:
            pass
        else:
            print("error")
            break
        data[tag] = json.loads(p3.stdout)

    with open(f'loc_per_release_for_{repo_owner}_{repo_name}.json', 'w') as file:
        file.write(json.dumps(data))


# process_repository(repo_name, repo_owner)
