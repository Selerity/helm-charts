# SAS Analytics Pro on Viya

This chart will deploy SAS Analytics Pro on Viya.  You can deploy this on a cloud Kubernetes service such as EKS (AWS) or AKS (Azure), or on the Kubernetes service deployed on Docker Desktop (KIND).

## Add the Repo

```
helm repo add selerity https://selerity.github.io/helm-charts
helm repo update
```

## Configure your settings

At a minimum you must provide values for `sas.order`, `sas.registryPass` and `sas.license`.  All configurable options can be examined by using the following command:

```
helm show values selerity/sas-analytics-pro
```

The `sas.registryPass` value can be found in the SAS documentation for [Step 2 — Access the Container Image](https://documentation.sas.com/doc/en/anprocdc/v_011/dplyviya0ctr/p0ot22u2rapcsfn1outngvut0f8m.htm#p0xt4ltecfl3gan1rvt589xgjpu6). Use the value shown as `randompasswordvalue` in the SAS documentation.

## Install Chart

```
helm install -n[VIYA_NAMESPACE] [RELEASE_NAME] selerity/sas-analytics-pro --set sas.order=[ORDER] --set sas.registryPass=[REGISTRY_PASSWORD] --set-file sas.license=[PATH_TO_LICENSE_FILE]
```

Example:

```
helm install -nviya xena selerity/sas-analytics-pro --set sas.order=ABC123 --set sas.registryPass="asdf@#%asd" --set-file sas.license=license.jwt
```

## Uninstall Chart

```
helm uninstall -n[VIYA_NAMESPACE] [RELEASE_NAME]
```

## Upgrading Chart

```
helm upgrade -n[VIYA_NAMESPACE] [RELEASE_NAME] selerity/sas-analytics-pro --install --set sas.order=[ORDER] --set sas.registryPass=[REGISTRY_PASSWORD] --set-file sas.license=[PATH_TO_LICENSE_FILE]
```

### Upgrading to 1.1.0

- The init container no longer uses the `selerity/sas-tools` image. It now uses `alpine:3.21` and calls the SAS Orders API directly via `curl` instead of relying on `mirrormgr` and `viya4-orders-cli`.
- New `initImage` value allows overriding the init container image.
- If you were providing `sas.ordersApiKey` and `sas.ordersApiSecret`, the license download now uses the SAS API directly — no behaviour change required.

### Upgrading to 1.0.0

This release includes the following breaking changes:

- `volumes` and `volumeMounts` values changed from object (`{}`) to array (`[]`) type. If you have custom volumes configured, update your values to use array syntax.
- Added `rbac.create` toggle. Existing deployments are unaffected as it defaults to `false`.

# NOTE

If you are using the Kubernetes service provided by Docker Desktop (KIND) you should manually pull the image before running the `helm` command. You can achieve this by following the steps in the official documentation for [Step 2 - Access the Container Image](https://documentation.sas.com/doc/en/anprocdc/v_011/dplyviya0ctr/p0ot22u2rapcsfn1outngvut0f8m.htm#p0xt4ltecfl3gan1rvt589xgjpu6) and stop once you have completed the `docker pull output-from-step-3` step.
