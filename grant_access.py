#!/usr/bin/env python3

#
# create file config.yaml with similar parameters
#
# 'dc': 'dc.local'
# 'd_admin': 'admin'
# 'd_pass': 'password'
# 'hd_user': 'user'
# 'hd_pass': 'password2'
# 'ssh_user': 'user2'
# 'ssh_password': 'password3'
# 'base': 'dc=mydomain,dc=local'
# 'group_to_remove_prefix': 'mygroup'
# 'url': 'https://helpdesk.domail.local/api/'
#

import sys
import requests
from requests.auth import HTTPBasicAuth
from pyad import pyad
import ruamel.yaml as yaml

with open('config.yaml') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

dc = config['dc']
d_admin = config['d_admin']
d_pass = config['d_pass']
hd_user = config['hd_user']
hd_pass = config['hd_pass']
url = config['url']

try:
    d_user = sys.argv[1]
    task_id = sys.argv[2]
except IndexError as err:
    print('Error: ', err)
    d_user = input('type full username: ')
    task_id = input('type task id: ')

url_task_life_time = url + 'tasklifetime/?taskid='

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 \
Safari/537.36'}

params = {'include': ['comments']}
response = requests.get((url_task_lifetime + task_id), headers=headers,
                        auth=HTTPBasicAuth(hd_user, hd_pass),
                        verify=False, params=params)

if response.status_code:
    for time in response.json()['TaskLifetimes']:
        if type(time.get('Comments')) is str and \
            ('vpn' in time.get('Comments') or
             'VPN' in time.get('Comments')):
            for element in time.get('Comments').split():
                if 'vpn' in element or 'VPN' in element:
                    vpn_group - element.strip(',')
else:
    print(response.status_code)

# get current status
url_task = url + 'task/'
params = {'include': ['status']}
response = requests.get((url_task + task_id), headers=headers,
                        auth=HTTPBasicAuth(hd_user, hd_pass),
                        verify=False, params=params)
print('current status is ', response.json()['Statuses'][0]['Id'])

# set status 'in progress'
if response.json()['Statuses'][0]['Id'] is not 27:
    data = {'taskid': task_id, 'Id': '27',
            'Name': 'В процессе'}
    response = requests.get((url_task + task_id), headers=headers,
                            auth=HTTPBasicAuth(hd_user, hd_pass),
                            verify=False, params=params, data=data)
elif response.json()['Statuses'][0]['Id'] is 27:
    print('Task is in progress')

pyad.set_defaults(ldap_server=dc, username=d_admin, password=d_pass)

try:
    user = pyad.aduser.ADUser.from_cn(d_user)
except:
    print(f'no user {d_user}')
    d_user = input('type full username')

try:
    group = pyad.adgroup.ADGroup.from_cn(vpn_group)
except:
    print(f'no vpn group {vpn_group}')
    vpn_group = input('type vpn group')

# get groups of user and remove user from VPN_RA_* groups
for i in user.get_memberOfs():
    if 'VPN_RA' in i.CN:
        print('remove from group ', i.CN)
        user.remove_from_group(i)

# user.add_to_group(vpn_group)
group.add_members([user])

# check: get user again
user = pyad.aduser.ADUser.from_cn(d_user)
for i in user.get_memberOfs():
    if 'VPN_RA' in i.CN:
        print('user added to ', i.CN)

# create task expenses
data = {'taskid': task_id, 'Minutes': '2',
        'Comments': f'Затрачено времени на заявку {task_id}'}
url_task_expenses = url + 'taskexpenses?taskid='
response = requests.get((url_task_expenses + task_id), headers=headers,
                        auth=HTTPBasicAuth(hd_user, hd_pass),
                        verify=False, data=data)

# set status 'complete'
params = {'include': ['status']}
response = requests.get((url_task + task_id), headers=headers,
                        auth=HTTPBasicAuth(hd_user, hd_pass),
                        verify=False, params=params)

if response.json()['Statuses'][0]['Id'] is not 29:
    data = {'taskid': task_id, 'Id': '29',
            'Name': 'Выполнена', 'IsFixed': 'True'}
    response = requests.get((url_task + task_id), headers=headers,
                            auth=HTTPBasicAuth(hd_user, hd_pass),
                            verify=False, params=params, data=data)
elif response.json()['Statuses'][0]['Id'] is 29:
    print('Task complete')
