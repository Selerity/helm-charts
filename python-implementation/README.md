# Viya 4 Home Directory Builder - Pure Python Implementation

This is a pure Python implementation of the Viya 4 Home Directory Builder that replaces the Kubernetes Helm chart for environments where Docker images cannot be pulled from the internet.

## Overview

The original Helm chart runs as a Kubernetes CronJob using a Python Docker image. This implementation runs directly on a Linux server with Python 3 installed, eliminating the need for Docker or Kubernetes.

## Features

- **No Docker Required**: Runs directly with Python 3
- **Configuration File Support**: JSON-based configuration
- **Command Line Interface**: Full CLI with all original options
- **Cron Integration**: Includes cron wrapper script
- **Dry Run Mode**: Safe testing before making changes
- **Comprehensive Logging**: Debug and info level logging

## Requirements

- Python 3.6+
- `requests` library
- Access to SAS Viya 4 environment
- Appropriate file system permissions for home directory management

## Installation

1. Copy the implementation files to your Linux server:
   ```bash
   scp -r python-implementation/ user@server:/opt/viya4-home-dir-builder/
   ```

2. Install Python dependencies:
   ```bash
   cd /opt/viya4-home-dir-builder
   pip3 install -r requirements.txt
   ```

3. Make scripts executable:
   ```bash
   chmod +x viya4_home_dir_builder.py run_cron.sh
   ```

## Configuration

### Method 1: Configuration File

Edit `config.json` with your environment settings:

```json
{
  "viya_base_url": "https://your-viya-server.com",
  "client_id": "selerity.homedir_builder",
  "client_secret": "your-client-secret",
  "consul_token": "your-consul-token",
  "home_dir_path": "/home",
  "user_exceptions": ["Administrator"],
  "debug": false,
  "dry_run": true
}
```

### Method 2: Command Line Arguments

```bash
./viya4_home_dir_builder.py \
  --viya-base-url https://your-viya-server.com \
  --client-id selerity.homedir_builder \
  --client-secret your-client-secret \
  --consul-token your-consul-token \
  --home-dir-path /home \
  --user-exceptions Administrator \
  --no-dry-run
```

## Usage

### Manual Execution

Run once with dry-run (safe mode):
```bash
./viya4_home_dir_builder.py --config config.json
```

Run with actual changes:
```bash
./viya4_home_dir_builder.py --config config.json --no-dry-run
```

### Scheduled Execution (Cron)

1. Edit the cron wrapper script paths if needed:
   ```bash
   nano run_cron.sh
   ```

2. Add to crontab (runs every 15 minutes like original):
   ```bash
   crontab -e
   # Add this line:
   0,15,30,45 * * * * /opt/viya4-home-dir-builder/run_cron.sh
   ```

## Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `viya_base_url` | Base URL of SAS Viya environment | Required |
| `client_id` | OAuth client ID | Required |
| `client_secret` | OAuth client secret | Required |
| `consul_token` | Consul token for client registration | Required |
| `home_dir_path` | Path to home directories | Required |
| `user_exceptions` | List of users to skip | `[]` |
| `debug` | Enable debug logging | `false` |
| `dry_run` | Only report changes, don't execute | `true` |
| `home_dir_mode` | Permissions for new directories | `0o750` |
| `home_dir_gid` | Group ID for home directories | `1001` |

## Migration from Helm Chart

The Python implementation provides the same functionality as the original Helm chart:

| Helm Chart Feature | Python Implementation |
|-------------------|----------------------|
| Kubernetes CronJob | Linux cron + wrapper script |
| ConfigMap values | JSON configuration file |
| Secret management | Configuration file (secure appropriately) |
| NFS volume mount | Direct file system access |
| Container image | Native Python 3 execution |

## Security Considerations

- Store `config.json` with restricted permissions: `chmod 600 config.json`
- Consider using environment variables for secrets instead of config file
- Ensure the script runs with appropriate user permissions for home directory management
- Regularly rotate OAuth client secrets

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure the script runs with sufficient privileges to create/modify home directories
2. **OAuth Errors**: Verify client credentials and Consul token
3. **Network Issues**: Check connectivity to Viya environment
4. **Python Dependencies**: Install requests library: `pip3 install requests`

### Debug Mode

Enable debug logging for troubleshooting:
```bash
./viya4_home_dir_builder.py --config config.json --debug
```

### Log Files

When using the cron wrapper, logs are written to `viya4_home_dir_builder.log`.

## License

This implementation maintains the same Creative Commons Attribution-NonCommercial-NoDerivatives License as the original Helm chart.