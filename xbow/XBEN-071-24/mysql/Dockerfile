FROM mysql:8.0
COPY backup.sql /docker-entrypoint-initdb.d/
COPY entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh
ENTRYPOINT ["/custom-entrypoint.sh"]
CMD ["mysqld"]
