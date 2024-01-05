#! /bin/bash


function service_kpi_backfill(){
    KEY="$1"
    #SPLUNK_HOST="localhost"
    SPLUNK_HOST="ec2-34-235-75-149.compute-1.amazonaws.com"
    USERNAME="admin"
    PASSWORD="wordpass123"
    # ITSI API endpoint to retrieve service keys
    result=0
    while [ "$result" == "0" ]; 
    do
      result=$(sudo /opt/splunk/bin/./splunk search "index=itsi_summary itsi_service_id=${KEY} alert_value!="N/A" | stats count" -auth ${USERNAME}:${PASSWORD}  -latest_time '-7d' -header false  2>/dev/null) 
      printf "\r$KEY Count: $result"
      if [ "$result" == "0" ];
        then
            sleep 60
        fi
    done
    ITSI_API_URL="https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/$KEY/"
    response=$(curl -s -k -u "${USERNAME}:${PASSWORD}" "$ITSI_API_URL")
    kpi_keys=$(echo "$response" | jq '[{_key: ._key, kpis: [.kpis[] | select (.title == "ServiceHealthScore") | { _key: ._key, title: .title, backfill_enabled: true}]}]')
    echo $kpi_keys

    curl -k -u "${USERNAME}:${PASSWORD}" https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/bulk_update/?is_partial_data=1 -H "Content-Type: application/json" -X POST -d "$kpi_keys"
 
}

function delete_kpi(){
    KEY="$1"
    #SPLUNK_HOST="localhost"
    SPLUNK_HOST="ec2-34-235-75-149.compute-1.amazonaws.com"
    USERNAME="admin"
    PASSWORD="wordpass123"
    # ITSI API endpoint to retrieve service keys
    ITSI_API_URL="https://${SPLUNK_HOST}:8089/servicesNS/nobody/SA-ITOA/itoa_interface/service/$KEY/"
    curl -k -u "${USERNAME}:${PASSWORD}" "$ITSI_API_URL" -X DELETE
}


service_kpi_backfill "70d25526-df44-4e35-9378-48b86ff46c20"
service_kpi_backfill "34896a2a-b4fa-463d-a016-cf76cde9841a"

delete_kpi "70d25526-df44-4e35-9378-48b86ff46c20"
delete_kpi "34896a2a-b4fa-463d-a016-cf76cde9841a"

SPLUNK_PASSWORD=wordpass123
sudo /opt/splunk/bin/./splunk cmd python /opt/splunk/etc/apps/SA-ITOA/bin/kvstore_to_json.py -m 1 -u admin -p $SPLUNK_PASSWORD -s 8089 -i -d -f '/opt/splunk/backup/itsi_services___service___0.json' -b '4.17.0' -n


sudo /opt/splunk/bin/./splunk cmd python /opt/splunk/etc/apps/SA-ITOA/bin/kvstore_to_json.py -m 2 -u admin -p $SPLUNK_PASSWORD -t -n



[{"_key":"9eaef7b8-8d05-4a41-9868-df2ac7ef4c73","kpis":[{"_key":"12990254-576b-48e3-989b-dc8946b76973","backfill_enabled":true}]}]