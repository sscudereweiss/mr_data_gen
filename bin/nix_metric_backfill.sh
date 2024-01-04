#! /bin/bash
minutes_backfill=1440
#minutes_backfill=300
file="/opt/splunk/etc/apps/mr_data_gen/bin/nix_entity_list.txt"
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
            minute=$(date -d "$backfill_start -"$i" minutes" +"%M")
            if [[ $minute < 37 ]]; 
            then
                CPU_Idle=$(shuf -i 50-60 -n 1) # Random CPU usage between 50% and 60%
                Memory_Usage=$(shuf -i 10-20 -n 1) # Random Memory usage between 10% and 20%
                Disk_Free=$(shuf -i 15-25 -n 1) # Random Disk free between 40% and 80%
                Disk_Read=$(shuf -i 2000-2100 -n 1) # Random Disk read between 100 and 2100 bytes
                Disk_Write=$(shuf -i 2000-2100 -n 1) # Random Disk write between 100 and 2100 bytes
                Network_Bytes_Received=$(shuf -i 800000-900000 -n 1) # Random Bytes received/sec between 1MB and 11MB
                Network_Bytes_Sent=$(shuf -i 2000000-2500000 -n 1) # Random Bytes sent/sec between 1MB and 6MB
            else
                CPU_Idle=$(shuf -i 90-100 -n 1) # Random CPU usage between 50% and 60%
                Memory_Usage=$(shuf -i 90-100 -n 1) # Random Memory usage between 10% and 20%
                Disk_Free=$(shuf -i 90-100 -n 1) # Random Disk free between 40% and 80%
                Disk_Read=$(shuf -i 0-100 -n 1) # Random Disk read between 100 and 2100 bytes
                Disk_Write=$(shuf -i 0-100 -n 1) # Random Disk write between 100 and 2100 bytes
                Network_Bytes_Received=$(shuf -i 900000-1000000 -n 1) # Random Bytes received/sec between 1MB and 11MB
                Network_Bytes_Sent=$(shuf -i 2500000-3000000 -n 1) # Random Bytes sent/sec between 1MB and 6MB
            fi
            curl -k -s -o /dev/null https://localhost:8088/services/collector -H "Authorization: Splunk e675db8b-7149-48ed-9483-4f3d0b070f7e" -d '{ "time": "'${back_time}'", "event": "metric", "source": "mcollect", "sourcetype": "mcollect_stash", "host": "'${line}'", "fields": { "metric_name:cpu.idle": "'${CPU_Idle}'", "metric_name:memory.used": "'${Memory_Usage}'", "metric_name:df.used": "'${Disk_Free}'", "metric_name:disk.ops.read": "'${Disk_Read}'", "metric_name:disk.ops.write": "'${Disk_Write}'", "metric_name:interface.octets.rx": "'${Network_Bytes_Received}'", "metric_name:interface.octets.tx": "'${Network_Bytes_Sent}'"}}'
          done
          echo "Backfill Complete for : ${line}") &
     done < "$file"
     wait
else
    echo "File $file does not exist or is not readable."
fi

echo "nix backfill finished in $SECONDS seconds"