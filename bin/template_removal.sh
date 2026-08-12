#! /bin/bash
SPLUNK_HOST="${SPLUNK_HOST:-localhost}"
USERNAME="${SPLUNK_USERNAME:-admin}"
: "${SPLUNK_PASSWORD:?Set SPLUNK_PASSWORD before running this script}"
# Check if the request was successful
file="service_keys.txt"
while IFS= read -r line; do
    KEY=$line
    curl -k -u "${USERNAME}:${SPLUNK_PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/${KEY}?is_partial_data=1 -H "Content-Type: application/json" -X POST -d '{"base_service_template_id": ""}'
done < "$file"