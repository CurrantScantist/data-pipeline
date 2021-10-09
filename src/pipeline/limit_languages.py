from pymongo import MongoClient
from dotenv import load_dotenv
import os
import ssl
from operator import itemgetter
from tqdm import tqdm
import time

load_dotenv()
CONNECTION_STRING = os.environ.get("CONNECTION_STRING")


def limit_languages_for_repository(repo_owner, repo_name, mongo_client, limit=12):
    """
    Function for limiting the number of different languages in the lOC data for each release
    :param repo_owner: the owner of the repository
    :param repo_name: the name of the repository
    :param mongo_client: the MongoCLient object from PyMongo
    :param limit: the maximum number of different languages to include in the LOC data
    :return: None
    """
    db = mongo_client["test_db"]
    release_collection = db["releases"]

    search_string = {
        "name": repo_name,
        "owner": repo_owner
    }

    languages = {}

    for release in release_collection.find(search_string):
        for language in release["LOC"].keys():
            if language not in languages:
                languages[language] = release["LOC"][language]["code"]
            else:
                languages[language] += release["LOC"][language]["code"]

    languages = sorted(languages.items(), key=itemgetter(1), reverse=True)
    keys = [language[0] for language in languages]

    top_keys = keys[:limit]

    for release in release_collection.find(search_string):
        new_data = {"Other": {
            "nFiles": 0,
            "blank": 0,
            "comment": 0,
            "code": 0
        }}
        for language in release["LOC"].keys():
            if language in top_keys:
                new_data[language] = release["LOC"][language]
            else:
                for loc_type in ["nFiles", "blank", "comment", "code"]:
                    new_data["Other"][loc_type] += release["LOC"][language][loc_type]

        for language in top_keys:
            if language not in new_data.keys():
                new_data[language] = {"nFiles": 0, "blank": 0, "comment": 0, "code": 0}

        # validate the new data
        correct_sum = release["LOC"]["SUM"]
        new_sum = {
            "nFiles": 0,
            "blank": 0,
            "comment": 0,
            "code": 0
        }

        for key in new_data.keys():
            if key == "SUM":
                continue
            for option in ["nFiles", "blank", "comment", "code"]:
                new_sum[option] += new_data[key][option]

        assert new_sum == correct_sum, f"Invalid sum of LOC for {repo_owner}/{repo_name} tag: {release['tag_name']}"

        release_search = {
            "name": repo_name,
            "owner": repo_owner,
            "tag_name": release["tag_name"]
        }

        release_collection.update_one(release_search, {"$set": {"LOC_limited": new_data}})


def limit_languages_for_current_data():
    """
    Function for calling limit_languages_for_repository for each repository currently in the database
    :return: None
    """
    client = MongoClient(CONNECTION_STRING, ssl_cert_reqs=ssl.CERT_NONE)
    db = client["test_db"]
    repo_collection = db["repositories"]

    projection = {
        "name": 1,
        "owner": 1
    }

    for repo in tqdm(repo_collection.find({}, projection), desc="Updating LOC data for repositories"):
        limit_languages_for_repository(repo["owner"], repo["name"], client)


if __name__ == '__main__':
    limit_languages_for_current_data()
