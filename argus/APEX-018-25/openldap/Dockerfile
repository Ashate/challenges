FROM osixia/openldap:1.5.0

# Copy LDIF files
COPY ldif/ /container/service/slapd/assets/config/bootstrap/ldif/custom/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
