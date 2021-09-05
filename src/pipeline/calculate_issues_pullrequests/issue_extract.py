import datetime
import json
import os

from perceval.backends.core.github import GitHub
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')


def save_issues_to_json(json_fn: str, owner: str, repository: str) -> None:
    repo = GitHub(
        owner=owner,
        repository=repository,
        api_token=[ACCESS_TOKEN],
        sleep_for_rate=True,
        sleep_time=300
    )

    json_data = {}

    current_date = datetime.datetime.now(datetime.timezone.utc)
    cut_off_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(weeks=80)

    for item in tqdm(
            repo.fetch(from_date=cut_off_date, to_date=current_date, category="issue"),
            desc="fetching repository data"):

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

    with open(json_fn, 'w') as f:
        json.dump(json_data, f, indent=4)

    tqdm.write("Issue data extracted to JSON")


if __name__ == "__main__":
    repositories = ['michaelliao/learn-python3']
    today = datetime.datetime.now().strftime('%Y-%m-%d-%H')

    for repo_str in repositories:
        owner, repo = repo_str.split("/")

        save_issues_to_json(
            json_fn=owner + '&' + repo + '&' + 'issue' + '&' + today + '.json',
            owner=owner,
            repository=repo
        )
