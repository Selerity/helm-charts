#!/usr/bin/env python3
import os
import sys
import json
import logging
import subprocess
import base64
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: pip3 install requests")
    sys.exit(1)

def get_k8s_secret(namespace, secret_name, key):
    """Get secret value from Kubernetes"""
    try:
        cmd = f"kubectl get secret {secret_name} -n {namespace} -o jsonpath='{{.data.{key}}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return base64.b64decode(result.stdout).decode('utf-8')
    except Exception as e:
        logging.error(f"Failed to get secret {secret_name}.{key}: {e}")
    return None

def get_k8s_configmap(namespace, configmap_name, key):
    """Get configmap value from Kubernetes"""
    try:
        cmd = f"kubectl get configmap {configmap_name} -n {namespace} -o jsonpath='{{.data.{key}}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
    except Exception as e:
        logging.error(f"Failed to get configmap {configmap_name}.{key}: {e}")
    return None

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    namespace = sys.argv[1] if len(sys.argv) > 1 else "viya"
    viya_base_url = sys.argv[2] if len(sys.argv) > 2 else None
    home_dir_path = sys.argv[3] if len(sys.argv) > 3 else "/home"
    
    # Get Viya secrets from Kubernetes
    consul_token = get_k8s_secret(namespace, "sas-consul-client", "CONSUL_TOKEN")
    logging.info(f"Consul token found: {bool(consul_token)}")
    
    # Configuration
    client_id = "selerity.homedir_builder"
    client_secret = os.urandom(16).hex()  # Generate random secret
    user_exceptions = ["Administrator"]
    dry_run = os.getenv('DRY_RUN', '1') == '1'
    
    if not viya_base_url:
        # Try to get from ingress
        cmd = f"kubectl get ingress -n {namespace} -o jsonpath='{{.items[0].spec.rules[0].host}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            viya_base_url = f"https://{result.stdout.strip()}"
    
    logging.info(f"Viya URL: {viya_base_url}")
    
    if not all([consul_token, viya_base_url]):
        logging.error("Missing required configuration. Usage: script.py <namespace> <viya_url> [home_path]")
        sys.exit(1)
    
    # Get admin token and register OAuth client
    url = f"{viya_base_url}/SASLogon/oauth/clients/consul?callback=false&serviceId={client_id}"
    response = requests.post(url, headers={'X-Consul-Token': consul_token})
    if response.status_code != 200:
        logging.error(f"Failed to get admin token: {response.status_code}")
        sys.exit(1)
    admin_token = response.json()['access_token']
    
    # Check if client exists, delete if it does
    check_url = f"{viya_base_url}/SASLogon/oauth/clients/{client_id}"
    check_response = requests.head(check_url, headers={'Authorization': f'Bearer {admin_token}'})
    if check_response.status_code == 200:
        requests.delete(check_url, headers={'Authorization': f'Bearer {admin_token}'})
    
    # Register new client
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'authorized_grant_types': 'client_credentials',
        'scope': 'openid *',
        'authorities': 'SASAdministrators'
    }
    reg_response = requests.post(f"{viya_base_url}/SASLogon/oauth/clients",
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {admin_token}'},
        json=payload)
    if reg_response.status_code not in [201, 409]:
        logging.error(f"Failed to register client: {reg_response.status_code}")
        sys.exit(1)
    
    # Get OAuth token
    response = requests.post(f"{viya_base_url}/SASLogon/oauth/token",
        data={'grant_type': 'client_credentials'},
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        auth=(client_id, client_secret))
    
    if response.status_code != 200:
        logging.error(f"Failed to get OAuth token: {response.status_code}")
        sys.exit(1)
    
    access_token = response.json()['access_token']
    
    # Get users and UIDs
    response = requests.get(f"{viya_base_url}/identities/users?limit=10000",
        headers={'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'})
    
    logging.info(f"Users API response: {response.status_code}")
    if response.status_code != 200:
        logging.error(f"Failed to get users: {response.status_code} - {response.text}")
        sys.exit(1)
    
    try:
        users_data = response.json()
    except:
        logging.error(f"Invalid JSON response: {response.text[:200]}")
        sys.exit(1)
    
    users = users_data.get('items', [])
    logging.info(f"Processing {len(users)} users...")
    
    uids = {}
    for i, user in enumerate(users):
        if i % 100 == 0:
            logging.info(f"Processed {i}/{len(users)} users")
        uid_response = requests.get(f"{viya_base_url}/identities/users/{user['id']}/identifier",
            headers={'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'})
        try:
            uids[user['id']] = uid_response.json()['uid']
        except:
            continue
    
    logging.info(f"Found UIDs for {len(uids)} users")
    
    # Process home directories
    home_path = Path(home_dir_path)
    existing_dirs = {d.name: d for d in home_path.iterdir() if d.is_dir()}
    
    for user_id, uid in uids.items():
        if user_id in user_exceptions:
            continue
            
        user_home = home_path / user_id
        
        if user_id in existing_dirs:
            current_uid = existing_dirs[user_id].stat().st_uid
            if current_uid != uid:
                logging.info(f"Updating {user_id}: {current_uid} -> {uid}")
                if not dry_run:
                    os.chown(user_home, uid, 1001)
        else:
            logging.info(f"Creating home for {user_id}")
            if not dry_run:
                user_home.mkdir(mode=0o750)
                os.chown(user_home, uid, 1001)

if __name__ == '__main__':
    main()