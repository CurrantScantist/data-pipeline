import os

from pymongo import MongoClient
import ssl
from colour import Color
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
CONNECTION_STRING = os.environ.get('CONNECTION_STRING')


def hash_string(key):
    p = 97
    m = 359
    res = 0
    for index, character in enumerate(key):
        res += ((ord(character) - 96) * p) % m
        res = max(res, 0)
    return res % m


def get_colour_from_string(key, saturation=0.65, lightness=0.5):
    hue = hash_string(key.lower())
    colour = Color(hsl=(hue / 360, saturation, lightness))
    return colour.hex


# def get_colour_triad(key, saturation=0.65, lightness=0.5):
#     hue1 = hash_string(key)
#     hue2 = (hue1 + 120) % 360
#     hue3 = (hue1 - 120) % 360
#     colour1 = Color(hsl=(hue1 / 360, saturation, lightness))
#     colour2 = Color(hsl=(hue2 / 360, saturation, lightness))
#     colour3 = Color(hsl=(hue3 / 360, saturation, lightness))
#     return colour1.hex, colour2.hex, colour3.hex


def update_colours_for_current_data():
    client = MongoClient(CONNECTION_STRING, ssl_cert_reqs=ssl.CERT_NONE)
    db = client['test_db']
    repo_collection = db['repositories']
    releases_collection = db['releases']

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
        repo_str = f"{repo['owner']}/{repo['name']}"
        new_data = {"repo_colour": get_colour_triad(repo_str), "language_colours": {},
                    "topic_colours": [get_colour_from_string(topic) for topic in repo['topics']]}

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
        search_dict = {"name": repo["name"], "owner": repo["owner"]}
        repo_languages = set()

        for release in releases_collection.find(search_dict):
            repo_languages.update(release['LOC'].keys())
        if "SUM" in repo_languages:
            repo_languages.remove("SUM")
        for language in list(repo_languages):
            new_data["language_colours"][language] = get_colour_from_string(language)

        repo_collection.update_one(search_dict, {"$set": new_data})


if __name__ == '__main__':
    update_colours_for_current_data()