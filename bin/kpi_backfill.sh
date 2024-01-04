#! /bin/bash
# Define variables
SPLUNK_HOST="ec2-34-235-75-149.compute-1.amazonaws.com"
USERNAME="admin"
PASSWORD="wordpass123"
# ITSI API endpoint to retrieve service keys
ITSI_API_URL="https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/"
KEY="9eaef7b8-8d05-4a41-9868-df2ac7ef4c73"
ITSI_API_URL="https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/$KEY/"
response=$(curl -s -k -u "${USERNAME}:${PASSWORD}" "$ITSI_API_URL")
remove_template=$(echo "$response" | jq '[{_key: ._key, base_service_template_id: ""}]')
curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/bulk_update/?is_partial_data=1 -H "Content-Type: application/json" -X POST -d "$remove_template"
kpi_keys=$(echo "$response" | jq '[{_key: ._key, kpis: [.kpis[] | select (.title == "ServiceHealthScore" or .title == "CPU Utilization %" or .title == "Database Errors" or .title == "Disk Utilization %" or .title == "Memory Utilization %") | { _key: ._key, title: .title, base_search: .base_search, threshold_field: .threshold_field, aggregate_statop: .aggregate_statop, urgency: .urgency, alert_period: .alert_period, search_alert_earliest: .search_alert_earliest, backfill_enabled: true }]}]')
curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/bulk_update/?is_partial_data=1 -H "Content-Type: application/json" -X POST -d "$kpi_keys"
