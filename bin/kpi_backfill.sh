#! /bin/bash
#curl -k -u admin:wordpass123 https://ec2-34-235-75-149.compute-1.amazonaws.com:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/da-itsi-cp-servicenow-incidents/ | jq '.' > output.json

# Define variables
SPLUNK_HOST="ec2-34-235-75-149.compute-1.amazonaws.com"
USERNAME="admin"
PASSWORD="wordpass123"

# ITSI API endpoint to retrieve service keys
ITSI_API_URL="https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/"

# Make the API request using curl
# Check if the request was successful
file="test_service_keys.txt"
# while IFS= read -r line; do
#     KEY=$line
#     ITSI_API_URL="https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/$KEY/"
#     response=$(curl -s -k -u "${USERNAME}:${PASSWORD}" "$ITSI_API_URL")
#     service_title=$(echo "$response" | jq '.title')
#     echo $service_title
#     echo "$response" > "full$service_title.json"
#     kpi_keys=$(echo "$response" | jq '{kpis: [.kpis[] | select (.title != "ServiceHealthScore") | { _key: ._key, title: .title, base_search: .base_search, threshold_field: .threshold_field, aggregate_thresholds: .aggregate_thresholds, entity_thresholds: .entity_thresholds, backfill_enabled: false }]}')
#     echo "$kpi_keys" > "$service_title.json"
#     curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/$KEY/?is_partial_data=1 -H "Content-Type: application/json" -X POST -d "$kpi_keys"
# done < "$file"
KEY="9eaef7b8-8d05-4a41-9868-df2ac7ef4c73"
ITSI_API_URL="https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/$KEY/"
response=$(curl -s -k -u "${USERNAME}:${PASSWORD}" "$ITSI_API_URL")
service_title=$(echo "$response" | jq '.title')
echo $service_title
echo "$response" > "full$service_title.json"
# kpi_keys=$(echo "$response" | jq '{kpis: [.kpis[] | select (.title != "ServiceHealthScore") | { _key: ._key, title: .title, base_search: .base_search, threshold_field: .threshold_field, aggregate_thresholds: .aggregate_thresholds, entity_thresholds: .entity_thresholds, backfill_enabled: false }]}')
kpi_keys=$(echo "$response" | jq '[{_key: ._key, kpis: [.kpis[] | select (.title != "ServiceHealthScore") | { _key: ._key, title: .title, base_search: .base_search, threshold_field: .threshold_field, backfill_enabled: false }]}]')
echo "$kpi_keys" > "$service_title.json"
curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/$KEY/?is_partial_data=1 -H "Content-Type: application/json" -X POST -d "$kpi_keys"
