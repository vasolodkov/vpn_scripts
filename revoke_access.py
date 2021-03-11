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
#

import sys
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
import paramiko
import ruamel.yaml as yaml


def delete_session(host):
    get_session = f'get vpn ssl monitor | grep {user_login}'
    print(f'Connection to {host}')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=ssh_user, password=ssh_password)
        stdin, stdout, stderr = client.exec_command(get_session)
        session_id = stdout.readlines()[0].split()[2]
        del_session = f'execute vpn sslvpn del-web {session_id}'
        stdin, stdout, stderr = client.exec_command(del_session)
        print('session deleted')
    except IndexError:
        print(f'No session for {user_login} on {host}')

with open('config.yaml') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

dc = config['dc']
d_admin = config['d_admin']
d_pass = config['d_pass']
ssh_user = config['ssh_user']
ssh_password = config['ssh_password']
base = config['base']
group_to_remove_prefix = config['group_to_remove_prefix']
forti_hosts = config['forti_hosts']

try:
    d_user = sys.argv[1]
except IndexError as err:
    print('Error: ', err)

server = Server(dc, get_info=ALL)
conn = Connection(server, user=d_admin, password=d_pass, auto_bind=True)

if conn.bind():
    search_filter_user = f'(&(objectClass=Person)(sn={d_user}))'
    conn.search(search_base=base,
                search_filter=search_filter_user,
                attributes=['sAMAccountName'. 'cn', 'memberOf'])
    user_cn = conn.entries[-1].cn.values[0]
    user_dn = conn.entries[-1].entry_dn
    user_groups = conn.entries[-1].memberOf
    user_login = conn.entries[-1].sAMAccountName.value
    for i in user_groups:
        if group_to_remove_prefix in i:
            group_to_remove = i
    conn.extend.microsoft.remove_members_from_groups(user_dn,
                                                     group_to_remove)

    for host in forti_hosts:
        try:
            delete_session(host)
        except paramiko.ssh_exception.AuthenticationException:
            print(f'check ssh login and password for {host}')
        except TimeoutError:
            print(f'host {host} is not available')
