#! /bin/bash
# minutes_backfill=10080
minutes_backfill=1440
hec_token=f17239e6-0ab5-47aa-8e01-7d265bbc573c
service_id=adfd2fc7-1cb1-45ee-a7e2-888e483789c8
# service_id=$1
kpi_id=SHKPI-adfd2fc7-1cb1-45ee-a7e2-888e483789c8
# kpi_id=$2

backfill_start=$(date -u)
service_health_score=100
alert_level=2
alert_severity=normal
color=\#99D18B

(for ((i=1; i<=$minutes_backfill; i++)); do
    back_time=$(date -d "$backfill_start -"$i" minutes" +%s)
    info_min_time=$(date -d "$backfill_start -"$(($i+1))" minutes" +%s)
    
    curl -k -s -o /dev/null https://localhost:8088/services/collector -H "Authorization: Splunk ${hec_token}" -d '{"time":"'${back_time}'","event":"metric","index": "itsi_summary_metrics", "source":"service_health_metrics_monitor","sourcetype":"itsi_summary:metrics","fields":{"alert_period":"1","source":"service_health_metrics_monitor","sourcetype":"stash","info_max_time":"'${back_time}'","info_min_time":"'${info_min_time}'","info_search_time":"'${back_time}'","is_null_alert_value":"0","itsi_kpi_id":"'${kpi_id}'","itsi_service_id":"'${service_id}'","itsi_team_id":"default_itsi_security_group","scoretype":"service_health", "metric_name:service_health_score":"'${service_health_score}'"}}'
    
    curl -k -s -o /dev/null https://localhost:8088/services/collector -H "Authorization: Splunk ${hec_token}" -d '{"time":"'${back_time}'","event":"metric", "index": "itsi_summary_metrics", "source":"service_health_metrics_monitor","sourcetype":"itsi_summary:metrics","fields":{"alert_period":"1","source":"service_health_metrics_monitor","sourcetype":"stash","info_max_time":"'${back_time}'","info_min_time":"'${info_min_time}'","info_search_time":"'${back_time}'","is_null_alert_value":"0","itsi_kpi_id":"'${kpi_id}'","itsi_service_id":"'${service_id}'","itsi_team_id":"default_itsi_security_group","scoretype":"service_health","metric_name:alert_level":"'${alert_level}'"}}'
    
    curl -k -s -o /dev/null https://localhost:8088/services/collector -H "Authorization: Splunk ${hec_token}" -d '{"time": "'${back_time}'", "index": "itsi_summary", "sourcetype": "stash", "event": "search_name=service_health_monitor, search_now='${back_time}', info_min_time='${info_min_time}', info_max_time='${back_time}', info_search_time='${back_time}', kpi=ServiceHealthScore, color="'${color}'", kpiid="'${kpi_id}'", scoretype=service_health, serviceid="'${service_id}'", itsi_service_id="'${service_id}'", alert_level='${alert_level}', itsi_kpi_id="'${kpi_id}'", alert_severity='${alert_severity}', health_score="'${service_health_score}'", severity_label='${alert_severity}', severity_value="'${service_health_score}'""}'
done) &

wait

