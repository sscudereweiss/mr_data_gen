#! /bin/bash


function service_kpi_backfill(){
    KEY="$1"
    #SPLUNK_HOST="localhost"
    SPLUNK_HOST="ec2-34-235-75-149.compute-1.amazonaws.com"
    USERNAME="admin"
    PASSWORD="wordpass123"
    # ITSI API endpoint to retrieve service keys
    result=0
    ITSI_API_URL="https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/$KEY/"
    response=$(curl -s -k -u "${USERNAME}:${PASSWORD}" "$ITSI_API_URL")
    service_title=$(echo "$response" | jq '.title' | sed 's/"//g')
    while [[ $result < 8 ]]; do
      result=$(sudo /opt/splunk/bin/./splunk search "| rest /services/messages | search message=\"Backfill*${service_title}*completed*\" | stats count" -auth ${USERNAME}:${PASSWORD} -header false  2>/dev/null) 
      printf "\r$service_title Count: $result"
      sleep 5
    done
    kpi_keys=$(echo "$response" | jq '[{_key: ._key, kpis: [.kpis[] | select (.title == "ServiceHealthScore") | { _key: ._key, title: .title, base_search: .base_search, threshold_field: .threshold_field, aggregate_statop: .aggregate_statop, urgency: .urgency, alert_period: .alert_period, search_alert_earliest: .search_alert_earliest, entity_id_fields: .entity_id_fields, entity_breakdown_id_fields: .entity_breakdown_id_fields, is_entity_breakdown: .is_entity_breakdown, is_service_entity_filter: .is_service_entity_filter, entity_statop: .entity_statop, backfill_earliest_time: "-7d", backfill_enabled: true }]}]')
    curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/bulk_update/?is_partial_data=1 -H "Content-Type: application/json" -X POST -d "$kpi_keys" 
}


(service_kpi_backfill "f799f86e-3128-443f-aba2-22f0cddab0e5") &
(service_kpi_backfill "34896a2a-b4fa-463d-a016-cf76cde9841a") &
wait