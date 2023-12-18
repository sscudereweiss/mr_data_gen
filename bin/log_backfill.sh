#! /bin/bash
start_time=`date +%s.%N`
minutes_backfill=10080
#minutes_backfill=1440
#minutes_backfill=10
hec_token="60469025-55a6-4718-81af-4c047f13401b"
file="/opt/splunk/etc/apps/mr_data_gen/bin/db_entity_list.txt"
#file="db_entity_list.txt"
backfill_start=$(date -u)
if [ -r "$file" ]; then
     while IFS= read -r line; do
          echo $line
          (for ((i=5; i<=$minutes_backfill; i+=5)); do
               #back_time=$(date -d "$backfill_start -"$i" minutes" +"%Y/%m/%d %H:%M:%S")
               back_time=$(date -d "$backfill_start -"$i" minutes" +%s)
               log_line="[CRITICAL] /opt/mysql/bin/mysqld: Disk is full writing '/mysqllog/binlog/localhost-3306-bin.000020' (Errcode: 28). Waiting for someone to free space... Retry in 60 secs"
               curl -k -s -o /dev/null https://localhost:8088/services/collector -H "Authorization: Splunk ${hec_token}" -d '{"time": "'${back_time}'", "event": "[CRITICAL] /opt/mysql/bin/mysqld: Disk is full writing '/mysqllog/binlog/localhost-3306-bin.000020' (Errcode: 28). Waiting for someone to free space... Retry in 60 secs"}'
               done) &
     done < "$file"
     wait
else
    echo "File $file does not exist or is not readable."
fi

end_time=`date +%s.%N`
runtime=$( echo "$end_time - $start_time" | bc -l )
echo "mysql backfill finished in $runtime seconds"