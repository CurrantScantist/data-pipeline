import json
from dateutil.parser import parse
from collections import Counter
from numpy import *
import datetime


# The number of new pullrequest per month
# object:project
# input:json.path
# output:The number of new pullrequest per month
def pullrequest_created_permounth(json_fn:str):
    f = open(json_fn,'r')
    json_data = json.load(f)
    datelist = []
    for num in json_data:
        created_at = json_data[num]['created_at']
        year, month, date = created_at.split('-')
        year_month = year + '-' + month
        datelist.append(year_month)
    group_result = Counter(datelist)
    list = group_result.most_common(len(group_result))  # counter change into list
    order_result = sorted(list, key=(lambda x: [x[0]]))  # sorted list
    return (order_result)


# The number of running pullrequest
# object:project
# input:json.path
# output:The number of ongoing pullrequest
def running_pullrequest_num(json_fn:str):
    f = open(json_fn, 'r')
    json_data = json.load(f)
    statelist = []
    for num in json_data:
        state = json_data[num]['state']
        if state == 'open':
            statelist.append(state)
    state_result = Counter(statelist)
    return (state_result)


# The number of pullrequest opened and closed per user per month
# object:project
# input:json.path
# output:The number of pullrequest opened and closed per user per month
def user_open_close_permonth(json_fn:str):
    f = open(json_fn, 'r')
    json_data = json.load(f)
    userlist = []
    statelist = []
    datelist = []
    for num in json_data:
        userlist.append(json_data[num]['user'])
        created_at = json_data[num]['created_at']
        year, month, date = created_at.split('-')
        year_month = year + '-' + month
        datelist.append(year_month)
        statelist.append(json_data[num]['state'])
    user_state_list = list(zip(datelist, userlist, statelist ))
    user_state_result = Counter(user_state_list)
    list1 = user_state_result.most_common(len(user_state_list))
    order_result = sorted(list1, key=(lambda x: [x[0]]))  # sorted list
    return (order_result)   #(year-month,someone,open/close,num)


# Active developer-user per month
# object:project
# input:json.path,year-month
#output:active user
def active_user(json_fn:str,y_m:str):   # y_m:xxxx-xx
    f = open(json_fn, 'r')
    json_data = json.load(f)
    datelist = []
    userlist = []
    aclist = []
    for num in json_data:
        created_at = json_data[num]['created_at']
        year, month, date = created_at.split('-')
        year_month = year + '-' + month
        if year_month == y_m:
            datelist.append(year_month)
            userlist.append(json_data[num]['user'])
    a = len(datelist)
    b = len(set(userlist))
    if a != 0:
        avg = a/b
    for i in userlist:
        if userlist.count(i)>avg:
            aclist.append(i)
    result = set(aclist)
    if result:
        return (result)
    else:
        return None


# Active developer-reviewer per month
# object:project
# input:json.path,year-month
#output:active reviewer
def active_reviewer(json_fn:str,y_m):   # y_m:xxxx-xx
    f = open(json_fn, 'r')
    json_data = json.load(f)
    datelist = []
    userlist = []
    aclist = []
    for num in json_data:
        submitted_at = json_data[num]['submitted_at']
        if submitted_at:
            year, month, date = submitted_at.split('-')
            year_month = year + '-' + month
            if year_month == y_m:
                datelist.append(year_month)
                for c in json_data[num]['reviewer']:
                    userlist.append(c['user'])
    a = len(userlist)
    b = len(set(userlist))
    if a != 0:
        avg = a/b
    for i in userlist:
        if userlist.count(i)>avg:
            aclist.append(i)
    result = set(aclist)
    if result:
        return (result)
    else:
        return None


# A list of overloaded users per month
# object:project
# input:json.path,year-month
# output:overloaded users
def overloaded_user(json_fn:str,y_m):
    f = open(json_fn, 'r')
    json_data = json.load(f)
    datelist = []
    userlist = []
    aclist = []
    for num in json_data:
        created_at = json_data[num]['created_at']
        year, month, date = created_at.split('-')
        year_month = year + '-' + month
        if year_month == y_m:
            datelist.append(year_month)
            userlist.append(json_data[num]['user'])
    for i in userlist:
        if userlist.count(i) >= 20:
            aclist.append(i)
    result = set(aclist)
    if result:
        return (result)
    else:
        return None

# A list of overloaded reviewers per month
# object:project
# input:json.path,year-month
# output:overloaded reviewers
def overloaded_reviewer(json_fn: str, y_m):  # y_m:xxxx-xx
        f = open(json_fn, 'r')
        json_data = json.load(f)
        datelist = []
        userlist = []
        aclist = []
        for num in json_data:
            submitted_at = json_data[num]['submitted_at']
            if submitted_at:
                year, month, date = submitted_at.split('-')
                year_month = year + '-' + month
                if year_month == y_m:
                    datelist.append(year_month)
                    for c in json_data[num]['reviewer']:
                        userlist.append(c['user'])
        for i in userlist:
            if userlist.count(i) >= 20:
                aclist.append(i)
        result = set(aclist)
        if result:
            return (result)
        else:
            return None


# The number of long running pullrequests
# object:project
# input:json.path
# output:The number of long running pullrequests
def long_running_pr(json_fn:str):
    f = open(json_fn, 'r')
    json_data = json.load(f)
    close_datelist = []
    create_datelist = []
    # Find two time difference: time2-time1
    def get_timediff(time1, time2):
        a = parse(time1)
        b = parse(time2)
        timediff = (b - a).days
        return timediff
    for num in json_data:
        if json_data[num]['closed_at'] == None:
            close_at = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            close_at = json_data[num]['closed_at']
        close_datelist.append(close_at)
        created_at = json_data[num]['created_at']
        create_datelist.append(created_at)
    timediff_list = list(map(lambda x: get_timediff(x[0], x[1]), zip(create_datelist, close_datelist)))
    a = 0
    for i in timediff_list:
        if i > 3:
            a = a + 1
    result = a
    return (result)


# Average loss time per pull request phase
# object:pellrequest
# input:json.path
# output:Average loss time
def avg_loss_time(json_fn:str):
    i = 0
    sum = 0
    f = open(json_fn, 'r')
    json_data = json.load(f)
    for num in json_data:
        created_at = json_data[num]['created_at']
        closed_at = json_data[num]['closed_at']
        if closed_at == None:
            continue
        temp = created_at.split('T')
        t = temp[1].split('Z')
        memp = closed_at.split('T')
        m = memp[1].split('Z')
        dt1 = datetime.datetime.strptime(temp[0] + ' ' + t[0], '%Y-%m-%d %H:%M:%S')
        dt2 = datetime.datetime.strptime(memp[0] + ' ' + m[0], '%Y-%m-%d %H:%M:%S')
        i = i + 1
        loss_time = dt2 - dt1
        sum = loss_time.seconds + sum
    result = int(sum / i / 3600)
    return (result)


# The number of pullrequests that were merged without approval
# object:project
# input:json.path
# output:The number of pullrequests that were merged without approval
def unapproved_merged_pr(json_fn:str):
    f = open(json_fn, 'r')
    json_data = json.load(f)
    np_merged = []
    for num in json_data:
        approve_state = json_data[num]['approve_state']
        merge_state = json_data[num]['merged']
        if approve_state == 'not approve' and merge_state == True:
            np_merged.append(num)
    result = len(np_merged)
    return (result)


# The number of times the pullrequest went back and forth between the author and the reviewer
# object:pullrequest
# input:json.path
# output:The number of times
def user_reviewer_times(json_fn:str):
    f = open(json_fn, 'r')
    json_data = json.load(f)
    numberlist = []
    review_times = []
    for num in json_data:
        number = str(num)
        numberlist.append(number)
        review_times.append(json_data[num]['review_times'])
    numbers = list(map(int, numberlist))
    r = list(zip(numbers, review_times))
    result = sorted(r, key=(lambda x: [x[0]]))
    return (result)


# Whether too many reviewers pull requests
# object:pullrequest
# input:json.path
# output:The number of reviewers / no
def whether_many_reviewers(json_fn:str):
    f = open(json_fn, 'r')
    json_data = json.load(f)
    answerlist = []
    numberlist = []
    for num in json_data:
        number = str(num)
        numberlist.append(number)
        reviewer_num = len(json_data[num]['reviewer'])
        if reviewer_num > 3:
            answer = reviewer_num
        else:
            answer = 'no'
        answerlist.append(answer)
    numbers = list(map(int, numberlist))
    r = list(zip(numbers, answerlist))
    result = sorted(r, key=(lambda x: [x[0]]))
    return (result)


# The number of comments of pullrequest
# object:pullrequest
# input:json.path
# output:The number of comments
def comments_num(json_fn:str):
    f = open(json_fn, 'r')
    json_data = json.load(f)
    numlist = []
    numberlist = []
    for num in json_data:
        number = str(num)
        numberlist.append(number)
        numlist.append(json_data[num]['comments_num'])
    numbers = list(map(int, numberlist))
    r = list(zip(numbers, numlist))
    result = sorted(r, key=(lambda x: [x[0]]))
    return (result)


# What is the duration of the review cycle
# object:pullrequest
# input:json.path
# output:The duration of the review cycle
def review_cycle(json_fn:str):
    f = open(json_fn, 'r')
    json_data = json.load(f)
    timedifflist = []
    numberlist = []
    for num in json_data:
        submitted_at = json_data[num]['submitted_at']
        merged_at = json_data[num]['merged_at']
        number = str(num)
        numberlist.append(number)
        if json_data[num]['approve_state'] == 'approve' and json_data[num]['merged_at']:
            temp = submitted_at.split('T')
            t = temp[1].split('Z')
            memp = merged_at.split('T')
            m = memp[1].split('Z')
            dt1 = datetime.datetime.strptime(temp[0] + ' ' + t[0], '%Y-%m-%d %H:%M:%S')
            dt2 = datetime.datetime.strptime(memp[0] + ' ' + m[0], '%Y-%m-%d %H:%M:%S')
            timediff = str(dt2 - dt1)
            timedifflist.append(timediff)
        else:
            timedifflist.append('no review')
    numbers = list(map(int, numberlist))
    r = list(zip(numbers, timedifflist))
    result = sorted(r, key=(lambda x: [x[0]]))
    return (result)


# How long does it take between creation and first review?
# object:pullrequest
# input:json.path
# output:The time between creation and first review
def create2review_time(json_fn:str):
    f = open(json_fn, 'r')
    json_data = json.load(f)
    timedifflist = []
    numberlist = []
    for num in json_data:
        submitted_at = json_data[num]['submitted_at']
        created_at = json_data[num]['created_at']
        number = str(num)
        numberlist.append(number)
        if json_data[num]['submitted_at']:
            temp = submitted_at.split('T')
            t = temp[1].split('Z')
            memp = created_at.split('T')
            m = memp[1].split('Z')
            dt1 = datetime.datetime.strptime(temp[0] + ' ' + t[0],'%Y-%m-%d %H:%M:%S')
            dt2 = datetime.datetime.strptime(memp[0] + ' ' + m[0], '%Y-%m-%d %H:%M:%S')
            timediff = str(dt1 - dt2)
            timedifflist.append(timediff)
        else:
            timedifflist.append('no review')
    numbers = list(map(int, numberlist))
    r = list(zip(numbers, timedifflist))
    result = sorted(r, key=(lambda x: [x[0]]))
    return (result)


if __name__ == "__main__":
    json_fn = './commit_issue/****.json'  #json file name
   # y_m = '2020-06'
    result = running_pullrequest_num(json_fn)
    print(result)