# Kubernetes-Integrated Viya 4 Home Directory Builder

Minimal Python implementation that uses kubectl to get configuration from existing Kubernetes secrets/configmaps.

## Requirements

- Python 3 with `requests` library
- `kubectl` access to SAS Viya namespace

## Installation

```bash
pip3 install requests
chmod +x k8s_viya_home_builder.py k8s_cron.sh
```

## Usage

### Manual Execution
```bash
./k8s_viya_home_builder.py <namespace> <viya_url> [home_path]
./k8s_viya_home_builder.py viya https://viya.company.com /home
```

### Scheduled (Cron)
```bash
crontab -e
# Add: 0,15,30,45 * * * * /path/to/k8s_cron.sh viya https://viya.company.com /home
```

## Configuration

Script retrieves:
- `CONSUL_TOKEN` from `sas-consul-client` secret
- Generates OAuth client dynamically
- Uses command line arguments for Viya URL and home path

## Migration

Replace Helm chart CronJob with this script - uses identical credentials and settings.