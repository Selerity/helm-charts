#!/bin/bash

# Prepare Environment File
echo "# SAS Analytics Pro Environment" > /sas-env/sas-env.sh

# Obtain SAS Container Registry credentials
if [ -f /certs.zip ]; then
    echo "Processing Certificate File"
    # Obtain SAS Container Registry credentials
    dl=$(mirrormgr list remote docker login --deployment-data /certs.zip)
    order=${dl#docker login -u }
    order=${order% -p*}
    secret=${dl#docker* -p }
    secret=${secret% cr.sas*}
    secret=$(tr -d "'" <<< "$secret")
    echo "ORDER=${order}" >> /sas-env/sas-env.sh
    echo "REGISTRYSECRET=\"${secret}\"" >> /sas-env/sas-env.sh

    # Get available image versions
    #mirrormgr list remote docker tags --deployment-data /certs.zip | grep sas-analytics-pro | cut -d':' -f2 > /sas-env/apro-versions.txt

    # Get available cadences

fi

if [ "${CLIENTCREDENTIALSID}x" != "x" ] && [ "${CLIENTCREDENTIALSSECRET}x" != "x" ] && [ "${ORDER}x" != "x" ] && [ "${CADENCENAME}x" != "x" ] && [ "${CADENCEVERSION}x" != "x" ]; then
    echo "SAS Viya Orders API credentials and Cadence Info found."
    # if [ -z ${ORDER+x} ]; then
    #     if [ -z ${order+x} ]; then
    #         echo "ERROR: SAS Viya Orders API cannot be used because ORDER is not set"
    #     else
    #         ORDER=${order}
    #     fi
    # fi
    viya4-orders-cli license "${ORDER}" "${CADENCENAME}" "${CADENCEVERSION}" -p /sasinsiderw -n license

fi

# Copy files
if [ -f /authinfo.txt ]; then
    echo "Copying authinfo file"
    cp -v /authinfo.txt /data/
fi
osfiles=(/osconfig/*)
if [ ${#osfiles[@]} -gt 0 ]; then
    echo "Copying osconfig files"
    cp -v /osconfig/* /osconfigrw/
    chmod -v 644 /osconfigrw/*
fi
infiles=(/sasinside/*)
if [ ${#infiles[@]} -gt 0 ]; then
    echo "Copying sasinside files"
    cp -v /sasinside/* /sasinsiderw/
    chmod -v 644 /sasinsiderw/*
fi
echo "Init Done"