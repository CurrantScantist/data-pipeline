import json
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from perceval.backends.core.github import GitHub
from tqdm import tqdm
from bson.codec_options import CodecOptions

load_dotenv()
ACCESS_TOKENS = [os.environ.get('ACCESS_TOKEN')]
for i in range(6):
    env_token = os.environ.get(f"ACCESS_TOKEN{i}")
    if env_token is not None:
        ACCESS_TOKENS.append(env_token)


def date_span(start_date, end_date, delta=timedelta(weeks=1)):
    """
    Creates a generator object that iterates week by week from a start date to an end date.
    :param start_date: the start datetime object
    :param end_date: the end datetime object
    :param delta: the timedelta increment that added each iteration
    :return: a generator object that iterates week by week from start to end date.
    """
    current_date = start_date
    while current_date < end_date:
        new_date = current_date + delta
        yield current_date, new_date
        current_date = new_date


def issue_is_open_in_week(issue, start_of_week, end_of_week, date_format="%Y-%m-%dT%H:%M:%S%z"):
    """
    Checks if an issue is open for the whole duration of a date range.
    :param issue: the issue object
    :param start_of_week: the start datetime object
    :param end_of_week: the end datetime object
    :param date_format: the datetime string format in the issue object
    :return: boolean for whether the issue was open for the whole duration of the date range.
    """
    if issue["created_at"] is None:
        return False
    open_date = datetime.strptime(issue["created_at"], date_format)
    if open_date < start_of_week:
        if issue["state"] == "open":
            return True
        closed_date = datetime.strptime(issue["closed_at"], date_format)
        if closed_date > end_of_week:
            return True
    return False


def pull_request_is_modified_in_week(pr, start_of_week, end_of_week, option, date_format="%Y-%m-%dT%H:%M:%S%z"):
    """
    Checks if a pull request was either created, closed, or merged, in between two dates.
    :param pr: the pull request object
    :param start_of_week: the start datetime object
    :param end_of_week: the end datetime object
    :param option: the option for which action to check. Must be one of ['created', 'closed', 'merged']
    :param date_format: the date_format for the pull request object
    :return: boolean for whether the pull request had the specified action performed within the date range
    """
    options = {
        "created": "created_at",
        "closed": "closed_at",
        "merged": "merged_at"
    }
    date_option = options[option]
    if pr[date_option] is None:
        return False
    action_date = datetime.strptime(pr[date_option], date_format)
    if start_of_week < action_date < end_of_week:
        return True
    return False


def commit_is_in_week(commit, start_of_week, end_of_week):
    """
    Checks if a commit was created in a specific date range
    :param commit: the commit object
    :param start_of_week: the start datetime object
    :param end_of_week: the end datetime object
    :return: boolean for whether the commit date is between the start_of_week and end_of_week dates
    """
    return start_of_week < commit.committed_datetime < end_of_week


def retrieve_issues(repo_owner, repo_name, repo, num_weeks, client, logger, date_format="%Y-%m-%dT%H:%M:%S%z"):
    """
    Retrieves a repository's issues from the github API. Due the the very slow process of retrieving issues from the
    github API, any issues that are extracted will be stored in mongodb so that they do not need to be retrieved from
    the github API in following pipeline runs. This function checks if there are any issues (within the relevant time
    period) already in mongodb and then retrieves issues from the github API using the appropriate cut off date based
    on the most recently updated issue found in mongodb.
    :param repo_owner: the owner of the repository
    :param repo_name: the name of the repository
    :param repo: the repo object (from perceval)
    :param num_weeks: the number of weeks from the current date to retrieve issues from
    :param client: the MongoClient object from PyMongo
    :param logger: The logger object to use for logging information
    :param date_format: the date format to use when representing dates as strings
    :return: the json object with the issue data for the last num_weeks weeks
    """
    db = client["test_db"]
    issue_collection = db["issues"].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.utc))
    json_data = {}

    current_date = datetime.now(timezone.utc)
    cut_off_date = datetime.now(timezone.utc) - timedelta(weeks=num_weeks)

    most_recent_update = None

    # retrieve any issues already stored in the database
    for db_issue in issue_collection.find({"name": repo_name, "owner": repo_owner,
                                           "updated_at": {"$gt": cut_off_date}},
                                          {"_id": 0, "name": 0, "owner": 0}):
        if most_recent_update is None:
            most_recent_update = db_issue["updated_at"]
        else:
            if db_issue["updated_at"] > most_recent_update:
                most_recent_update = db_issue["updated_at"]

        for date_str in ["created_at", "closed_at", "updated_at"]:
            if db_issue[date_str] is not None:
                if db_issue[date_str] != "None":
                    db_issue[date_str] = db_issue[date_str].strftime(date_format)
        json_data[db_issue["id"]] = db_issue

    logger.info(f"There were {len(json_data.keys())} relevant issues already found in the database")

    # get the new cut off date (if there were issues already in the database)
    if most_recent_update is not None:
        cut_off_date = most_recent_update

    logger.info(f"Finding github issues since {cut_off_date.strftime(date_format)}")

    for item in tqdm(
            repo.fetch(from_date=cut_off_date, to_date=current_date, category="issue"),
            desc="fetching issue data"):

        num = item['data']['number']
        json_data[num] = {}
        json_data[num]['user'] = item['data']['user']['login']
        json_data[num]['created_at'] = item['data']['created_at']
        json_data[num]['updated_at'] = item['data']['updated_at']
        json_data[num]['closed_at'] = item['data']['closed_at']
        json_data[num]['state'] = item['data']['state']
        json_data[num]['comments'] = []
        for c in item['data']['comments_data']:
            json_data[num]['comments'].append({'user': c['user']['login'], 'created_at': c['created_at']})

        search = {
            "name": repo_name,
            "owner": repo_owner,
            "id": num
        }

        issue_to_insert = json_data[num].copy()
        for date_str in ["created_at", "closed_at", "updated_at"]:
            if issue_to_insert[date_str] is not None:
                if issue_to_insert[date_str] != "None":
                    issue_to_insert[date_str] = datetime.strptime(issue_to_insert[date_str], date_format)

        issue_collection.update_one(search, {"$set": issue_to_insert}, upsert=True)

    logger.info("Issue data successfully retrieved")
    return json_data


def retrieve_pull_requests(repo_owner, repo_name, repo, num_weeks, client, logger, date_format="%Y-%m-%dT%H:%M:%S%z"):
    """
    Retrieves a repository's pull requests from the github API. Due the the very slow process of retrieving pull
    requests from the github API, any pull requests that are extracted will be stored in mongodb so that they do not
    need to be retrieved from the github API in following pipeline runs. This function checks if there are any pull
    requests (within the relevant time period) already in mongodb and then retrieves pull requests from the github API
    using the appropriate cut off date based on the most recently updated pull request found in mongodb.
    :param repo_owner: the owner of the repository
    :param repo_name: the name of the repository
    :param repo: the repo object (from perceval)
    :param num_weeks: the number of weeks from the current date to retrieve issues from
    :param client: the MongoClient object from PyMongo
    :param logger: The logger object to use for logging information
    :param date_format: the date format to use when representing dates as strings
    :return: the json object with the pull request data for the last num_weeks weeks
    """
    db = client["test_db"]
    pr_collection = db["pull_requests"].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.utc))
    json_data = {}

    current_date = datetime.now(timezone.utc)
    cut_off_date = datetime.now(timezone.utc) - timedelta(weeks=num_weeks)

    most_recent_update = None

    # retrieve any pull requests already stored in the database
    for db_pull_request in pr_collection.find({"name": repo_name, "owner": repo_owner,
                                               "updated_at": {"$gt": cut_off_date}},
                                              {"_id": 0, "name": 0, "owner": 0}):
        if most_recent_update is None:
            most_recent_update = db_pull_request["updated_at"]
        else:
            if db_pull_request["updated_at"] > most_recent_update:
                most_recent_update = db_pull_request["updated_at"]

        for date_str in ["created_at", "closed_at", "updated_at", "merged_at"]:
            if db_pull_request[date_str] is not None:
                if db_pull_request[date_str] != "None":
                    db_pull_request[date_str] = db_pull_request[date_str].strftime(date_format)
        json_data[db_pull_request["id"]] = db_pull_request

    logger.info(f"There were {len(json_data.keys())} relevant pull requests already found in the database")

    # get the new cut off date (if there were pull requests already in the database)
    if most_recent_update is not None:
        cut_off_date = most_recent_update

    logger.info(f"Finding github pull requests since {cut_off_date.strftime(date_format)}")

    for item in tqdm(
            repo.fetch(from_date=cut_off_date, to_date=current_date, category="pull_request"),
            desc="fetching pull request data"):

        if 'pull_request' in item['data']:
            continue

        num = str(item['data']['number'])
        json_data[num] = {}
        json_data[num]['title'] = item['data']['title']
        json_data[num]['user'] = item['data']['user']['login']
        json_data[num]['state'] = item['data']['state']
        json_data[num]['created_at'] = item['data']['created_at']
        json_data[num]['closed_at'] = item['data']['closed_at']
        json_data[num]['updated_at'] = item['data']['updated_at']
        json_data[num]['submitted_at'] = []
        if item['data']['reviews_data']:
            for c in item['data']['reviews_data']:
                if json_data[num]['submitted_at']:
                    continue
                if c['user_data']:
                    if c['user_data']['login'] != json_data[num]['user']:
                        json_data[num]['submitted_at'] = c['submitted_at']
        json_data[num]['merged'] = item['data']['merged']
        json_data[num]['merged_at'] = item['data']['merged_at']
        json_data[num]['comments_num'] = item['data']['comments']
        json_data[num]['approve_state'] = []
        if item['data']['reviews_data']:
            json_data[num]['approve_state'] = 'approve'
        else:
            json_data[num]['approve_state'] = 'not approve'
        json_data[num]['review_times'] = item['data']['review_comments']
        json_data[num]['reviewer'] = []
        if item['data']['reviews_data']:
            for c in item['data']['reviews_data']:
                if c['user_data']:
                    json_data[num]['reviewer'].append({'user': c['user_data']['login']})

        search = {
            "name": repo_name,
            "owner": repo_owner,
            "id": num
        }

        # add the pull request data to the database
        pr_to_insert = json_data[num].copy()
        for date_str in ["created_at", "closed_at", "updated_at", "merged_at"]:
            if pr_to_insert[date_str] is not None:
                if pr_to_insert[date_str] != "None":
                    pr_to_insert[date_str] = datetime.strptime(pr_to_insert[date_str], date_format)

        pr_collection.update_one(search, {"$set": pr_to_insert}, upsert=True)

    logger.info("Pull Request data successfully retrieved")
    return json_data


def retrieve_commits(repo_instance):
    """
    Retrieves a list of unique commit objects from a Repo object
    :param repo_instance: the Repo object
    :return: a list of unique commits
    """
    commit_list = []
    hexshas = set()
    for ref in tqdm(repo_instance.references, desc="extracting commits from branches"):
        for commit in repo_instance.iter_commits(ref.name):
            if commit.hexsha in hexshas:
                continue
            commit_list.append(commit)
            hexshas.add(commit.hexsha)
    return commit_list


def generate_heatmap_data(repo_owner, repo_name, repo_instance, mongo_client, logger, dimensions=(19, 8)):
    """
    Generates the heatmap data. The data includes metrics for issues, pull requests and commit frequency.
    :param repo_owner: the owner of the repository
    :param repo_name: the name of the repository
    :param repo_instance: the local git Repo object
    :param mongo_client: the MongoClient object from PyMongo
    :param logger: The logger object to use for logging information
    :param dimensions: the dimensions of the heatmap to generate (width, height)
    :return: an array containing the necessary data for the heatmap
    """
    num_weeks = dimensions[0] * dimensions[1]
    start_date = datetime.now(timezone.utc) - timedelta(weeks=num_weeks)
    end_date = datetime.now(timezone.utc)

    results = []

    tokens = ACCESS_TOKENS
    tokens = [token for token in tokens if token is not None]

    repo = GitHub(
        owner=repo_owner,
        repository=repo_name,
        api_token=tokens,
        sleep_for_rate=True,
        sleep_time=300
    )

    issues = retrieve_issues(repo_owner, repo_name, repo, num_weeks, mongo_client, logger)
    pull_requests = retrieve_pull_requests(repo_owner, repo_name, repo, num_weeks, mongo_client, logger)
    commits = retrieve_commits(repo_instance)

    for start_of_week, end_of_week in date_span(start_date, end_date):
        index = num_weeks - len(results) - 1
        obj = {
            "week": index,
            "start": start_of_week.strftime('%Y-%m-%d-%H'),
            "end": end_of_week.strftime('%Y-%m-%d-%H'),
            "coords": {
                "x": dimensions[0] - (index // dimensions[1]) - 1,
                "y": index % dimensions[1]
            },
            "issues": {
                "open": 0
            },
            "pull_requests": {
                "created": 0,
                "merged": 0,
                "closed": 0,
            },
            "commits": {
                "created": 0
            }
        }

        # check issues
        for issue in issues.values():
            if issue_is_open_in_week(issue, start_of_week, end_of_week):
                obj["issues"]["open"] += 1

        # check pull requests
        for pr in pull_requests.values():
            for option in ["created", "merged", "closed"]:
                if pull_request_is_modified_in_week(pr, start_of_week, end_of_week, option):
                    obj["pull_requests"][option] += 1

        # check commits
        for commit in commits:
            if commit_is_in_week(commit, start_of_week, end_of_week):
                obj["commits"]["created"] += 1

        results.append(obj)

    return results[::-1]


def push_heatmap_data_to_mongodb(repo_owner, repo_name, data, client):
    """
    Pushes the repository heatmap data to the mongoDB database
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :param repo_name: the name of the repository. Eg, 'react'
    :param data: the heatmap for the repository (list of dicts)
    :param client: the MongoDB client
    :return: None
    """
    db = client['test_db']
    repo_collection = db['repositories']

    search_dict = {
        "name": repo_name,
        "owner": repo_owner
    }
    repo_collection.update_one(search_dict, {'$set': {'heatmap_data': data}}, upsert=True)
