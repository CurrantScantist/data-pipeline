import os

os.environ["GIT_PYTHON_REFRESH"] = "quiet"
import datetime
import json
from perceval.backends.core.github import GitHub


# Get the data about pullrequest
def save_pull_requests2json(json_fn: str, owner: str, repository: str) -> None:
    repo = GitHub(
        owner=owner,
        repository=repository,
        api_token=[""],  # put your github token here
        sleep_for_rate=True)
    json_data = {}

    for item in repo.fetch(
            category="pull_request"):  # if it is necessary,you need to change the parameter define in github.py
        # if 'pull_request' in item['data']:
        #     kind = 'Pull request'
        # else:
        #     kind = 'Issue'
        if 'pull_request' in item['data']:
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

    with open(json_fn, 'w') as f:
        json.dump(json_data, f, indent=4)
    print("Saved pull_requests to " + json_fn)


# def save_gitlab_pull_request2json(json_fn: str, owner: str, repository: str) -> None:
#         repo = GitLab(
#             owner=owner,
#             repository=repository,
#             api_token="xGEyvgGYj6etPSHNgUgt",
#             sleep_for_rate=True)
#         json_data = {}
#
#         for item in repo.fetch():
#             # if 'pull_request' in item['data']:
#             #     kind = 'Pull request'
#             # else:
#             #     kind = 'Issue'
#             if item['data']['type'] != 'ISSUE':
#                 print(item['data']['type'])
#                 continue
#             num = item['data']['iid']
#             json_data[num] = {}
#             json_data[num]['title'] = item['data']['title']
#             json_data[num]['user'] = item['data']['author']['name']
#             json_data[num]['body'] = item['data']['description']
#             json_data[num]['state'] = item['data']['state']
#             json_data[num]['comments'] = []
#             for c in item['data']['notes_data']:
#                 json_data[num]['comments'].append({'user': c['author']['name'], 'body': c['body']})
#
#         with open(json_fn, 'w') as f:
#             json.dump(json_data, f, indent=4)
#             print("Saved issues to " + json_fn)

if __name__ == "__main__":

    owner = ['NLPchina+Word2VEC_java', 'lvandeve+lodepng', 'socketio+socket.io-client-cpp']  # item name
    nowtime = datetime.datetime.now().strftime('%Y-%m-%d-%H')
    for i in owner:
        demt = i.split('+')
        username = demt[0]
        projectname = demt[1]
        save_pull_requests2json(
            json_fn='./commit_issue/' + username + '&' + projectname + '&' + 'pq' + '&' + nowtime + '.json',
            owner=username,
            repository=projectname
        )
        # NLPchina / Word2VEC_java

        # save_gitlab_issue2json(
        #     json_fn='./commit_issue/libxml2_issue.json',
        #     owner='GNOME',
        #     repository='libxml2'
        # )
