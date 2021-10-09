import datetime
import json
import logging
import math
import os
import platform
import re
import ssl
import subprocess
import time

import colorama
import git
import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from tqdm.auto import tqdm

from .colours import generate_repository_colours
from .exceptions import HTTPError, RemoteRepoNotFoundError, InvalidArgumentError
from .generate_heatmap_data import generate_heatmap_data, push_heatmap_data_to_mongodb
from .limit_languages import limit_languages_for_repository
from .sca_helpers import collect_scantist_sca_data

colorama.init(autoreset=True)
load_dotenv()
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
CONNECTION_STRING = os.environ.get('CONNECTION_STRING')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPOS_DIR = os.path.join(CURRENT_DIR, "tmp")
LOGS_DIR = os.path.join(CURRENT_DIR, "logs")

if not os.path.exists(REPOS_DIR):
    os.mkdir(REPOS_DIR)

if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)


class TqdmLoggingHandler(logging.Handler):
    """
    Custom stream handler to allow the console progress bars from the tqdm package to work alongside python logging.
    """
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        """
        Override of the Handler.emit method. This new method prints the message using the 'write()' function provided
        by tqdm so that the tqdm progress bars still work properly.
        :param record: the LogRecord object from the logging library
        :return: None
        """
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


class HostnameFilter(logging.Filter):
    """
    Custom filter for logging. This filter allows the hostname of the device that is running the pipeline to be added to
    the logging output
    """
    hostname = platform.node()

    def filter(self, record):
        """
        Override of the logging.Filter.filter() method
        :param record: the LogRecord object from the logging package
        :return: "Returns True if the record should be logged, or False otherwise." (from the logging documentation)
        """
        record.hostname = HostnameFilter.hostname
        return True


class RepositoryFilter(logging.Filter):
    """
    Custom filter for logging. This filter allows the repository that is currently being processed to be added to the
    logging output
    """
    def __init__(self, repo_owner, repo_name):
        super().__init__()
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.repo_str = f"{repo_owner}/{repo_name}"

    def filter(self, record):
        """
        Override of the logging.Filter.filter() method
        :param record: the LogRecord object from the logging package
        :return: "Returns True if the record should be logged, or False otherwise." (from the logging documentation)
        """
        record.repository = self.repo_str
        return True


class CustomLogger(logging.Logger):
    """
    Custom Logger class that performs extra actions when an exception is logged. Specifically an exception will trigger
    the log files (if any) to be renamed so that "[ERROR]" is appended to the name of the log file. This is for greater
    readability when looking at the log files from a file system.
    """
    def __init__(self, name):
        super(CustomLogger, self).__init__(name)
        self.exception_has_occurred = False

    def exception(self, msg, *args, exc_info=..., stack_info=..., stacklevel=..., extra=..., **kwargs):
        """
        Override of the exception method of the logging.Logger class. This new method will rename the log files (if any)
        to include "[ERROR]" in the file name for greater visibility.
        """
        if not self.exception_has_occurred:

            file_handlers = [h for h in self.handlers if isinstance(h, logging.FileHandler)]
            for file_handler in file_handlers:
                # get log file name
                base_file = os.path.splitext(file_handler.baseFilename)[0]
                new_file = f"{base_file} [ERROR].log"

                # delete handler
                file_handler.close()
                self.removeHandler(file_handler)

                # rename the log file
                os.rename(file_handler.baseFilename, new_file)

                # create new file handler with new file name
                new_handler = CustomFileHandler(new_file)
                self.addHandler(new_handler)

            self.exception_has_occurred = True

        super(CustomLogger, self).exception(msg)


class CustomFileHandler(logging.FileHandler):
    """
    Wrapper for the logging.FileHandler function to update the filehandler with filtering options and similar
    """
    def __init__(self, filename):
        super().__init__(filename)
        self.addFilter(HostnameFilter())
        file_format = logging.Formatter("%(asctime)s [%(hostname)s] %(funcName)s() %(levelname)s:%(message)s")
        self.setLevel(logging.INFO)
        self.setFormatter(file_format)


def get_current_repo_log_directory(start_datetime):
    """
    Creates the directory to contain the log files for the current run of the pipeline
    :param start_datetime: the date that the current pipeline run began
    :return: the directory (str) to contain the log files
    """
    month_log_dir = os.path.join(LOGS_DIR, start_datetime.strftime("%Y-%m"))
    if not os.path.exists(month_log_dir):
        os.mkdir(month_log_dir)
    current_log_dir = os.path.join(month_log_dir, start_datetime.strftime("%Y-%m-%dT%H-%M-%S%z"))
    if not os.path.exists(current_log_dir):
        os.mkdir(current_log_dir)

    return current_log_dir


def get_logger(repo_owner, repo_name, start_datetime):
    """
    Generates a custom logger object from the python logging package for a particular repository. The logging output is
    redirected to both a log file for the repository and to the terminal. The terminal logging output uses colours to
    help with readability. The log file will be renamed from something like "vuejs-vue.log" to "vuejs-vue [ERROR].log"
    if any exceptions occur when processing that repository.
    :param repo_owner: the owner of the repository, eg. 'facebook'
    :param repo_name: the name of the repository, eg. 'react'
    :param start_datetime: the date that the current pipeline run began
    :return: the custom logger object (logging.Logger)
    """
    logging.setLoggerClass(CustomLogger)

    current_log_dir = get_current_repo_log_directory(start_datetime)

    datetime_str = start_datetime.strftime('%Y-%m-%dT%H-%M-%S%z')
    logger = logging.getLogger(f"{datetime_str}/{repo_owner}/{repo_name}")
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers = []

    # file handler
    file = CustomFileHandler(os.path.join(current_log_dir, f"{repo_owner}-{repo_name}.log"))

    # stream handler
    stream = TqdmLoggingHandler()
    stream.addFilter(HostnameFilter())
    stream.addFilter(RepositoryFilter(repo_owner, repo_name))
    stream_format = logging.Formatter(f"{colorama.Fore.GREEN}%(asctime)s "
                                      f"{colorama.Fore.LIGHTRED_EX}[%(repository)s] "
                                      f"{colorama.Fore.LIGHTMAGENTA_EX}%(funcName)s() "
                                      f"{colorama.Fore.LIGHTCYAN_EX}%(levelname)s: "
                                      f"{colorama.Fore.WHITE}%(message)s")
    stream.setLevel(logging.INFO)
    stream.setFormatter(stream_format)

    logger.addHandler(file)
    logger.addHandler(stream)
    return logger


class Progress(git.RemoteProgress):
    """
    Class for showing progress to the console while a repository is cloning locally
    """

    def __init__(self, logger):
        super().__init__()
        self.logger = logger

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.logger.debug(self._cur_line)


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


def clone_repo(repo_owner, repo_name, logger, print_progress=True):
    """
    Clones a github repository locally
    :param print_progress: True for printing cloning progress to the console, False for no printing
    :param repo_name: the name of the repository. Eg, 'react'
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :param logger: The logger object to use for logging information
    :return: repo: the Repo type from gitPython
    """
    remote_url = f"https://github.com/{repo_owner}/{repo_name}.git"
    repo_path = os.path.join(REPOS_DIR, repo_name)
    repo = git.Repo.clone_from(remote_url, repo_path, progress=Progress(logger) if print_progress else None)

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

    owner_keys = ["login", "avatar_url", "gravatar_id", "html_url", "type"]
    # filtering the json response to only include the keys above
    data["owner_obj"] = dict(zip(owner_keys, [r["owner"][key] for key in owner_keys]))
    if 'organization' in r:
        data["organization_obj"] = dict(zip(owner_keys, [r["organization"][key] for key in owner_keys]))

    keys = ["description", "forks", "forks_count", "language", "stargazers_count", "watchers_count", "watchers", "size",
            "default_branch", "open_issues_count", "open_issues", "topics", "has_issues", "archived", "disabled",
            "visibility", "pushed_at", "created_at", "updated_at", "html_url", "fork", "homepage", "has_projects",
            "has_downloads", "has_wiki", "has_pages", "license", "subscribers_count"]
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


def get_commits_per_author(repo):
    """
    Gets a tally of the number of commits all time and in the last 30 days for each author and returns a dictionary
    structure containing the data
    :param repo: the Repo type from gitPython
    :return: a dictionary with the commit data
    """
    data = {}
    all_time_total = 0
    last_30_days_total = 0
    commit_set = set()
    for ref in repo.references:
        for commit in repo.iter_commits(ref.name):
            # if the commit has already been counted for another branch, ignore it
            if commit.hexsha in commit_set:
                continue
            commit_set.add(commit.hexsha)
            if commit.author.name in data.keys():
                data[commit.author.name]["all_time"] += 1
                all_time_total += 1
            else:
                data[commit.author.name] = {
                    "name": commit.author.name,
                    "all_time": 1,
                    "last_30_days": 0
                }
                all_time_total += 1
            # check if the commit was in the most recent 30 days
            if (datetime.datetime.now(datetime.timezone.utc) - commit.committed_datetime) < datetime.timedelta(
                    days=30):
                data[commit.author.name]["last_30_days"] += 1
                last_30_days_total += 1

    # sort authors by number of commits
    all_time_list = sorted(data.values(), key=lambda x: x["all_time"], reverse=True)
    last_30_days_list = sorted(data.values(), key=lambda x: x["last_30_days"], reverse=True)
    MAX_AUTHORS = 25
    return {
        "all_time": {
            "top_25": all_time_list[:min(MAX_AUTHORS, len(all_time_list))],
            "total": all_time_total
        },
        "last_30_days": {
            "top_25": last_30_days_list[:min(MAX_AUTHORS, len(last_30_days_list))],
            "total": last_30_days_total
        }
    }


def get_monthly_commit_data(repo):
    """
    Gets the total number of commits for each month of a repo and gets total number of contributors per month,
    and returns a dictionary structure containing the data
    :param repo: The Repo type from gitPython
    :return: a dictionary with monthly commit and contributor data
    """
    data = {}
    commit_set = set()
    all_time_total = 0
    for ref in repo.references:

        for commit in repo.iter_commits(ref.name):
            # if the commit has already been counted for another branch, ignore it
            if commit.hexsha in commit_set:
                continue
            commit_set.add(commit.hexsha)
            # print(commit.hexsha)

            commit_date = commit.committed_datetime.strftime('%Y-%m')
            if commit_date in data.keys():
                data[commit_date]["commits"] += 1
                all_time_total += 1
            else:  # For the first commit of a month
                data[commit_date] = {
                    "month": commit_date,
                    "commits": 1,
                    "contributor_count": 1,
                    "contributor_name": {commit.author.name}
                }
            # If the contributor name is unique:
            if commit.author.name not in data[commit_date]["contributor_name"]:
                data[commit_date]["contributor_count"] += 1
                data[commit_date]["contributor_name"].add(commit.author.name)

    monthly_data_list = sorted(data.values(), key=lambda x: x["month"], reverse=True)  # list of dictionary of set
    for i, _ in enumerate(monthly_data_list):
        monthly_data_list[i].pop("contributor_name")

    return {
        "month_data": monthly_data_list
    }


def reduce_releases(releases, max_releases=15):
    """
    Reduces a list of tag names to a shorter list of tag names. The purpose of this function is to identify a subset
    of all the git tags which will be processed by the pipeline, so that the pipeline does not need to process all tags.
    :param max_releases: the maximum number of releases that can be allowed
    :param releases: a list of release/tag names
    :return: a subset of the input list
    """
    if len(releases) < 5:
        return releases

    if max_releases < 2:
        raise InvalidArgumentError('max_releases must be greater than 2')

    # calculate N to aim for less than 30 releases
    n = max(2, math.floor(len(releases) / max_releases - 2))
    if n < 2:
        return releases

    first = releases.pop(0)
    last = releases.pop(len(releases) - 1)
    good_releases = []

    for index, release in enumerate(releases):
        if index % n == 0:
            good_releases.append(release)

    return [first] + good_releases + [last]


def process_repository(repo_str, start_datetime):
    """
    Processes the repository by doing the following:
        - validate the repository input
        - clone the repository (if not currently in the 'tmp' folder
        - retrieve a list of tags/releases for the repository
        - iterate through the tags/releases
        - calculate the LOC data for each tag/release by using a command line tool called 'cloc'
        - push the data to mongodb
    :param repo_str: concatenation of the repository owner and name separated by a '/'. Eg, 'facebook/react'
    :param start_datetime: the date that the pipeline run began
    :return: None
    """
    if not is_valid_repo_name(repo_str):
        tqdm.write("Invalid repository name!")
        return

    repo_owner, repo_name = repo_str.split("/")

    logger = get_logger(repo_owner, repo_name, start_datetime)

    logger.info(f"Running pipeline process for repository: {repo_str}")

    try:
        # get repository metadata from the github API
        logger.info("Retrieving repository metadata from the Github REST API")
        try:
            data = get_repository_metadata(repo_owner, repo_name)
        except RemoteRepoNotFoundError as e:
            logger.exception(str(e))
            return

        repo_path = os.path.join(REPOS_DIR, repo_name)

        # check if repository is already cloned locally
        if check_local_repo_exists(repo_name):
            logger.info("using cached repository")
            repo = git.Repo(repo_path)
        else:
            logger.info("cloning repository...")
            repo = clone_repo(repo_owner, repo_name, logger)

        # get the mongoDB client
        logger.info("connecting to mongodb")
        mongo_client = MongoClient(CONNECTION_STRING, ssl_cert_reqs=ssl.CERT_NONE)

        raise Exception("random exception")

        logger.info("calculating commits per author data")
        data['commits_per_author'] = get_commits_per_author(repo)

        logger.info("calculating commits per month")
        data['commits_per_month'] = get_monthly_commit_data(repo)

        logger.info("Generating heatmap data")
        heatmap_data = generate_heatmap_data(repo_owner, repo_name, repo, mongo_client, logger)

        logger.info("Pushing heatmap data to mongodb")
        push_heatmap_data_to_mongodb(repo_owner, repo_name, heatmap_data, mongo_client)

        # get the tags from the repository
        tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
        logger.info(f"There were {len(tags)} tags found in the repository")

        # adding some tag related information to the repository metadata
        data["num_tags"] = len(tags)
        if len(tags) > 0:
            data["latest_tag"] = tags[-1].name
        else:
            data["latest_tag"] = None

        # reducing the number of tags
        tags = reduce_releases(tags, max_releases=30)
        logger.info(f"number of tags reduced to: {len(tags)}")

        g = git.Git(repo_path)  # initialise git in order to checkout each tag
        tag_loop = tqdm(tags, desc="calculating LOC for each tag")  # tqdm object for displaying the progress bar

        for tag in tag_loop:
            tag_name = tag.name
            tag_loop.set_description(f"processing tag: {tag}")
            tag_loop.refresh()

            logger.info(f"checking out tag: {tag}")
            g.checkout(tag_name, force=True)

            logger.info(f"counting LOC for tag: {tag}")
            # calling the 'cloc' command line tool to count LOC statistics for the repository
            tag_data = call_cloc(repo_path)  # this data can possibly be used later on

            logger.info("pushing to mongodb...")
            push_release_to_mongodb(repo_owner, repo_name, tag, tag_data, mongo_client)

        logger.info("Updating the LOC data to limit the number of languages")
        limit_languages_for_repository(repo_owner, repo_name, mongo_client)

        # push the repository data to mongoDB
        logger.info("Pushing repository data to mongoDB")
        push_repository_to_mongodb(repo_owner, repo_name, data, mongo_client)

        try:
            logger.info("Collecting SCA data")
            collect_scantist_sca_data(REPOS_DIR, repo_path, repo_owner, repo_name, mongo_client, logger)
        except Exception as err:
            logger.exception(err)

        logger.info("Generating dynamic colours for the repository")
        generate_repository_colours(repo_owner, repo_name, mongo_client)

        repo.close()
        time.sleep(2)  # to wait for the previous git related processes to release the repository
        logger.info("deleting local repository...")
        clean_up_repo(repo_name)

    except Exception as e:
        logger.exception(str(e))
