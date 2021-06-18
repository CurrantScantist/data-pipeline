"""
For simplicity, the pipeline will be written in this file first as a draft without custom timechecking, logs, visualiser, etc
The requests library will be used temporarily but this will likely switch to asyncio + aiohttp later on for efficiency.
"""
import requests
import os
import json


"""
LOOPING THROUHG DATA FOLDER TO GET REPOSITORY NAMES

data folder will have the following structure (for now):
.
+-- data
|   +-- react                                           (repository name without the owner)
|       +-- name.txt                                    (file containing a single line with the fullname of the repository, eg, 'facebook/react')
|       +-- 1                                           (directory for a single release, the name is irrelevant since it will be stored in a .txt file also)
|           +-- release.txt                             (file containing a single line with the full release name, eg, '17.0.2 (March 22, 2021)')
|           +-- **other data from scantist apps**       (folders of manually downloaded data from scantist sca, archtimize, etc)

"""
base = "./data"
to_process = []
data = dict()


for repo in os.listdir('./data'):
    if os.path.isdir(f"{base}/{repo}"):

        repo_name = ""
        with open(f"{base}/{repo}/name.txt", 'r') as name_file:
            repo_name = name_file.readline().strip()

        data[repo_name] = {
            "releases": dict()
        }

        for release in os.listdir(f"{base}/{repo}"):

            if os.path.isdir(f"{base}/{repo}/{release}"):
                release_name = ""
                with open(f"{base}/{repo}/{release}/release.txt", 'r') as release_name_file:
                    release_name = release_name_file.readline().strip()

                print(
                    f"repository name: {repo_name}, release name: {release_name}")

                data[repo_name]["releases"][release_name] = dict()

                to_process.append({
                    "repo": repo,
                    "owner": repo_name.split("/")[0],
                    "release": release_name,
                })


"""
RETRIEVING METADATA

Done:
 - repo name
 - repo owner
 - repo link

 - release created at
 - release published at
 - release id
 - release url (link to the page on github)
 - release description/body

TODO:
 - the api call for a specific release can be changed to only retrieve that release instead of all of them
 https://docs.github.com/en/rest/reference/repos#get-a-release-by-tag-name

"""
for repository in data.keys():
    # get whole repository stats
    owner, repo = repository.split("/")
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}")
    r = r.json()

    # with open('./response.json', 'w') as file:
    #     file.write(json.dumps(r))

    keys = ["description", "forks", "forks_count", "language", "stargazers_count", "watchers_count", "watchers", "size", "default_branch", "open_issues_count", "open_issues",
            "topics", "has_issues", "archived", "disabled", "visibility", "pushed_at", "created_at", "updated_at"]
    for key in keys:
        try:
            data[repository][key] = r[key]
        except KeyError:
            print(f"key '{key}' was not found in the response")

    # get the repository languages
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/languages")
    data[repository]["languages"] = r.json()

for entry in to_process:
    r = requests.get(
        f'https://api.github.com/repos/{entry["owner"]}/{entry["repo"]}/releases')
    r = r.json()

    metadata = dict()

    for release in r:
        if release["name"] == entry["release"]:
            metadata["created_at"] = release["created_at"]
            metadata["tag_name"] = release["tag_name"]
            metadata["published_at"] = release["published_at"]
            metadata["release_id"] = release["id"]
            # the api url is also available
            metadata["release_link"] = release["html_url"]
            metadata["release_description"] = release["body"]

    repo_name = entry["owner"] + '/' + entry["repo"]
    data[repo_name]["releases"][entry["release"]] = metadata

with open('./test.json', 'w') as file:
    file.write(json.dumps(data))
