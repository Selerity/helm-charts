"""
(c) Selerity Pty. Ltd. 2022.  All Rights Reserved.
This work is licensed under the Creative Commons Attribution-NonCommercial-NoDerivitives License. To view a copy 
of the license, visit https://creativecommons.org/licenses/by-nc-nd/4.0/
"""

import os
import sys
import requests
import logging

viya_base_url = os.environ.get('VIYA_BASE_URL')
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
consul_token = os.environ.get('CONSUL_TOKEN')
home_dir_path = os.environ.get('HOME_DIR_PATH')
debug_flag = os.environ.get('DEBUG')
user_exceptions = os.environ.get('USER_EXCEPTIONS')
dry_run = os.environ.get('DRY_RUN', '1')

if debug_flag == "1":
    loglevel = logging.DEBUG
else:
    loglevel = logging.INFO

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', stream = sys.stdout, level=loglevel)
log = logging.getLogger()
log.info("Starting execution.")

def oauth_client_exists(consul_token, viya_base_url, client_id):
    # Request OAuth token
    url = f"{viya_base_url}/SASLogon/oauth/clients/consul?callback=false&serviceId={client_id}"
    headers = {'X-Consul-Token': consul_token}
    response = requests.request("POST", url, headers=headers)
    access_token = response.json()['access_token']
    # Get Clients
    url = f"{viya_base_url}/SASLogon/oauth/clients/{client_id}"
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    response = requests.request("HEAD", url, headers=headers)
    if response.status_code == 200:
        return(True)
    else:
        return(False)

def register_oauth_client(consul_token, viya_base_url, client_id, client_secret):
    # Request client registration OAuth token
    url = f"{viya_base_url}/SASLogon/oauth/clients/consul?callback=false&serviceId={client_id}"
    headers = {'X-Consul-Token': consul_token}
    response = requests.request("POST", url, headers=headers)
    access_token = response.json()['access_token']
    # Client Registration
    url = f"{viya_base_url}/SASLogon/oauth/clients"
    payload = {"client_id": client_id, "client_secret": client_secret, "authorized_grant_types": "client_credentials", "scope": "openid *", "authorities": "SASAdministrators"}
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    response = requests.request("POST", url, headers=headers, json=payload)
    if response.status_code == 200:
        return(True)
    else:
        return(False)

def delete_oauth_client(consul_token, viya_base_url, client_id):
    # Request client registration OAuth token
    url = f"{viya_base_url}/SASLogon/oauth/clients/consul?callback=false&serviceId={client_id}"
    headers = {'X-Consul-Token': consul_token}
    response = requests.request("POST", url, headers=headers)
    access_token = response.json()['access_token']
    # Delete Client Registration
    url = f"{viya_base_url}/SASLogon/oauth/clients/{client_id}"
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    response = requests.request("DELETE", url, headers=headers)
    return(response)

def get_token(consul_token, viya_base_url, client_id, client_secret, retry=0):
    # Get token
    url = f"{viya_base_url}/SASLogon/oauth/token"
    payload = {'grant_type': 'client_credentials'}
    headers = {'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.request("POST", url, headers=headers, data=payload, auth=(client_id, client_secret))
    if response.status_code != 200:
        if retry == 0:
            log.info("The OAuth Client has become corrupted. Recreating it...")
            delete_oauth_client(consul_token, viya_base_url, client_id)
            register_oauth_client(consul_token, viya_base_url, client_id, client_secret)
            access_token = get_token(consul_token, viya_base_url, client_id, client_secret, retry=1)
    access_token = response.json()['access_token']
    return(access_token)

def get_uids(viya_base_url, access_token):
    uid = {}
    # Get Users
    url = f"{viya_base_url}/identities/users"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}
    response = requests.request("GET", url, headers=headers)
    users = response.json()["items"]
    for user in users:
        url = f"{viya_base_url}/identities/users/{user['id']}/identifier"
        response = requests.request("GET", url, headers=headers)
        uid[user['id']] = response.json()["uid"]
    return(uid)

def home_dir_builder(consul_token, viya_base_url, client_id, client_secret, home_dir_path, user_exceptions, dry_run):
    access_token = get_token(consul_token, viya_base_url, client_id, client_secret)
    uids = get_uids(viya_base_url, access_token)
    # Get a list of all home dirs
    from pathlib import Path
    import os
    home = Path(home_dir_path)
    home_dirs = {}
    for d in home.iterdir():
        home_dirs[d.name] = d
    # Process list of users found in Viya
    for uid in uids:
        if uid in home_dirs:
            log.info(f"Found a matching home directory for {uid}...")
            if uids[uid] != home_dirs[uid].stat().st_uid:
                log.info(f"uid for {home_dirs[uid]} is different. Directory: {home_dirs[uid].stat().st_uid}, Viya: {uids[uid]}. Changing...")
                if dry_run == '0':
                    try:
                        os.chown(home_dirs[uid], uids[uid], 1001)
                        log.info(f"uid changed on {home_dirs[uid]} to {uids[uid]}")
                    except:
                        log.error(f"Unable to change owner for {home_dirs[uid]}")
                else:
                    log.info("DRY RUN: No action taken.")
            else:
                log.info(f"uid of {home_dirs[uid]} is correct ({uids[uid]})")
        else:
            if uid in user_exceptions:
                log.info(f"Home directory for {uid} doesn't exist, but is being ignored due to exception list")
            else:
                log.info(f"Home directory for {uid} doesn't appear to exist. Creating...")
                if dry_run == '0':
                    try:
                        new_home_dir = Path(home, uid)
                        new_home_dir.mkdir(mode=750)
                        log.info(f"Created home directory for {uid}")
                        try:
                            os.chown(new_home_dir, uids[uid], 1001)
                        except:
                            log.error(f"Unable to change owner for {new_home_dir}")
                    except:
                        log.error(f"Unable to create home directory for {uid}")
                else:
                    log.info("DRY RUN: Action not taken.")

def printVariables(viya_base_url, client_id, client_secret, consul_token, home_dir_path, user_exceptions):
    log.debug(f"VIYA_BASE_URL  : {viya_base_url}")
    log.debug(f"CLIENT_ID      : {client_id}")
    log.debug(f"CLIENT_SECRET  : {client_secret}")
    log.debug(f"CONSUL_TOKEN   : {consul_token}")
    log.debug(f"HOME_DIR_PATH  : {home_dir_path}")
    log.debug(f"USER_EXCEPTIONS: {user_exceptions}")

# Main
if user_exceptions == None:
    user_exceptions = str()
user_exceptions = ''.join(user_exceptions.split()).split(',')

printVariables(viya_base_url, client_id, client_secret, consul_token, home_dir_path, user_exceptions)

if consul_token == None or viya_base_url == None or client_id == None or client_secret == None or home_dir_path == None:
    log.error('Environment variables not set correctly.')
    printVariables(viya_base_url, client_id, client_secret, consul_token, home_dir_path, user_exceptions)
else:
    # Check if our OAuth Client exists or not, and create it if not
    if oauth_client_exists(consul_token, viya_base_url, client_id) == False:
        log.info(f"OAuth client does not exist. Creating...")
        register_oauth_client(consul_token, viya_base_url, client_id, client_secret)
        if oauth_client_exists(consul_token, viya_base_url, client_id) == False:
            log.error(f"Error creating OAuth client {client_id}")
    # Run homedir builder
    home_dir_builder(consul_token, viya_base_url, client_id, client_secret, home_dir_path, user_exceptions, dry_run)
log.info("Ending execution.")