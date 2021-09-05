import datetime
import json
from collections import Counter


# 函数名称√
# 在每个函数前注释该函数的对象：项目/issue√
# 在每个函数前注释该函数的输入输出√


# The number of created issues per month(object:item)
# input:json.path
# output:the number of new issues per month(as list)
def issues_created_permonth(json_fn: str):
    f = open(json_fn, 'r')
    data = json.load(f)
    res = []
    for num in data:
        created_at = data[num]['created_at']  # get data from jsonfiles
        if created_at == None: continue  # judge state
        temp = created_at.split('T')
        m = temp[0].split('-')  # split into year-month-day
        res.append(m[0] + m[1])  # store into the list
    result = Counter(res)
    list = result.most_common(len(result))  # counter change into list
    order_result = sorted(list, key=(lambda x: [x[0]]))  # sorted list
    return (order_result)


# The number of updated issues per month(object:item)
# input:json.path
# output:the number of updated issues per month(as list)
def issues_updated_permonth(json_fn: str):
    f = open(json_fn, 'r')
    data = json.load(f)
    res = []
    for num in data:
        updated_at = data[num]['updated_at']  # get data from jsonfiles
        if updated_at == None: continue  # judge state
        temp = updated_at.split('T')
        m = temp[0].split('-')  # split into year-month-day
        res.append(m[0] + m[1])  # store into the list
    result = Counter(res)
    list = result.most_common(len(result))  # counter change into list
    order_result = sorted(list, key=(lambda x: [x[0]]))  # sorted list
    return (order_result)


# The number of closed issues per month(object:item)
# input:json.path
# output:the number of closed issues per month(as list)
def issues_closed_permonth(json_fn: str):
    f = open(json_fn, 'r')
    data = json.load(f)
    res = []
    for num in data:
        closed_at = data[num]['closed_at']  # get data from jsonfiles
        if closed_at == None: continue  # judge state
        temp = closed_at.split('T')
        m = temp[0].split('-')  # split into year-month-day
        res.append(m[0] + m[1])  # store into the list
    result = Counter(res)
    list = result.most_common(len(result))  # counter change into list
    order_result = sorted(list, key=(lambda x: [x[0]]))  # sorted list
    return (order_result)


# How long have open issues been left open?(object:issues)
# input:json.path
# output:duration of each issue(as list)
def issue_unresolved_duration(json_fn: str):
    delaytime = []
    numberlist = []
    res = []
    f = open(json_fn, 'r')
    data = json.load(f)
    for num in data:
        created_at = data[num]['created_at']
        closed_at = data[num]['closed_at']
        if closed_at == None:
            temp = created_at.split('T')
            res.append(temp[0])
            number = str(num)
            numberlist.append(number)
    numbers = list(map(int, numberlist))
    for i in res:
        dt1 = datetime.datetime.strptime(i, '%Y-%m-%d')
        today = datetime.datetime.today()
        dt2 = datetime.datetime(today.year, today.month, today.day)
        delay = str(dt2 - dt1)
        delay_temp = delay.split(',')
        delaytime.append(delay_temp[0])
    duration = list(zip(numbers, delaytime))
    order_duration = sorted(duration, key=(lambda x: [x[0]]))  # sorted list
    return (order_duration)


# How long does it take for another contributor to respond(object:issues)
# input:json.path
# output:duration of each issue(as list)
def issue_beresponded_duration(json_fn: str):
    f = open(json_fn, 'r')
    data = json.load(f)
    numberlist = []
    value = []
    for num in data:
        user = data[num]['user']
        comments = data[num]['comments']
        created_at = data[num]['created_at']
        temp = created_at.split('T')
        t = temp[1].split('Z')
        number = str(num)
        numberlist.append(number)  # get the id of issue
        if comments == []:
            value.append('null')
        for c in comments:
            comments_user = c['user']
            comments_time = c['created_at']
            if user == comments_user:
                value.append('null')
                continue
            memp = comments_time.split('T')
            m = memp[1].split('Z')
            dt1 = datetime.datetime.strptime(temp[0] + ' ' + t[0], '%Y-%m-%d %H:%M:%S')
            dt2 = datetime.datetime.strptime(memp[0] + ' ' + m[0], '%Y-%m-%d %H:%M:%S')
            value.append(str(dt2 - dt1))
            break
    numbers = list(map(int, numberlist))
    duration = list(zip(numbers, value))
    order_duration = sorted(duration, key=(lambda x: [x[0]]))
    return (order_duration)  # 输出数组（id+返回值：时间/null）


# How long will it take to solve the issue(object:issues)
# input:json.path
# output:time to close(as list)
def issue_closed_howtime(json_fn: str):
    f = open(json_fn, 'r')
    data = json.load(f)
    numberlist = []
    value = []
    for num in data:
        created_at = data[num]['created_at']
        closed_at = data[num]['closed_at']
        number = str(num)
        numberlist.append(number)  # get the id of issue
        if closed_at == None:
            value.append('null')
            continue
        temp = created_at.split('T')
        t = temp[1].split('Z')
        memp = closed_at.split('T')
        m = memp[1].split('Z')
        dt1 = datetime.datetime.strptime(temp[0] + ' ' + t[0], '%Y-%m-%d %H:%M:%S')
        dt2 = datetime.datetime.strptime(memp[0] + ' ' + m[0], '%Y-%m-%d %H:%M:%S')
        value.append(str(dt2 - dt1))  # 数组（id+解决：时间/null）
    numbers = list(map(int, numberlist))
    time_to_close = list(zip(numbers, value))
    order = sorted(time_to_close, key=(lambda x: [x[0]]))
    return (order)


# average time to solve issus(object:item)
# input:json.path
# output:average time(as list)
def issue_closed_avg(json_sn: str):
    i = 0
    sum = 0
    f = open(json_fn, 'r')
    data = json.load(f)
    for num in data:
        created_at = data[num]['created_at']
        closed_at = data[num]['closed_at']
        if closed_at == None:
            continue
        temp = created_at.split('T')
        t = temp[1].split('Z')
        memp = closed_at.split('T')
        m = memp[1].split('Z')
        dt1 = datetime.datetime.strptime(temp[0] + ' ' + t[0], '%Y-%m-%d %H:%M:%S')
        dt2 = datetime.datetime.strptime(memp[0] + ' ' + m[0], '%Y-%m-%d %H:%M:%S')
        i = i + 1
        issue_closed_time = dt2 - dt1
        sum = issue_closed_time.seconds + sum
    avg = int(sum / i / 3600)
    return (avg)


if __name__ == "__main__":
    json_fn = 'michaelliao&learn-python3&issue&2021-09-05-17.json'  # json file name

    data = {
        "issues_created_permonth": issues_created_permonth(json_fn),
        "issues_updated_permonth": issues_updated_permonth(json_fn),
        "issues_closed_permonth": issues_closed_permonth(json_fn),
        "issue_unresolved_duration": issue_unresolved_duration(json_fn),
        "issue_beresponded_duration": issue_beresponded_duration(json_fn),
        "issue_closed_howtime": issue_closed_howtime(json_fn),
        "issue_closed_avg": issue_closed_avg(json_fn)
    }

    with open('results.json', 'w') as file:
        json.dump(data, file, indent=4)
