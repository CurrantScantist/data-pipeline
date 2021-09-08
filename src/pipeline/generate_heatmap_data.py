import json
from datetime import datetime, timedelta, timezone
import os

from perceval.backends.core.github import GitHub
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
ACCESS_TOKEN2 = os.environ.get('ACCESS_TOKEN2')


def date_span(start_date, end_date, delta=timedelta(weeks=1)):
    current_date = start_date
    while current_date < end_date:
        new_date = current_date + delta
        yield current_date, new_date
        current_date = new_date


def issue_is_open_in_week(issue, start_of_week, end_of_week, date_format="%Y-%m-%dT%H:%M:%S%z"):
    if issue["created_at"] is None:
        return False
    open_date = datetime.strptime(issue["created_at"], date_format)
    if open_date < start_of_week:
        if issue["state"] == "open":
            return True
        else:
            closed_date = datetime.strptime(issue["closed_at"], date_format)
            if closed_date > end_of_week:
                return True
    return False


def pull_request_is_modified_in_week(pr, start_of_week, end_of_week, option, date_format="%Y-%m-%dT%H:%M:%S%z"):
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
    return start_of_week < commit.committed_datetime < end_of_week


def retrieve_issues(repo, num_weeks):
    json_data = {}

    current_date = datetime.now(timezone.utc)
    cut_off_date = datetime.now(timezone.utc) - timedelta(weeks=num_weeks)

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

    tqdm.write("Issue data extracted to JSON")
    return json_data


def retrieve_pull_requests(repo, num_weeks):
    json_data = {}

    current_date = datetime.now(timezone.utc)
    cut_off_date = datetime.now(timezone.utc) - timedelta(weeks=num_weeks)

    for item in tqdm(
            repo.fetch(from_date=cut_off_date, to_date=current_date, category="pull_request"),
            desc="fetching repository data"):

        if 'pull_request' in item['data']:
            print("the random if statement is actually triggering")
            with open('random_data.json', 'w') as file:
                json.dump(item, file, indent=4)
            continue

        num = item['data']['number']
        json_data[num] = {}
        json_data[num]['title'] = item['data']['title']
        json_data[num]['user'] = item['data']['user']['login']
        json_data[num]['state'] = item['data']['state']
        json_data[num]['created_at'] = item['data']['created_at']
        json_data[num]['closed_at'] = item['data']['closed_at']
        json_data[num]['submitted_at'] = []
        if item['data']['reviews_data']:
            for c in item['data']['reviews_data']:
                if json_data[num]['submitted_at']:
                    continue
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
                json_data[num]['reviewer'].append({'user': c['user_data']['login']})

    tqdm.write("Pull Request data extracted to JSON")
    return json_data


def retrieve_commits(repo_instance):
    commit_list = []
    hexshas = set()
    for ref in tqdm(repo_instance.references, desc="extracting commits from branches"):
        for commit in repo_instance.iter_commits(ref.name):
            if commit.hexsha in hexshas:
                continue
            commit_list.append(commit)
            hexshas.add(commit.hexsha)
    return commit_list


def generate_heatmap_data(repo_owner, repo_name, repo_instance, dimensions=(19, 8)):
    num_weeks = dimensions[0] * dimensions[1]
    start_date = datetime.now(timezone.utc) - timedelta(weeks=num_weeks)
    end_date = datetime.now(timezone.utc)

    results = []

    tokens = [ACCESS_TOKEN, ACCESS_TOKEN2]
    tokens = [token for token in tokens if token is not None]

    repo = GitHub(
        owner=repo_owner,
        repository=repo_name,
        api_token=tokens,
        sleep_for_rate=True,
        sleep_time=300
    )

    issues = retrieve_issues(repo, num_weeks)
    pull_requests = retrieve_pull_requests(repo, num_weeks)
    commits = retrieve_commits(repo_instance)

    for start_of_week, end_of_week in date_span(start_date, end_date):
        obj = {
            "week": num_weeks - len(results),
            "start": start_of_week.strftime('%Y-%m-%d-%H'),
            "end": end_of_week.strftime('%Y-%m-%d-%H'),
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


# def get_open_issues_per_week(issues):
#     start_date = datetime.now(timezone.utc) - timedelta(weeks=80)
#     end_date = datetime.now(timezone.utc)
#
#     date_format = "%Y-%m-%dT%H:%M:%S%z"
#     results = []
#
#     for start_of_week, end_of_week in date_span(start_date, end_date):
#         num_open_issues = 0
#         for issue in issues.values():
#             if issue["created_at"] is None:
#                 continue
#             open_date = datetime.strptime(issue["created_at"], date_format)
#             if open_date < start_of_week:
#                 if issue["state"] == "open":
#                     num_open_issues += 1
#                 else:
#                     closed_date = datetime.strptime(issue["closed_at"], date_format)
#                     if closed_date > end_of_week:
#                         num_open_issues += 1
#
#         index = 80 - len(results)
#
#         results.append({
#             "week": 80 - index,
#             "coordinates": [index % 4, (index//4) % 20],
#             "start": start_of_week.strftime('%Y-%m-%d-%H'),
#             "end": end_of_week.strftime('%Y-%m-%d-%H'),
#             "open_issues": num_open_issues
#         })
#     return results


# TODO: get the number of pull requests created per week, closed per week and merged per week

# TODO: get the number of commits per week


if __name__ == '__main__':

    file_name = r"C:\Users\jackw\Documents\GitHub\data-pipeline\heatmap_data_for_socketio_socket.io-client-cpp.json"

    with open(file_name, 'r') as file:
        data = json.load(file)

    new_data_array = []

    for obj in data["data"]:
        obj["week"] = obj["week"] - 1
        obj["coords"] = {
            "x": obj["week"]//8,
            "y": obj["week"] % 8,
        }
        new_data_array.append(obj)

    new_data = {
        "data": new_data_array
    }

    with open("new_file.json", 'w') as file:
        json.dump(new_data, file, indent=4)

