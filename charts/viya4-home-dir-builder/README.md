# Viya 4 Home Directory Builder

This chart is for SAS Viya 4 deployments that are relying on a non-Posix identify provide (i.e. the identify provider does not manage the `uid` of each user).  This is most likely the case if you are using Samba or Active Directory as your identity provider.  In these situations Viya generates a `uid` for each user to use whenever file system operations are performed in the context of a user. This Helm Chart provides a Cron Job that can be run at regular intervals to make sure the home directories of your users have the correct `uid` (as far as Viya is concerned).

**NOTE:** Do not use this cron job if the home directories being mounted into Viya are already in use with an established Linux landscape.  This will update the `uid` on user's home directories from the generated `uid` stored within Viya.

## Add the Repo

```
helm repo add selerity https://selerity.github.io/helm-charts
helm repo update
```

## Configure your settings

At a minimum you must provide values for `viya.base_url` and `nfs.server`.  All configurable options can be examined by using the following command:

```
helm show values selerity/viya4-home-dir-builder
```

The default settings will create a kubernetes Cron Job that must be triggered manually (i.e. suspended), and when triggered will only report on what it will do (i.e. it will perform a `dry run`).  To allow the process to create/update home directories add the `--set dry_run=0` option to the command line.

## Install Chart

```
helm install -n[VIYA_NAMESPACE] [RELEASE_NAME] selerity/viya4-home-dir-builder --set viya.base_url=[VIYA_BASE_URL] --set nfs.server=[NFS_SERVER_NAME]
```

Example:

```
helm install -nviya thor selerity/viya4-home-dir-builder --set viya.base_url=https://viya.server.com --set nfs.server=mynfs.server.com
```

## Uninstall Chart

```
helm uninstall -n[VIYA_NAMESPACE] [RELEASE_NAME]
```

## Upgrading Chart

```
helm upgrade -n[VIYA_NAMESPACE] [RELEASE_NAME] selerity/viya4-home-dir-builder --install --set viya.base_url=[VIYA_BASE_URL] --set nfs.server=[NFS_SERVER_NAME]
```
