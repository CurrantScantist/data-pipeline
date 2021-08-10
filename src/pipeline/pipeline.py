import json
import os
import re
import subprocess
import ssl
import time
import datetime

import git
import requests
from tqdm.auto import tqdm
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
CONNECTION_STRING = os.environ.get('CONNECTION_STRING')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPOS_DIR = os.path.join(CURRENT_DIR, "tmp")

if not os.path.exists(REPOS_DIR):
    os.mkdir(REPOS_DIR)


class Progress(git.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        tqdm.write(self._cur_line)


class RemoteRepoNotFoundError(Exception):
    """
    Custom error for when a remote repository is not found on github.com
    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)


class HTTPError(Exception):
    """
    Custom error for when a request returns an unexpected status code
    """

    def __init__(self, status_code):
        self.status_code = status_code
        self.message = f"Error with status code: {status_code}"
        super().__init__(self.message)


def get_releases(repo_owner, repo_name):
    """
    Retrieves a list of releases for a github repository
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :param repo_name: the name of the repository. Eg, 'react'
    :return: an array of release objects returned by the github REST API
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases?per_page=100&page=1"
    res = requests.get(url, auth=("user", ACCESS_TOKEN))

    if res.status_code != 200:
        raise HTTPError(res.status_code)

    releases = res.json()
    while 'next' in res.links.keys():
        res = requests.get(res.links['next']['url'], auth=("user", ACCESS_TOKEN))
        releases.extend(res.json())
    return releases


def check_local_repo_exists(repo_name):
    """
    Checks if the local repository has already been cloned from github
    :param repo_name: the name of the repository. Eg, 'react'
    :return: True if it exists, False otherwise
    """
    path = os.path.join(REPOS_DIR, repo_name)
    if os.path.exists(path):
        if os.path.isdir(path):
            # check that directory is a git repository
            try:
                _ = git.Repo(path).git_dir
                return True
            except git.exc.InvalidGitRepositoryError:
                return False
    return False


def check_remote_repo_exists(repo_owner, repo_name):
    """
    Checks if a repository exists on github.com
    :param repo_name: the name of the repository. Eg, 'react'
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :return: a tuple. first item: boolean of whether the repository exists on github.com, second item: the data object
    returned from the github API
    """
    response = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}", auth=('user', ACCESS_TOKEN))
    r = response.json()
    if response.status_code != 200:
        if response.status_code == 404:
            return False, r
        raise HTTPError(response.status_code)
    return True, r


def is_valid_repo_name(repo_str):
    """
    Checks if a repository url string is valid
    :param repo_str: repository name, containing the owner and repo separated by a /. eg. 'facebook/react'
    :return: True if valid, False otherwise
    """
    repo_url_pattern = r"[a-zA-Z0-9\-\_\.]+/[a-zA-Z0-9\-\_\.]+"
    return bool(re.fullmatch(repo_url_pattern, repo_str))


def clone_repo(repo_owner, repo_name, print_progress=True):
    """
    Clones a github repository locally
    :param print_progress: True for printing cloning progress to the console, False for no printing
    :param repo_name: the name of the repository. Eg, 'react'
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :return: repo: the Repo type from gitPython
    """
    remote_url = f"https://github.com/{repo_owner}/{repo_name}.git"
    repo_path = os.path.join(REPOS_DIR, repo_name)
    repo = git.Repo.clone_from(remote_url, repo_path, progress=Progress() if print_progress else None)

    return repo


def clean_up_repo(repo_name):
    """
    Removes a local repository that has been cloned by the pipeline
    :param repo_name: the name of the repository. Eg, 'react'
    :return: None
    """
    if check_local_repo_exists(repo_name):
        git.rmtree(os.path.join(REPOS_DIR, repo_name))


def push_release_to_mongodb(repo_owner, repo_name, tag, tag_data, client):
    """
    Pushes a single release to the 'releases' collection on mongoDB. This will use the update function and will upsert
    the data if it is not found in the collection
    :param client: the MongoDB client
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :param repo_name: the name of the repository. Eg, 'react'
    :param tag: the gitPython 'Tag' type
    :param tag_data: the data to be stored for the tag
    :return: None
    """
    db = client['test_db']
    release_collection = db['releases']
    search_dict = {
        "name": repo_name,
        "owner": repo_owner,
        "tag_name": tag.name
    }
    data_to_insert = {
        "name": repo_name,
        "owner": repo_owner,
        "tag_name": tag.name,
        "committed_date": tag.commit.committed_datetime,
        "LOC": tag_data,
    }
    release_collection.update_one(search_dict, {'$set': data_to_insert}, upsert=True)


def get_repository_metadata(repo_owner, repo_name):
    """
    Retrieves repository metadata from the Github REST API. Data includes general metadata, repository language stats,
    and repository topics (if available).
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :param repo_name: the name of the repository. Eg, 'react'
    :return: a dictionary containing the available data that could be retrieved
    """
    data = {}

    response = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}", auth=('user', ACCESS_TOKEN))
    r = response.json()

    if response.status_code != 200:
        if response.status_code == 404:
            raise RemoteRepoNotFoundError(f"Repository: {repo_owner}/{repo_name} could not be found on github.com")
        raise HTTPError(response.status_code)

    data["name"] = repo_name
    data["owner"] = repo_owner

    keys = ["description", "forks", "forks_count", "language", "stargazers_count", "watchers_count", "watchers", "size",
            "default_branch", "open_issues_count", "open_issues",
            "topics", "has_issues", "archived", "disabled", "visibility", "pushed_at", "created_at", "updated_at"]
    for key in keys:
        try:
            data[key] = r[key]
        except KeyError:
            pass

    # get the repository languages
    response = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}/languages",
                            auth=('user', ACCESS_TOKEN))
    data["languages"] = response.json()

    if response.status_code != 200:
        raise HTTPError(response.status_code)

    # get the topics for the repository
    headers_for_topics = {'Accept': 'application/vnd.github.mercy-preview+json'}
    response = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}/topics", headers=headers_for_topics,
                            auth=('user', ACCESS_TOKEN))

    if response.status_code != 200:
        raise HTTPError(response.status_code)

    data["topics"] = response.json()["names"]
    return data


def push_repository_to_mongodb(repo_owner, repo_name, data, client):
    """
    Pushes the repository metadata to the mongoDB database
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :param repo_name: the name of the repository. Eg, 'react'
    :param data: the metadata for the repository (python dictionary)
    :param client: the MongoDB client
    :return: None
    """
    db = client['test_db']
    repo_collection = db['repositories']

    search_dict = {
        "name": repo_name,
        "owner": repo_owner
    }
    repo_collection.update_one(search_dict, {'$set': data}, upsert=True)


def call_cloc(repo_path, include_header=False):
    """
    Calls CLOC for a local git repository. Information about CLOC can be found here: https://github.com/AlDanial/cloc
    :param repo_path: the path to the local git repository
    :param include_header: whether to include the header information in the output
    :return: The output of the 'cloc' tool in a dictionary format
    """
    p = subprocess.run(f"cloc . --vcs=git --json", cwd=repo_path, capture_output=True)
    if p.returncode != 0:
        raise SystemError(p.stderr)

    tag_data = json.loads(p.stdout)
    if not include_header:
        header_data = tag_data.pop('header')
    return tag_data


def get_commits_per_author(repo, default_branch):
    data = {}
    all_time_total = 0
    last_30_days_total = 0
    for commit in repo.iter_commits(default_branch):
        if commit.author.name in data.keys():
            data[commit.author.name]["all_time"] += 1
            all_time_total += 1
            # check if the commit was in the most recent 30 days
            if (datetime.datetime.now(datetime.timezone.utc) - commit.committed_datetime) < datetime.timedelta(days=30):
                data[commit.author.name]["last_30_days"] += 1
                last_30_days_total += 1
        else:
            data[commit.author.name] = {
                "name": commit.author.name,
                "all_time": 0,
                "last_30_days": 0
            }
    # sort authors by number of commits
    all_time_list = sorted(data.values(), key=lambda x: x["all_time"], reverse=True)
    last_30_days_list = sorted(data.values(), key=lambda x: x["last_30_days"], reverse=True)
    MAX_AUTHORS = 25
    to_return = {
        "all_time": {
            "top_25": all_time_list[:min(MAX_AUTHORS, len(all_time_list))],
            "total": all_time_total
        },
        "last_30_days": {
            "top_25": last_30_days_list[:min(MAX_AUTHORS, len(last_30_days_list))],
            "total": last_30_days_total
        }
    }
    print(f"num of authors: {len(all_time_list)}")
    with open('./test.json', 'w') as file:
        file.write(json.dumps(to_return))
    return to_return


def get_commits_per_month():
    pass


def process_repository(repo_str):
    """
    Processes the repository by doing the following:
        - validate the repository input
        - clone the repository (if not currently in the 'tmp' folder
        - retrieve a list of tags/releases for the repository
        - iterate through the tags/releases
        - calculate the LOC data for each tag/release by using a command line tool called 'cloc'
        - push the data to mongodb
    :param repo_str: concatenation of the repository owner and name separated by a '/'. Eg, 'facebook/react'
    :return: None
    """
    if not is_valid_repo_name(repo_str):
        tqdm.write("Invalid repository name!")
        return

    repo_owner, repo_name = repo_str.split("/")

    tqdm.write(f"Running pipeline process for repository: {repo_str}")

    # get repository metadata from the github API
    tqdm.write("Retrieving repository metadata from the Github REST API")
    try:
        data = get_repository_metadata(repo_owner, repo_name)
    except RemoteRepoNotFoundError as e:
        tqdm.write(e.message)
        return

    repo_path = os.path.join(REPOS_DIR, repo_name)

    # check if repository is already cloned locally
    if check_local_repo_exists(repo_name):
        tqdm.write("using cached repository")
        repo = git.Repo(repo_path)
    else:
        tqdm.write("cloning repository...")
        repo = clone_repo(repo_owner, repo_name)

    # get the tags from the repository
    tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
    tqdm.write(f"There were {len(tags)} tags found in the repository")

    tqdm.write("calculating commit data")
    get_commits_per_author(repo, data['default_branch'])

    # adding some tag related information to the repository metadata
    data["num_tags"] = len(tags)
    if len(tags) > 0:
        data["latest_tag"] = tags[-1].name
    else:
        data["latest_tag"] = None

    # get the mongoDB client
    mongo_client = MongoClient(CONNECTION_STRING, ssl_cert_reqs=ssl.CERT_NONE)

    # push the repository data to mongoDB
    tqdm.write("Pushing repository data to mongoDB")
    push_repository_to_mongodb(repo_owner, repo_name, data, mongo_client)

    g = git.Git(repo_path)  # initialise git in order to checkout each tag
    tag_loop = tqdm(tags, desc="calculating LOC for each tag")  # tqdm object for displaying the progress bar

    for tag in tag_loop:
        tag_name = tag.name
        tag_loop.set_description(f"processing tag: {tag}")
        tag_loop.refresh()

        tqdm.write(f"checking out tag: {tag}")
        g.checkout(tag_name)

        tqdm.write(f"counting LOC for tag: {tag}")
        # calling the 'cloc' command line tool to count LOC statistics for the repository
        tag_data = call_cloc(repo_path)  # this data can possibly be used later on

        tqdm.write("pushing to mongodb...")
        push_release_to_mongodb(repo_owner, repo_name, tag, tag_data, mongo_client)

    tqdm.write("deleting local repository...")

    repo.close()
    time.sleep(2)  # to wait for the previous git related processes to release the repository
    clean_up_repo(repo_name)
