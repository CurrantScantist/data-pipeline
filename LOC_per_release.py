import json
import os
import re
import subprocess
from operator import itemgetter
import ssl

import git
import requests
from tqdm.auto import tqdm
from pymongo import MongoClient

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


def check_local_repo_exists(repo_name):
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


def check_remote_repo_exists(repo_owner, repo_name):
    """
    Checks if a repository exists on github.com
    :param repo_name: the name of the repository. Eg, 'react'
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :return: a tuple. first item: boolean of whether the repository exists on github.com, second item: the data object
    returned from the github API
    """
    r = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}", auth=('user', secrets.ACCESS_TOKEN))
    r = r.json()
    if 'message' in r.keys():
        if r['message'] == 'Not Found':
            return False, r
    return True, r


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
    if check_local_repo_exists(repo_name):
        git.rmtree(os.path.join(REPOS_DIR, repo_name))


def push_release_to_mongodb(repo_owner, repo_name, release, release_data):
    """
    Pushes a single release to the 'releases' collection on mongoDB. This will use the update function and will upsert
    the data if it is not found in the collection
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :param repo_name: the name of the repository. Eg, 'react'
    :param release: the release object returned from the github REST API
    :param release_data: the data to be stored for the release
    :return: None
    """
    client = MongoClient(secrets.CONNECTION_STRING, ssl_cert_reqs=ssl.CERT_NONE)
    db = client['test_db']
    release_collection = db['releases']
    release_tag = release["tag_name"]
    search_dict = {
        "name": repo_name,
        "owner": repo_owner,
        "release": {"tag_name": release_tag}
    }
    data_to_insert = {
        "name": repo_name,
        "owner": repo_owner,
        "release": release,
        "LOC": release_data,
    }
    release_collection.update_one(search_dict, {'$set': data_to_insert}, upsert=True)


def process_repository(repo_str):
    if not is_valid_repo_name(repo_str):
        tqdm.write("Invalid repository name!")
        return

    repo_owner, repo_name = repo_str.split("/")

    # check if repository exists on github.com
    repo_exists, response = check_remote_repo_exists(repo_owner, repo_name)
    if not repo_exists:
        tqdm.write(f"Repository: {repo_owner}/{repo_name} could not be found on github.com")
        return

    # check if repository is already there
    if check_local_repo_exists(repo_name):
        tqdm.write("using cached repository")
        pass
    else:
        tqdm.write("cloning repository...")
        clone_repo(repo_owner, repo_name)

    releases = get_releases(repo_owner, repo_name)
    assert len(releases) > 0, "There must be at least one release"

    # sorting the releases for slightly better efficiency
    releases = sorted(releases, key=itemgetter('tag_name'), reverse=True)

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

        tqdm.write("pushing to mongodb...")
        push_release_to_mongodb(repo_owner, repo_name, release, release_data)
        # data[tag] = release_data

    tqdm.write("deleting local repository...")
    clean_up_repo(repo_name)


if __name__ == '__main__':
    repo_input = input("Please enter a repository (eg, 'facebook/react'): ")
    process_repository(repo_input)
