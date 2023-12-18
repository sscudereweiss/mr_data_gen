#! /bin/bash
SPLUNK_HOST="splunk.example.com"
USERNAME="admin"
PASSWORD="REDACTED"
# Check if the request was successful
file="service_keys.txt"
while IFS= read -r line; do
    KEY=$line
    curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/${KEY}?is_partial_data=1 -H "Content-Type: application/json" -X POST -d '{"base_service_template_id": ""}'
done < "$file"