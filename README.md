# MR Data Gen

Splunk app (v1.1.3) that generates synthetic demo data for **Splunk ITSI**, Nagios, MySQL, RUM, APM, and Synthetics scenarios using scheduled saved searches and optional HEC backfill scripts.

## Requirements

- Splunk Enterprise with **Splunk ITSI** and **SA-ITOA**
- Indexes: `itsi_im_metrics`, `itsi_im_meta`, `nagios`, `mysql`, and ITSI summary indexes (see `local/indexes.conf` for retention caps)
- Role `itoa_admin` referenced in metadata ACLs (or adjust permissions in `metadata/default.meta`)

## App layout

```
mr_data_gen/
├── default/          # Shipped saved searches, macros, props, dashboards
├── local/            # Instance-specific inputs, index limits, ITSI import searches
├── bin/              # Backfill and ITSI content-pack helper scripts
├── lookups/          # CSV lookups (eventstorm_hosts, simple_replaytest)
└── metadata/         # Object permissions
```

## Install

1. Copy this app to `$SPLUNK_HOME/etc/apps/mr_data_gen`.
2. Configure HEC tokens in `local/inputs.conf` (replace `CHANGE_ME_*` placeholders) and set `disabled = 0` when ready.
3. Reload or restart Splunk to pick up the app.
4. Validate configuration:

   ```bash
   $SPLUNK_HOME/bin/splunk btool check --debug
   # Splunk 9+
   $SPLUNK_HOME/bin/splunk validate files
   ```

## Scheduled data generation

`default/savedsearches.conf` contains 15 scheduled searches (mostly every minute) for EDU/SLG Nagios alerts, datacenter generators, RUM/APM, Synthetics, and MySQL errors. Review and disable searches you do not need in demo environments.

`local/savedsearches.conf` contains ITSI import-object searches (KPI attributes, episode contact map, APM/RUM/SSM entity import).

## Dashboards

From the app nav:

- `datagen_status` — monitor generated metrics
- `mysql_backfill_status` — MySQL backfill status
- `entity_management_reporting_and_analytics` — entity reporting

## Bin scripts

Set credentials before running operational scripts:

| Variable | Used by |
|----------|---------|
| `SPLUNK_PASSWORD` | `enable_content_packs.sh`, `kpi_backfill.sh`, `template_removal.sh` |
| `SPLUNK_HEC_TOKEN` | `*_metric_backfill.sh`, `log_backfill.sh`, `summary_metric_backfill.sh` |
| `SPLUNK_HOST` | REST scripts (default: `localhost`) |
| `SPLUNK_USERNAME` | REST scripts (default: `admin`) |

Example:

```bash
export SPLUNK_PASSWORD='your-admin-password'
export SPLUNK_HEC_TOKEN='your-hec-token'
./bin/nix_metric_backfill.sh
```

## Lookups

`lookups/eventstorm_hosts.csv` is defined in `default/transforms.conf` as `eventstorm_hosts` for use in SPL via `lookup eventstorm_hosts ...`.

## Notes

- `local/` contains instance overrides; do not copy host-specific tokens into shared packages.
- Backfill scripts assume Linux paths under `/opt/splunk/etc/apps/mr_data_gen/bin/` for entity list files.
- `bin/enable_content_packs.sh` installs ITSI content packs via the SA-ITOA REST API.
