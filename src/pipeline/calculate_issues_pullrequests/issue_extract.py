import json
import re
import datetime
from git import Repo
from git.objects import commit
from perceval.backends.core.github import GitHub
from perceval.backends.core.gitlab import GitLab


def save_issue2json(json_fn:str, owner:str, repository:str) -> None:
    repo = GitHub(
        owner=owner, 
        repository=repository, 
        api_token=["***"], # put your github token here
        sleep_for_rate=True)
        
    json_data = {}

    for item in repo.fetch():  #if it is necessary,you need to change the parameter define in github.py
        # if 'pull_request' in item['data']:
        #     kind = 'Pull request'
        # else:
        #     kind = 'Issue'
        if 'pull_request' in item['data']:
            continue
        num = item['data']['number']
        json_data[num] = {}
        json_data[num]['user'] = item['data']['user']['login']
        json_data[num]['created_at'] = item['data']['created_at']  #Change the output by modifying here
        json_data[num]['updated_at'] = item['data']['updated_at']
        json_data[num]['closed_at'] = item['data']['closed_at']
        json_data[num]['state'] = item['data']['state']
        json_data[num]['comments'] = []
        for c in item['data']['comments_data']:
            json_data[num]['comments'].append({'user': c['user']['login'],'created_at': c['created_at']})

    with open(json_fn, 'w') as f:
        json.dump(json_data, f, indent=4)
    print("Saved issues to " + json_fn)

# def save_gitlab_issue2json(json_fn:str, owner:str, repository:str) -> None:
#     repo = GitLab(
#         owner=owner,
#         repository=repository,
#         api_token="xGEyvgGYj6etPSHNgUgt",
#         sleep_for_rate=True)
#     json_data = {}
#
#     for item in repo.fetch():
#         # if 'pull_request' in item['data']:
#         #     kind = 'Pull request'
#         # else:
#         #     kind = 'Issue'
#         if item['data']['type'] != 'ISSUE':
#             print(item['data']['type'])
#             continue
#         num = item['data']['iid']
#         json_data[num] = {}
#         json_data[num]['title'] = item['data']['title']
#         json_data[num]['user'] = item['data']['author']['name']
#         json_data[num]['body'] = item['data']['description']
#         json_data[num]['state'] = item['data']['state']
#         json_data[num]['comments'] = []
#         for c in item['data']['notes_data']:
#             json_data[num]['comments'].append({'user': c['author']['name'], 'body': c['body']})
#
#     with open(json_fn, 'w') as f:
#         json.dump(json_data, f, indent=4)
#     print("Saved issues to " + json_fn)


if __name__ == "__main__":

  owner=['NLPchina+Word2VEC_java','chaoss+wg-risk','michaelliao+learn-python3','lydiahallie+javascript-questions']#item name
  nowtime=datetime.datetime.now().strftime('%Y-%m-%d-%H')
  for i in owner:
     demt=i.split('+')
     username=demt[0]
     projectname=demt[1]
     save_issue2json(
        json_fn='./commit_issue/'+username+'&'+projectname+'&'+'issue'+'&'+nowtime+'.json',
        owner=username,
        repository= projectname
    )


    # NLPchina / Word2VEC_java

    # save_gitlab_issue2json(
    #     json_fn='./commit_issue/libxml2_issue.json',
    #     owner='GNOME',
    #     repository='libxml2'
    # )
