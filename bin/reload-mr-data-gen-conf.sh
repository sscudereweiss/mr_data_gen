#!/usr/bin/env bash
# Reload mr_data_gen savedsearches + macros after git pull on SA-SPLUNK-LAB.
# Run as the splunk OS user (e.g. ssh SA-SPLUNK-LAB, then: sudo su - splunk).
# Requires SPLUNK_PASSWORD (admin password) in the environment.
set -euo pipefail

: "${SPLUNK_PASSWORD:?Set SPLUNK_PASSWORD to the Splunk admin password}"

SPLUNK=/opt/splunk/bin/splunk
AUTH="admin:${SPLUNK_PASSWORD}"

"${SPLUNK}" _internal call \
  /servicesNS/nobody/mr_data_gen/configs/conf-savedsearches/_reload \
  -method POST -auth "${AUTH}"

"${SPLUNK}" _internal call \
  /servicesNS/nobody/mr_data_gen/configs/conf-macros/_reload \
  -method POST -auth "${AUTH}"

echo "Reloaded savedsearches.conf and macros.conf for mr_data_gen."
