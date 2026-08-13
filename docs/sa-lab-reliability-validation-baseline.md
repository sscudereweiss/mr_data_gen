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

## Post-deploy snapshot (-4h window, 2026-08-13 after reload)

Config on branch `feature/sa-lab-savedsearches-throttle` at commit `d4e0001`. Deploy: `git push` locally → `git pull` on host → `bin/reload-mr-data-gen-conf.sh` (HTTP 200 reload at 10:25 ET).

| Metric | Pre-deploy baseline | Post-deploy (-4h) | Notes |
|--------|---------------------|-------------------|-------|
| mr_data_gen inline runs | 47,087 | **10,128** | ~78% reduction (throttle + partial flat macro on Hi_ED DC 1) |
| mr_data_gen inline run-seconds | 8,555 | **1,031** | ~88% reduction |
| mr_data_gen named runs | — | **2,232** | Throttled cadence active |
| Hi_ED DC 1 Generator runs | 236 (~59/h) | **48 (~12/h)** | Matches `*/5 8-18 * * 1-5` |
| ITSI Import (SSM API) | ~60/h | **26 in 10:00 hour** | `*/15` reload applied; full hour should settle ~4/h |
| Scheduler skips (-4h) | 0 | **0** | No skip events |
| EDU_DC_1_* metrics (15m) | — | **12 hosts × 6 points** | Flat macro spike validated via `mstats` |

Hi_ED DC 1 used `generate_*_flat` macros with `map` (16 inline jobs per parent run); SLG APM collapsed to single 7-row pipeline; Synthetics disabled; ITSI imports at `*/15`; DC `schedule_priority=default`.

## Hi_ED DC 1 lookup flatten (2026-08-13)

Config at commit **`dfbe8f5`**. Replaces four role subsearch macros + 16 `map` inline jobs with one `inputlookup edu_dc1_hosts` pipeline and a single `mcollect` pass per scheduled run.

| Dimension | Before (map `_flat` macros) | After (lookup flat) |
|-----------|----------------------------|---------------------|
| Bracket subsearches per run | 4 | **0** |
| `map` inline jobs per run | 16 | **0** |
| Parent scheduled jobs per run | 1 | 1 |
| Host rows per run | 16 (via map) | **16** (`inputlookup where enabled=1`) |
| Expected inline runs from DC1 alone | ~12/h × 16 ≈ **192/h** (demo window) | **~0/h** from DC1 |

### Validation (passed at deploy)

```spl
| inputlookup edu_dc1_hosts where enabled=1 | stats count
| mstats count WHERE index=itsi_im_metrics metric_name=* host=EDU_DC_1_* BY host | stats count as hosts
| mstats avg(cpu.idle) AS avgcpuidle max(df.used) AS maxdiskused max(memory.used) AS maxmemused
  WHERE index=itsi_im_metrics host=EDU_DC_1_MySQL_* BY host
```

| Check | Result |
|-------|--------|
| Lookup rows (`enabled=1`) | **16** |
| Hosts with metrics (-15m) | **16** |
| MySQL KPI base search | **4 hosts** with `cpu.idle`, `df.used`, `memory.used` |
| Ad-hoc `Hi_ED DC 1 Generator` | **DONE** (no SearchParser / mcollect errors) |

### Inline-run audit (compare after 4h in demo window)

```spl
index=_audit action=search info=completed app=mr_data_gen savedsearch_name="" earliest=-4h
| stats count as inline_runs

index=_audit action=search info=completed savedsearch_name="Hi_ED DC 1 Generator" earliest=-4h
| stats count avg(total_run_time) as avg_parent_s max(total_run_time) as max_parent_s
```

Expect: parent `Hi_ED DC 1 Generator` count unchanged (~12/h in demo window); **unnamed inline `count` drops** versus the map-based `_flat` period because DC1 no longer fans out 16 map jobs per parent run. Other DC generators (DC2, SLG) may still contribute inline runs until migrated to the same lookup pattern.

Host coverage is controlled by [`lookups/edu_dc1_hosts.csv`](../lookups/edu_dc1_hosts.csv) (`enabled=0` to disable a row without deleting it).

## Hi_ED DC 1 scripted input (2026-08-13)

Replaces scheduled SPL `map` + `mcollect` with a **classic scripted input** (`bin/edu_dc1_metrics_gen.py` → stdout → log-to-metrics → `itsi_im_metrics`). See [Setting up a scripted input](https://help.splunk.com/en/splunk-enterprise/developing-views-and-apps-for-splunk-web/9.4/build-scripted-inputs/setting-up-a-scripted-input).

| Dimension | SPL + map (prior) | Scripted input |
|-----------|-------------------|----------------|
| Parent scheduled SPL jobs (DC1) | 1 per 5 min | **0** (search disabled) |
| Inline `map` jobs per tick | 16 | **0** |
| Processes per tick | 1 heavy search | 1 Python script, ≤16 stdout lines |
| Host identity | `host=$host$` in map | `_MetaData:Host::` per stdout line |

### Enable on SA Lab

```ini
# local/inputs.conf
[script://$SPLUNK_HOME/etc/apps/mr_data_gen/bin/edu_dc1_metrics_gen.py]
disabled = 0

# local/savedsearches.conf
[Hi_ED DC 1 Generator]
disabled = 1
```

Reload: `bin/reload-mr-data-gen-conf.sh` (inputs + props + transforms). Splunkd restart may be required for scripted input enable — ask before restart.

### Validation

```spl
| mstats count WHERE index=itsi_im_metrics metric_name=* earliest=-15m BY host
| search host=EDU_DC_1_*
| stats count as hosts

| mstats avg(cpu.idle) AS avgcpuidle max(df.used) AS maxdiskused max(memory.used) AS maxmemused
  WHERE index=itsi_im_metrics
  (host=EDU_DC_1_MySQL_01 OR host=EDU_DC_1_MySQL_02 OR host=EDU_DC_1_MySQL_03 OR host=EDU_DC_1_MySQL_04)
  earliest=-15m BY host
```

Expect **16** EDU_DC_1 hosts with fresh metrics during demo window; MySQL KPI base search returns **4** hosts.

## Deploy command

Uses SSH host **`SA-SPLUNK-LAB`** (`~/.ssh/config` → `34.235.75.149`).

**Convention:** SSH as `ec2-user`, then become **`splunk`** for git, Splunk CLI, and app reloads (`sudo su - splunk`). Do not run `splunk` commands as root without `-u splunk`.

Deploy by pushing the branch locally, then pulling on the host (app is a git checkout):

```bash
# Local: push branch
git push origin feature/sa-lab-savedsearches-throttle

# Host: pull branch (as splunk user)
ssh SA-SPLUNK-LAB
sudo su - splunk
cd /opt/splunk/etc/apps/mr_data_gen
git fetch origin feature/sa-lab-savedsearches-throttle
git pull --ff-only origin feature/sa-lab-savedsearches-throttle
git log -1 --oneline
exit   # leave splunk user shell when done
```

Non-interactive equivalent:

```bash
ssh SA-SPLUNK-LAB 'sudo -u splunk bash -s' <<'EOF'
set -e
cd /opt/splunk/etc/apps/mr_data_gen
git pull --ff-only origin feature/sa-lab-savedsearches-throttle
git log -1 --oneline
EOF
```

Reload scheduler and views (still as **splunk** user; requires admin password):

```bash
ssh SA-SPLUNK-LAB
sudo su - splunk
export SPLUNK_PASSWORD='your-admin-password'
/opt/splunk/etc/apps/mr_data_gen/bin/reload-mr-data-gen-conf.sh
curl -sk -u "admin:${SPLUNK_PASSWORD}" -X POST \
  'https://127.0.0.1:8089/services/apps/local/mr_data_gen/_reload'
curl -sk -u "admin:${SPLUNK_PASSWORD}" -X POST \
  'https://127.0.0.1:8089/servicesNS/nobody/mr_data_gen/data/ui/views/_reload'
curl -sk -u "admin:${SPLUNK_PASSWORD}" -X POST \
  'https://127.0.0.1:8089/servicesNS/nobody/mr_data_gen/data/ui/nav/_reload'
```

Or after `sudo su - splunk` and `splunk login`:

```bash
/opt/splunk/bin/splunk _internal call \
  /servicesNS/nobody/mr_data_gen/configs/conf-savedsearches/_reload -method POST
/opt/splunk/bin/splunk _internal call \
  /servicesNS/nobody/mr_data_gen/configs/conf-macros/_reload -method POST
```

Dashboard URL (Classic XML, not Dashboard Studio listing):  
`/app/mr_data_gen/search_performance_validation`
