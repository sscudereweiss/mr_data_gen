#! /bin/bash
SPLUNK_HOST="ec2-34-235-75-149.compute-1.amazonaws.com"

function service_kpi_backfill(){
    KEY="$1"
    SPLUNK_HOST="localhost"
    USERNAME="admin"
    PASSWORD="wordpass123"
    # ITSI API endpoint to retrieve service keys
    
    ITSI_API_URL="https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/$KEY/"
    response=$(curl -s -k -u "${USERNAME}:${PASSWORD}" "$ITSI_API_URL")
    remove_template=$(echo "$response" | jq '[{_key: ._key, base_service_template_id: ""}]')
    curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/bulk_update/?is_partial_data=1 -H "Content-Type: application/json" -X POST -d "$remove_template"
    sudo /opt/splunk/bin/./splunk cmd python /opt/splunk/etc/apps/SA-ITOA/bin/kvstore_to_json.py -m 2 -u ${USERNAME} -p ${PASSWORD} -t -f '/opt/splunk/etc/apps/mr_data_gen/bin/kvstoreops' -n
    
    #kpi_keys=$(echo "$response" | jq '[{_key: ._key, kpis: [.kpis[] | select (.title == "CPU Utilization %" or .title == "Database Errors" or .title == "Disk Utilization %" or .title == "Memory Utilization %") | { _key: ._key, title: .title, base_search: .base_search, threshold_field: .threshold_field, aggregate_statop: .aggregate_statop, urgency: .urgency, alert_period: .alert_period, search_alert_earliest: .search_alert_earliest, entity_id_fields: .entity_id_fields, entity_breakdown_id_fields: .entity_breakdown_id_fields, is_entity_breakdown: .is_entity_breakdown, is_service_entity_filter: .is_service_entity_filter, entity_statop: .entity_statop, base_search_id: .base_search_id, base_search_metric: .base_search_metric, backfill_earliest_time: "-1d", backfill_enabled: true }]}]')
    #curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/bulk_update/?is_partial_data=1 -H "Content-Type: application/json" -X POST -d "$kpi_keys"

    # result=0
    # while [ "$result" == "0" ]; 
    # do
    #   result=$(sudo /opt/splunk/bin/./splunk search "index=itsi_summary itsi_service_id=${KEY} alert_value!="N/A" | stats count" -auth ${USERNAME}:${PASSWORD}  -latest_time '-1d' -header false  2>/dev/null) 
    #   printf "\r$KEY Count: $result"
    #   sleep 60
    # done

    # kpi_keys=$(echo "$response" | jq '[{_key: ._key, kpis: [.kpis[] | select (.title == "ServiceHealthScore"
    # ) | { _key: ._key, title: .title, base_search: .base_search, threshold_field: .threshold_field, aggregate_statop: .aggregate_statop, urgency: .urgency, alert_period: .alert_period, search_alert_earliest: .search_alert_earliest, entity_id_fields: .entity_id_fields, entity_breakdown_id_fields: .entity_breakdown_id_fields, is_entity_breakdown: .is_entity_breakdown, is_service_entity_filter: .is_service_entity_filter, entity_statop: .entity_statop, backfill_earliest_time: "-1d", backfill_enabled: true }]}]')

    # curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/bulk_update/?is_partial_data=1 -H "Content-Type: application/json" -X POST -d "$kpi_keys"
 
}

function delete_kpi(){
    KEY="$1"
    SPLUNK_HOST="localhost"
    USERNAME="admin"
    PASSWORD="wordpass123"
    # ITSI API endpoint to retrieve service keys
    ITSI_API_URL="https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/$KEY/"
    curl -k -u "${USERNAME}:${PASSWORD}" "$ITSI_API_URL" -X DELETE
}


service_kpi_backfill "9eaef7b8-8d05-4a41-9868-df2ac7ef4c73"
service_kpi_backfill "518e222b-55a1-4443-ab6e-e02c44071e54"

delete_kpi "9eaef7b8-8d05-4a41-9868-df2ac7ef4c73"
delete_kpi "518e222b-55a1-4443-ab6e-e02c44071e54"

SPLUNK_PASSWORD=wordpass123
sudo /opt/splunk/bin/./splunk cmd python /opt/splunk/etc/apps/SA-ITOA/bin/kvstore_to_json.py -m 1 -u admin -p $SPLUNK_PASSWORD -s 8089 -i -d -f '/opt/splunk/backup/itsi_services___service___0.json' -b '4.17.0' -n


sudo /opt/splunk/bin/./splunk cmd python /opt/splunk/etc/apps/SA-ITOA/bin/kvstore_to_json.py -m 2 -u admin -p $SPLUNK_PASSWORD -t -n



[{"_key":"9eaef7b8-8d05-4a41-9868-df2ac7ef4c73","kpis":[{"_key":"12990254-576b-48e3-989b-dc8946b76973","backfill_enabled":true}]}]