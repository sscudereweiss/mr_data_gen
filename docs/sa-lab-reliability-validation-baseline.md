# mr_data_gen reliability validation baseline

Captured **before** deploying throttled schedules in `local/savedsearches.conf` to prod (2026-08-12).

## Pre-deploy baseline (-4h window)

| Metric | Value |
|--------|-------|
| Splunk health | **red** (scheduler) |
| mr_data_gen inline runs | 47,087 |
| mr_data_gen inline run-seconds | 8,555 |
| SLG DC 1 Generator runs | 240 (~60/h) |
| Hi_ED DC 1 Generator runs | 236 (~59/h) |
| Scheduler skips (-4h) | 0 (none in window) |

## Expected post-deploy (demo hours Mon–Fri 08:00–18:00, `*/5`)

| Search | Before cadence | After cadence | Expected runs/h (demo window) |
|--------|----------------|---------------|-------------------------------|
| DC generators | ~60/h | `*/5 8-18 * * 1-5` | ~12/h |
| Inline fan-out | ~11.8k/h | proportional | ~2.4k/h |
| Off-hours | ~60/h each | 0 | 0 |

## Validation SPL (run 4h after deploy)

```spl
index=_audit action=search info=completed app=mr_data_gen earliest=-4h
| stats count avg(total_run_time) as avg_s sum(total_run_time) as total_s by savedsearch_name
| sort - count

index=_audit action=search info=completed app=mr_data_gen savedsearch_name="" earliest=-4h
| timechart span=15m count

index=_audit action=search info=completed savedsearch_name="SLG DC 1 Generator" earliest=-4h
| timechart span=15m count

index=_internal source=*scheduler.log* "Skipping execution" earliest=-4h
| rex field=_raw "reason=(?<reason>[^,]+)"
| stats count by reason
```

## Deploy command

Uses SSH host **`SA-SPLUNK-LAB`** (`~/.ssh/config` → `34.235.75.149`).

```bash
# Quick SSH test
ssh SA-SPLUNK-LAB 'hostname'

scp local/savedsearches.conf SA-SPLUNK-LAB:/tmp/
ssh SA-SPLUNK-LAB 'sudo cp /tmp/savedsearches.conf /opt/splunk/etc/apps/mr_data_gen/local/ && \
  sudo chown splunk:splunk /opt/splunk/etc/apps/mr_data_gen/local/savedsearches.conf && \
  sudo /opt/splunk/bin/splunk validate files --type=conf --name=savedsearches --path=/opt/splunk/etc/apps/mr_data_gen && \
  sudo /opt/splunk/bin/splunk reload saved-searches'
```
