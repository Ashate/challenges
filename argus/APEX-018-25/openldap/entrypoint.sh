#!/bin/bash
# Substitute FLAG env var into LDIF files at container startup
if [ -n "$FLAG" ]; then
    find /container/service/slapd/assets/config/bootstrap/ldif/custom/ -name "*.ldif" -exec sed -i "s|FLAG{ldap_injection_authentication_bypass}|$FLAG|g" {} \;
fi
exec /container/tool/run "$@"
