import subprocess
import json
import requests
from tqdm import tqdm

import secrets

repo_name = "react"
repo_owner = "facebook"

data = {}

# p1 = subprocess.run(f"git clone https://github.com/{repo_owner}/{repo_name}.git", capture_output=True, text=True, cwd="./repositories")

# releases = ["v17.0.2", "v17.0.1", "v17.0.0"]


def get_releases():
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases?per_page=100&page=1"
    res = requests.get(url, auth=("user", secrets.ACCESS_TOKEN))
    releases = res.json()
    while 'next' in res.links.keys():
        res = requests.get(res.links['next']['url'], auth=("user", secrets.ACCESS_TOKEN))
        releases.extend(res.json())
    return releases


releases = get_releases()
print(len(releases))


for release in tqdm(releases, desc="calculating LOC for each release"):
    tag = release["tag_name"]
    print(f"checking out tag: {tag}")
    p2 = subprocess.run(f"git checkout {tag}", cwd=f"./repositories/{repo_name}", capture_output=True)
    if p2.returncode == 0:
        pass
    else:
        print("error")
        break
    print(f"count LOC for tag: {tag}")
    p3 = subprocess.run(f"cloc . --vcs=git --json", cwd=f"./repositories/{repo_name}", capture_output=True)
    if p3.returncode == 0:
        pass
    else:
        print("error")
        break
    data[tag] = json.loads(p3.stdout)

with open('loc_per_release_for_facebook_react.json', 'w') as file:
    file.write(json.dumps(data))
