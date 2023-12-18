#! /bin/bash
SPLUNK_HOST="ec2-34-235-75-149.compute-1.amazonaws.com"
USERNAME="admin"
PASSWORD="wordpass123"
# Check if the request was successful
file="service_keys.txt"
while IFS= read -r line; do
    KEY=$line
    curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/${KEY}?is_partial_data=1 -H "Content-Type: application/json" -X POST -d '{"base_service_template_id": ""}'
done < "$file"