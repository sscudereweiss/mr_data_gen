#! /bin/bash
minutes_backfill=1440
file="nix_entity_list.txt"
backfill_start=$(date -u)
if [ -r "$file" ]; then
     while IFS= read -r line; do
          echo $line
          for ((i=1; i<=$minutes_backfill; i++)); do
               back_time=$(date -d "$backfill_start -"$i" minutes" +%s)
               CPU_Idle=$(( (RANDOM % 30) + 10 )) # Random CPU usage between 10% and 90%
               Memory_Usage=$(( (RANDOM % 70) + 30 )) # Random Memory usage between 30% and 100%
               Disk_Free=$(( (RANDOM % 60) + 20 )) # Random Disk free between 20% and 80%
               Disk_Read=$(( (RANDOM % 100) + 2000 )) # Random Disk read between 100 and 2100 bytes
               Disk_Write=$(( (RANDOM % 100) + 2000 )) # Random Disk write between 100 and 2100 bytes
               Network_Bytes_Received=$(( (RANDOM % 100) + 1000000 )) # Random Bytes received/sec between 1MB and 11MB
               Network_Bytes_Sent=$(( (RANDOM % 5000000) + 1000000 )) # Random Bytes sent/sec between 1MB and 6MB
               curl -k -s -o /dev/null https://localhost:8088/services/collector -H "Authorization: Splunk e675db8b-7149-48ed-9483-4f3d0b070f7e" -d '{ "time": "'${back_time}'", "event": "metric", "source": "mcollect", "sourcetype": "mcollect_stash", "host": "'${line}'", "fields": { "metric_name:cpu.idle": "'${CPU_Idle}'", "metric_name:memory.used": "'${Memory_Usage}'", "metric_name:df.used": "'${Disk_Free}'", "metric_name:disk.ops.read": "'${Disk_Read}'", "metric_name:disk.ops.write": "'${Disk_Write}'", "metric_name:interface.octets.rx": "'${Network_Bytes_Received}'", "metric_name:interface.octets.tx": "'${Network_Bytes_Sent}'"}}' &
          done
     done < "$file"
else
    echo "File $file does not exist or is not readable."
fi