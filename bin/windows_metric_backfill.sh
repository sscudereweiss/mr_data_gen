#! /bin/bash
minutes_backfill=10080
file="/opt/splunk/etc/apps/mr_data_gen/bin/windows_entity_list.txt"
backfill_start=$(date -u)
if [ -r "$file" ]; then
     while IFS= read -r line; do
          echo $line
          for ((i=1; i<=$minutes_backfill; i++)); do
               back_time=$(date -d "$backfill_start -"$i" minutes" +%s)
               Processor_Idle_Time=$((40 + RANDOM % 10))
               Memory_Committed_Bytes_In_Use=$((60 + RANDOM % 10 ))
               LogicalDisk_Free_Space=$((50 + RANDOM %10 ))
               Avg_Disk_Bytes_Read=$((1800 + RANDOM % 100 ))
               Avg_Disk_Bytes_Write=$((1800 + RANDOM % 100 ))
               Network_Interface_Bytes_Received_sec=$((7000000 + RANDOM % 100))
               Network_Interface_Bytes_Sent_sec=$((2000000 + RANDOM % 100))
               curl -k -s -o /dev/null https://localhost:8088/services/collector -H "Authorization: Splunk e675db8b-7149-48ed-9483-4f3d0b070f7e" -d '{ "time": "'${back_time}'", "event": "metric", "source": "mcollect", "sourcetype": "mcollect_stash", "host": "'${line}'", "fields": { "metric_name:Avg._Disk_Bytes/Read": "'${Avg_Disk_Bytes_Read}'", "metric_name:Avg._Disk_Bytes/Write": "'${Avg_Disk_Bytes_Write}'", "metric_name:LogicalDisk.%_Free_Space": "'${LogicalDisk_Free_Space}'", "metric_name:Memory.%_Committed_Bytes_In_Use": "'${Memory_Committed_Bytes_In_Use}'", "metric_name:Network_Interface.Bytes_Received/sec": "'${Network_Interface_Bytes_Received_sec}'", "metric_name:Network_Interface.Bytes_Sent/sec": "'${Network_Interface_Bytes_Sent_sec}'", "metric_name:Processor.%_Idle_Time": "'${Processor_Idle_Time}'"}}' &
               done
     done < "$file"
else
    echo "File $file does not exist or is not readable."
fi