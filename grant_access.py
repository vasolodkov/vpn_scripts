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
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
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
base = config['base']
group_to_remove_prefix = config['group_to_remove_prefix']
url = config['url']

try:
    task_id = sys.argv[1]
except IndexError as err:
    print('Error: ', err)
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

d_user = response.json()['Task']['Field115']

server = Server(dc, get_info=ALL)
conn = Connection(server, user=d_admin, password=d_pass, auto_bind=True)
conn_bind()  # must be True

search_filter_user = f'(&(objectClass=Person) (sn={d_user}))'
conn.search(search_base=base, search_filter=search_filter_user,
            attributes=['sAMAccountName', 'cn', 'memberOf'])
user_cn = conn.entries[-1].cn.values[0]
user_dn = conn.entries[-1].entry_dn
user_groups = conn.entries[-1].memberOf

search_filter_group = f'(&(objectClass=group) (name={vpn_group}))'
conn.search(search_base=base, search_fscope=SUBTREE,
            search_filter=search_filter_group)
group_dn = conn.entries[0].entry_dn

for i in user_groups:
    if group_to_remove_prefix in i:
        group_to_remove = i

try:
    conn.extend.microsoft.remove_members_from_groups(user_dn, group_to_remove)
except NameError:
    print(f'{user_cn} not in vpn group')

conn.extend.microsoft.add_members_to_groups(user_dn, group_dn)

# checking
search_filter_user = f'(&(objectClass=Person) (sn={d_user}))'
conn.search(search_base=base, search_filter=search_filter_user,
            attributes=['sAMAccountName', 'cn', 'memberOf'])
user_groups = conn.entries[-1].memberOf

if group_dn in user_groups:
    print(f'{user_cn} in {vpn_group}')

# create task expenses
data = {'taskid': task_id, 'Minutes': '2',
        'Comments': f'Затрачено времени на заявку {task_id}'}
url_task_expenses = url + 'taskexpenses?taskid='
response = requests.get((url_task_expenses + task_id), headers=headers,
                        auth=HTTPBasicAuth(hd_user, hd_pass),
                        verify=False, data=data)

# set status 'complete'
params = {'include': ['status']}
response = requests.post((url_task + task_id), headers=headers,
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
