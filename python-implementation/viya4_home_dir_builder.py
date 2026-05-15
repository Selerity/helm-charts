#!/usr/bin/env python3
"""
Pure Python implementation of Viya 4 Home Directory Builder
Replaces the Kubernetes CronJob with a standalone Python script
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests library is required. Install with: pip3 install requests")
    sys.exit(1)


class Viya4HomeDirBuilder:
    def __init__(self, config_file: str = None, **kwargs):
        self.config = self._load_config(config_file, **kwargs)
        self._setup_logging()
        
    def _load_config(self, config_file: str, **kwargs) -> Dict:
        """Load configuration from file or command line arguments"""
        config = {}
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        
        # Override with command line arguments
        config.update({k: v for k, v in kwargs.items() if v is not None})
        
        # Set defaults
        defaults = {
            'debug': False,
            'dry_run': True,
            'user_exceptions': [],
            'home_dir_mode': 0o750,
            'home_dir_gid': 1001
        }
        
        for key, value in defaults.items():
            config.setdefault(key, value)
            
        return config
    
    def _setup_logging(self):
        """Setup logging configuration"""
        level = logging.DEBUG if self.config.get('debug') else logging.INFO
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(message)s',
            stream=sys.stdout,
            level=level
        )
        self.log = logging.getLogger()
    
    def _validate_config(self) -> bool:
        """Validate required configuration parameters"""
        required = ['viya_base_url', 'client_id', 'client_secret', 'consul_token', 'home_dir_path']
        missing = [key for key in required if not self.config.get(key)]
        
        if missing:
            self.log.error(f"Missing required configuration: {', '.join(missing)}")
            return False
        return True
    
    def oauth_client_exists(self) -> bool:
        """Check if OAuth client exists"""
        url = f"{self.config['viya_base_url']}/SASLogon/oauth/clients/consul"
        params = {'callback': 'false', 'serviceId': self.config['client_id']}
        headers = {'X-Consul-Token': self.config['consul_token']}
        
        try:
            response = requests.post(url, headers=headers, params=params)
            access_token = response.json()['access_token']
            
            url = f"{self.config['viya_base_url']}/SASLogon/oauth/clients/{self.config['client_id']}"
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.head(url, headers=headers)
            
            return response.status_code == 200
        except Exception as e:
            self.log.error(f"Error checking OAuth client: {e}")
            return False
    
    def register_oauth_client(self) -> bool:
        """Register OAuth client"""
        url = f"{self.config['viya_base_url']}/SASLogon/oauth/clients/consul"
        params = {'callback': 'false', 'serviceId': self.config['client_id']}
        headers = {'X-Consul-Token': self.config['consul_token']}
        
        try:
            response = requests.post(url, headers=headers, params=params)
            access_token = response.json()['access_token']
            
            url = f"{self.config['viya_base_url']}/SASLogon/oauth/clients"
            payload = {
                'client_id': self.config['client_id'],
                'client_secret': self.config['client_secret'],
                'authorized_grant_types': 'client_credentials',
                'scope': 'openid *',
                'authorities': 'SASAdministrators'
            }
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
            response = requests.post(url, headers=headers, json=payload)
            
            return response.status_code == 201
        except Exception as e:
            self.log.error(f"Error registering OAuth client: {e}")
            return False
    
    def get_access_token(self) -> Optional[str]:
        """Get OAuth access token"""
        url = f"{self.config['viya_base_url']}/SASLogon/oauth/token"
        payload = {'grant_type': 'client_credentials'}
        headers = {'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                data=payload, 
                auth=(self.config['client_id'], self.config['client_secret'])
            )
            
            if response.status_code == 200:
                return response.json()['access_token']
            else:
                self.log.error(f"Failed to get access token: {response.status_code}")
                return None
        except Exception as e:
            self.log.error(f"Error getting access token: {e}")
            return None
    
    def get_user_uids(self, access_token: str) -> Dict[str, int]:
        """Get user UIDs from Viya"""
        uids = {}
        url = f"{self.config['viya_base_url']}/identities/users?limit=10000"
        headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
        
        try:
            response = requests.get(url, headers=headers)
            users = response.json().get('items', [])
            
            for user in users:
                user_id = user['id']
                uid_url = f"{self.config['viya_base_url']}/identities/users/{user_id}/identifier"
                uid_response = requests.get(uid_url, headers=headers)
                
                try:
                    uids[user_id] = uid_response.json()['uid']
                except Exception:
                    self.log.error(f"Unable to get UID for user {user_id}")
                    
        except Exception as e:
            self.log.error(f"Error getting user UIDs: {e}")
            
        return uids
    
    def process_home_directories(self, uids: Dict[str, int]):
        """Process home directories - create/update ownership"""
        home_path = Path(self.config['home_dir_path'])
        user_exceptions = self.config.get('user_exceptions', [])
        
        if not home_path.exists():
            self.log.error(f"Home directory path does not exist: {home_path}")
            return
        
        # Get existing home directories
        existing_dirs = {d.name: d for d in home_path.iterdir() if d.is_dir()}
        
        for user_id, uid in uids.items():
            if user_id in user_exceptions:
                self.log.info(f"Skipping user {user_id} (in exceptions list)")
                continue
                
            user_home = home_path / user_id
            
            if user_id in existing_dirs:
                # Check and update ownership
                current_uid = existing_dirs[user_id].stat().st_uid
                if current_uid != uid:
                    self.log.info(f"Updating ownership for {user_id}: {current_uid} -> {uid}")
                    if not self.config['dry_run']:
                        try:
                            os.chown(user_home, uid, self.config['home_dir_gid'])
                            self.log.info(f"Updated ownership for {user_home}")
                        except Exception as e:
                            self.log.error(f"Failed to update ownership for {user_home}: {e}")
                    else:
                        self.log.info("DRY RUN: No action taken")
                else:
                    self.log.info(f"Ownership correct for {user_id} (UID: {uid})")
            else:
                # Create new home directory
                self.log.info(f"Creating home directory for {user_id}")
                if not self.config['dry_run']:
                    try:
                        user_home.mkdir(mode=self.config['home_dir_mode'])
                        os.chown(user_home, uid, self.config['home_dir_gid'])
                        self.log.info(f"Created home directory: {user_home}")
                    except Exception as e:
                        self.log.error(f"Failed to create home directory for {user_id}: {e}")
                else:
                    self.log.info("DRY RUN: No action taken")
    
    def run(self):
        """Main execution method"""
        self.log.info("Starting Viya 4 Home Directory Builder")
        
        if not self._validate_config():
            return False
        
        # Ensure OAuth client exists
        if not self.oauth_client_exists():
            self.log.info("OAuth client does not exist. Creating...")
            if not self.register_oauth_client():
                self.log.error("Failed to register OAuth client")
                return False
        
        # Get access token
        access_token = self.get_access_token()
        if not access_token:
            self.log.error("Failed to get access token")
            return False
        
        # Get user UIDs
        uids = self.get_user_uids(access_token)
        if not uids:
            self.log.warning("No users found")
            return True
        
        self.log.info(f"Found {len(uids)} users")
        
        # Process home directories
        self.process_home_directories(uids)
        
        self.log.info("Execution completed")
        return True


def main():
    parser = argparse.ArgumentParser(description='Viya 4 Home Directory Builder')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--viya-base-url', help='Viya base URL')
    parser.add_argument('--client-id', help='OAuth client ID')
    parser.add_argument('--client-secret', help='OAuth client secret')
    parser.add_argument('--consul-token', help='Consul token')
    parser.add_argument('--home-dir-path', help='Home directory path')
    parser.add_argument('--user-exceptions', nargs='*', help='Users to exclude')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run')
    parser.add_argument('--no-dry-run', action='store_true', help='Disable dry run')
    
    args = parser.parse_args()
    
    # Convert args to config dict
    config = {k.replace('_', '-'): v for k, v in vars(args).items() if v is not None}
    
    # Handle dry_run logic
    if args.no_dry_run:
        config['dry_run'] = False
    elif args.dry_run:
        config['dry_run'] = True
    
    builder = Viya4HomeDirBuilder(args.config, **config)
    success = builder.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()