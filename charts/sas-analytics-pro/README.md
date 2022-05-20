# SAS Analytics Pro on Viya

This chart will deploy SAS Anlaytics Pro on Viya.  You can deploy this on a cloud Kubernetes service such as EKS (AWS) or AKS (Azure), or on the Kubernetes service deployed on Docker Desktop (KIND).

## Add the Repo

```
helm repo add selerity https://selerity.github.io/helm-charts
helm repo update
```

## Configure your settings

At a minimum you must provide values for `sas.order` and `sas.registryPass`.  All configurable options can be examined by using the following command:

```
helm show values selerity/sas-analytics-pro
```

The `sas.registryPass` value can be found by using the `mirrormgr list remote docker login` command as described in [Step 2 — Access the Container Image](https://documentation.sas.com/doc/en/anprocdc/v_011/dplyviya0ctr/p0ot22u2rapcsfn1outngvut0f8m.htm#p0xt4ltecfl3gan1rvt589xgjpu6) of the official SAS Documentation.  Use the value shown as `randompasswordvalue` in the SAS documentation.

## Install Chart

```
helm install -n[VIYA_NAMESPACE] [RELEASE_NAME] selerity/sas-analytics-pro --set sas.order=[ORDER] --set sas.registryPass=[REGISTRY_PASSWORD]]
```

Example:

```
helm install -nviya xena selerity/sas-analytics-pro --set sas.order=ABC123 --set sas.registryPass="asdf@#%asd"
```

## Uninstall Chart

```
helm uninstall -n[VIYA_NAMESPACE] [RELEASE_NAME]
```

## Upgrading Chart

```
helm upgrade -n[VIYA_NAMESPACE] [RELEASE_NAME] selerity/sas-analytics-pro --install --set sas.order=[ORDER] --set sas.registryPass=[REGISTRY_PASSWORD]
```

# NOTE

If you are using the Kubernetes service provided by Docker Desktop (KIND) you should manually pull the image before running the `helm` command. You can achieve this by following the steps in the official documentation for [Step 2 - Access the Container Image](https://documentation.sas.com/doc/en/anprocdc/v_011/dplyviya0ctr/p0ot22u2rapcsfn1outngvut0f8m.htm#p0xt4ltecfl3gan1rvt589xgjpu6) and stop once you have completed the `docker pull output-from-step-3` step.