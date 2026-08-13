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

Deploy by pushing the branch locally, then pulling on the host (app is a git checkout):

```bash
# Local: push branch
git push origin feature/sa-lab-savedsearches-throttle

# Host: pull branch (as splunk user)
ssh SA-SPLUNK-LAB 'sudo -u splunk bash -s' <<'EOF'
set -e
cd /opt/splunk/etc/apps/mr_data_gen
git fetch origin feature/sa-lab-savedsearches-throttle
git checkout origin/feature/sa-lab-savedsearches-throttle -- local/savedsearches.conf local/macros.conf
git pull --ff-only origin feature/sa-lab-savedsearches-throttle
git log -1 --oneline
EOF

# Host: reload scheduler (requires admin password)
ssh SA-SPLUNK-LAB 'sudo -u splunk env SPLUNK_PASSWORD="$SPLUNK_PASSWORD" /opt/splunk/etc/apps/mr_data_gen/bin/reload-mr-data-gen-conf.sh'
```

Or interactively on the host:

```bash
ssh SA-SPLUNK-LAB
sudo -u splunk /opt/splunk/bin/splunk login
sudo -u splunk /opt/splunk/bin/splunk _internal call \
  /servicesNS/nobody/mr_data_gen/configs/conf-savedsearches/_reload -method POST
sudo -u splunk /opt/splunk/bin/splunk _internal call \
  /servicesNS/nobody/mr_data_gen/configs/conf-macros/_reload -method POST
```
