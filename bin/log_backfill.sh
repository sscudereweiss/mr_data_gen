#! /bin/bash
#minutes_backfill=10080
minutes_backfill=1440
#minutes_backfill=10
hec_token="5f99ec42-9989-48f8-b97d-1e41e8f6989a"
file="/opt/splunk/etc/apps/mr_data_gen/bin/db_entity_list.txt"
#file="db_entity_list.txt"
backfill_start=$(date -u)

function ProgressBar {
# Process data
    let _progress=(${1}*100/${2}*100)/100
    let _done=(${_progress}*4)/10
    let _left=40-$_done
# Build progressbar string lengths
    _fill=$(printf "%${_done}s")
    _empty=$(printf "%${_left}s")

# 1.2 Build progressbar strings and print the ProgressBar line
# 1.2.1 Output example:                           
# 1.2.1.1 Progress : [########################################] 100%
printf "\r${3} Backfill Progress : [${_fill// /#}${_empty// /-}] ${_progress}%%"

}


if [ -r "$file" ]; then
     COUNTER=1
     length=$(wc -l < $file )
     while IFS= read -r line; do
          echo "Logs Backfill in Progress for : ${line}"
          (for ((i=1; i<=$minutes_backfill; i++)); do
               minute=$(date -d "$backfill_start -"$i" minutes" +"%M")
               if [[ $minute > 37 ]]; then 
                    back_time=$(date -d "$backfill_start -"$i" minutes" +%s)
                    curl -k -s -o /dev/null https://localhost:8088/services/collector -H "Authorization: Splunk ${hec_token}" -d '{"time": "'${back_time}'", "index": "mysql", "sourcetype": "mysqld", "host": "'${line}'", "event": "[CRITICAL] /opt/mysql/bin/mysqld: Disk is full writing '/mysqllog/binlog/localhost-3306-bin.000020' (Errcode: 28). Waiting for someone to free space... Retry in 60 secs"}'
               fi
          done 
          echo "Backfill Complete for : ${line}") &
     done < "$file"
     wait
else
    echo "File $file does not exist or is not readable."
fi

echo "mysql backfill finished in $SECONDS seconds"