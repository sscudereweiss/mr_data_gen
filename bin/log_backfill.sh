#! /bin/bash
start_time=`date +%s.%N`
minutes_backfill=10080
#minutes_backfill=2880
#minutes_backfill=10
hec_token="5f99ec42-9989-48f8-b97d-1e41e8f6989a"
file="/opt/splunk/etc/apps/mr_data_gen/bin/db_entity_list.txt"
#file="db_entity_list.txt"
backfill_start=$(date -u)
if [ -r "$file" ]; then
     while IFS= read -r line; do
          echo $line
          for ((i=1; i<=$minutes_backfill; i++)); do
               minute=$(date -d "$backfill_start -"$i" minutes" +"%M")
               if [[ $minute > 40 ]]; then 
                    back_time=$(date -d "$backfill_start -"$i" minutes" +%s)
                    curl -k  https://localhost:8088/services/collector -H "Authorization: Splunk ${hec_token}" -d '{"time": "'${back_time}'", "index": "mysql", "host": "'${line}'", "event": "[CRITICAL] /opt/mysql/bin/mysqld: Disk is full writing '/mysqllog/binlog/localhost-3306-bin.000020' (Errcode: 28). Waiting for someone to free space... Retry in 60 secs"}'
               fi
               
               done
     done < "$file"
else
    echo "File $file does not exist or is not readable."
fi

end_time=`date +%s.%N`
runtime=$( echo "$end_time - $start_time" | bc -l )
echo "mysql backfill finished in $runtime seconds"