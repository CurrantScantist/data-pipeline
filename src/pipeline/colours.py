import os

from pymongo import MongoClient
import ssl
from colour import Color
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
CONNECTION_STRING = os.environ.get('CONNECTION_STRING')


def hash_string(key, p=97, m=359):
    """
    Function to hash a string using the universal hash function with the specified parameters.
    :param key: the string to hash
    :param p: prime number
    :param m: the modulus value
    :return: the hashed result
    """
    res = 0
    for index, character in enumerate(key):
        res += ((ord(character) - 96) * p) % m
        res = max(res, 0)
    return res % m


def get_colour_from_string(key, saturation=0.65, lightness=0.5):
    """
    Function to take a string and return a hex representation of a colour for it. The hash of the string determines the
    hue and generates the colour in the HSL colour space.
    :param key: the string key
    :param saturation: the saturation value of the colour
    :param lightness: the lightness value of the colour
    :return: hex string for the colour
    """
    hue = hash_string(key.lower())
    colour = Color(hsl=(hue / 360, saturation, lightness))
    return colour.hex


def generate_repository_colours(repo_owner, repo_name, mongo_client, repo=None):
    """
    Function to generate the dynamic colours for a repository and push this data to mongodb
    :param repo_owner: the owner of the repository
    :param repo_name: the name of the repository
    :param mongo_client: the MongoClient object from PyMongo
    :param repo: the repository data object from the database if available (optional)
    :return: None
    """
    db = mongo_client["test_db"]
    repo_collection = db['repositories']
    releases_collection = db['releases']

    search_dict = {"name": repo_name, "owner": repo_owner}
    if repo is None:
        projection = {
            "_id": 0,
            "name": 1,
            "owner": 1,
            "languages": 1,
            "topics": 1,
            "nodelink_data": 1,
            "license": 1
        }
        repo = repo_collection.find_one(search_dict, projection)

    repo_str = f"{repo_owner}/{repo_name}"
    new_data = {"repo_colour": get_colour_from_string(repo_str), "language_colours": {},
                "topic_colours": dict([(topic, get_colour_from_string(topic)) for topic in repo['topics']])}

    license_colours = {}

    # update the licenses
    if "license" in repo.keys():
        license_name = repo["license"]["name"]
        license_colours[license_name] = get_colour_from_string(license_name)

    if "nodelink_data" in repo.keys():
        licenses = [obj["name"] for obj in repo["nodelink_data"]["categories"]]
        for license_name in licenses:
            license_colours[license_name] = get_colour_from_string(license_name)

    new_data["license_colours"] = license_colours

    # calculate the colours for languages
    repo_languages = set()

    for release in releases_collection.find(search_dict):
        repo_languages.update(release['LOC'].keys())
    if "SUM" in repo_languages:
        repo_languages.remove("SUM")
    for language in list(repo_languages):
        new_data["language_colours"][language] = get_colour_from_string(language)

    repo_collection.update_one(search_dict, {"$set": new_data})


def update_colours_for_current_data():
    """
    Function to call generate_repository_colours() for every repository currently in mongodb. This can be used to
    quickly update the colour configuration without running the pipeline.
    :return: None
    """
    client = MongoClient(CONNECTION_STRING, ssl_cert_reqs=ssl.CERT_NONE)
    db = client['test_db']
    repo_collection = db['repositories']

    projection = {
        "_id": 0,
        "name": 1,
        "owner": 1,
        "languages": 1,
        "topics": 1,
        "nodelink_data": 1,
        "license": 1
    }
    for repo in tqdm(repo_collection.find({}, projection), desc="updating repository colours"):
        generate_repository_colours(repo["owner"], repo["name"], client, repo=repo)


if __name__ == '__main__':
    update_colours_for_current_data()
