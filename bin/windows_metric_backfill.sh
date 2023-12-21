#! /bin/bash
minutes_backfill=10080
#minutes_backfill=300
file="/opt/splunk/etc/apps/mr_data_gen/bin/windows_entity_list.txt"
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
        echo "Backfill in Progress for : ${line}"
        (for ((i=1; i<=$minutes_backfill; i++)); do
           back_time=$(date -d "$backfill_start -"$i" minutes" +%s)
           Processor_Idle_Time=$(shuf -i 30-80 -n 1)
           Memory_Committed_Bytes_In_Use=$(shuf -i 60-80 -n 1)
           LogicalDisk_Free_Space=$(shuf -i 40-60 -n 1)
           Avg_Disk_Bytes_Read=$(shuf -i 40000-60000 -n 1)
           Avg_Disk_Bytes_Write=$(shuf -i 40000-60000 -n 1)
           Network_Interface_Bytes_Received_sec=$(shuf -i 800000-1000000 -n 1)
           Network_Interface_Bytes_Sent_sec=$(shuf -i 2000000-3000000 -n 1)
           (curl -k -s -o /dev/null https://localhost:8088/services/collector -H "Authorization: Splunk e675db8b-7149-48ed-9483-4f3d0b070f7e" -d '{ "time": "'${back_time}'", "event": "metric", "source": "mcollect", "sourcetype": "mcollect_stash", "host": "'${line}'", "fields": { "metric_name:Avg._Disk_Bytes/Read": "'${Avg_Disk_Bytes_Read}'", "metric_name:Avg._Disk_Bytes/Write": "'${Avg_Disk_Bytes_Write}'", "metric_name:LogicalDisk.%_Free_Space": "'${LogicalDisk_Free_Space}'", "metric_name:Memory.%_Committed_Bytes_In_Use": "'${Memory_Committed_Bytes_In_Use}'", "metric_name:Network_Interface.Bytes_Received/sec": "'${Network_Interface_Bytes_Received_sec}'", "metric_name:Network_Interface.Bytes_Sent/sec": "'${Network_Interface_Bytes_Sent_sec}'", "metric_name:Processor.%_Idle_Time": "'${Processor_Idle_Time}'"}}') &
          done 
          echo "Backfill Complete for : ${line}") &
     done < "$file"
     wait
else
    echo "File $file does not exist or is not readable."
fi

echo "windows backfill finished in $SECONDS seconds"