#!/bin/sh

SAS_API_BASE="https://api.apiproxy.sas.com/mysas"

# Prepare Environment File
echo "# SAS Analytics Pro Environment" > /sas-env/sas-env.sh

# Download license via SAS Orders API
if [ "${CLIENTCREDENTIALSID}x" != "x" ] && [ "${CLIENTCREDENTIALSSECRET}x" != "x" ] && [ "${ORDER}x" != "x" ] && [ "${CADENCENAME}x" != "x" ] && [ "${CADENCEVERSION}x" != "x" ]; then
    echo "Downloading license from SAS Orders API..."
    curl -sf \
        -H "ClientId: ${CLIENTCREDENTIALSID}" \
        -H "ClientSecret: ${CLIENTCREDENTIALSSECRET}" \
        -o /sasinsiderw/license.jwt \
        "${SAS_API_BASE}/orders/${ORDER}/cadences/${CADENCENAME}/${CADENCEVERSION}/license"

    if [ $? -eq 0 ]; then
        echo "License downloaded successfully."
    else
        echo "ERROR: Failed to download license from SAS Orders API."
        exit 1
    fi
fi

# Download and extract certificates for registry credentials
if [ -f /certs.zip ]; then
    echo "Processing provided certificate file..."
    mkdir -p /tmp/certs
    unzip -qo /certs.zip -d /tmp/certs

    # Extract registry credentials from the entitlement certificate
    PEM_FILE=$(find /tmp/certs -name "entitlement_certificate.pem" -type f | head -1)
    if [ -n "$PEM_FILE" ]; then
        order=$(openssl x509 -in "$PEM_FILE" -noout -subject 2>/dev/null | sed -n 's/.*CN *= *//p')
        secret=$(cat "$PEM_FILE" | base64 -w 0 2>/dev/null || cat "$PEM_FILE" | base64 2>/dev/null)
        if [ -n "$order" ] && [ -n "$secret" ]; then
            echo "ORDER=${order}" >> /sas-env/sas-env.sh
            echo "REGISTRYSECRET=\"${secret}\"" >> /sas-env/sas-env.sh
            echo "Registry credentials extracted from certificate."
        fi
    else
        echo "WARNING: No entitlement_certificate.pem found in certificate archive."
    fi
    rm -rf /tmp/certs
elif [ "${CLIENTCREDENTIALSID}x" != "x" ] && [ "${CLIENTCREDENTIALSSECRET}x" != "x" ] && [ "${ORDER}x" != "x" ]; then
    echo "Downloading certificates from SAS Orders API..."
    curl -sf \
        -H "ClientId: ${CLIENTCREDENTIALSID}" \
        -H "ClientSecret: ${CLIENTCREDENTIALSSECRET}" \
        -o /tmp/certs.zip \
        "${SAS_API_BASE}/orders/${ORDER}/certificates"

    if [ $? -eq 0 ] && [ -f /tmp/certs.zip ]; then
        mkdir -p /tmp/certs
        unzip -qo /tmp/certs.zip -d /tmp/certs

        PEM_FILE=$(find /tmp/certs -name "entitlement_certificate.pem" -type f | head -1)
        if [ -n "$PEM_FILE" ]; then
            order=$(openssl x509 -in "$PEM_FILE" -noout -subject 2>/dev/null | sed -n 's/.*CN *= *//p')
            secret=$(cat "$PEM_FILE" | base64 -w 0 2>/dev/null || cat "$PEM_FILE" | base64 2>/dev/null)
            if [ -n "$order" ] && [ -n "$secret" ]; then
                echo "ORDER=${order}" >> /sas-env/sas-env.sh
                echo "REGISTRYSECRET=\"${secret}\"" >> /sas-env/sas-env.sh
                echo "Registry credentials extracted from downloaded certificate."
            fi
        else
            echo "WARNING: No entitlement_certificate.pem found in downloaded archive."
        fi
        rm -rf /tmp/certs /tmp/certs.zip
    else
        echo "ERROR: Failed to download certificates from SAS Orders API."
        exit 1
    fi
fi

# Copy files
if [ -f /authinfo.txt ]; then
    echo "Copying authinfo file"
    cp -v /authinfo.txt /data/
fi
if [ "$(ls /osconfig/ 2>/dev/null)" ]; then
    echo "Copying osconfig files"
    cp -v /osconfig/* /osconfigrw/
    chmod -v 644 /osconfigrw/*
fi
if [ "$(ls /sasinside/ 2>/dev/null)" ]; then
    echo "Copying sasinside files"
    cp -v /sasinside/* /sasinsiderw/
    chmod -v 644 /sasinsiderw/*
fi
echo "Init Done"
