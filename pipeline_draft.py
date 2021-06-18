"""
For simplicity, the pipeline will be written in this file first as a draft without custom timechecking, logs, visualiser, etc
The requests library will be used temporarily but this will likely switch to asyncio + aiohttp later on for efficiency.
"""
import requests
import os


"""
LOOPING THROUHG DATA FOLDER TO GET REPOSITORY NAMES
"""
base = "./data"
for repo in os.listdir('./data'):
    if os.path.isdir(f"{base}/{repo}"):

        repo_name = ""
        with open(f"{base}/{repo}/name.txt", 'r') as name_file:
            repo_name = name_file.readline().strip()

        for release in os.listdir(f"{base}/{repo}"):
            
            if os.path.isdir(f"{base}/{repo}/{release}"):
                release_name = ""
                with open(f"{base}/{repo}/{release}/release.txt", 'r') as release_name_file:
                    release_name = release_name_file.readline().strip()

                print(f"repository name: {repo_name}, release name: {release_name}")




"""
READING METADATA
"""