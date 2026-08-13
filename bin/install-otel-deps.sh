#!/usr/bin/env bash
# Install OpenTelemetry packages into mr_data_gen/lib/ for scripted-input instrumentation.
# Run as the splunk OS user on the Splunk host after git pull.
set -euo pipefail

SPLUNK_HOME="${SPLUNK_HOME:-/opt/splunk}"
APP="${SPLUNK_HOME}/etc/apps/mr_data_gen"
REQ="${APP}/requirements-otel.txt"
TARGET="${APP}/lib"

if [[ ! -f "${REQ}" ]]; then
  echo "Missing ${REQ}" >&2
  exit 1
fi

PYTHON=""
for candidate in "${SPLUNK_HOME}/bin/python3.9" "${SPLUNK_HOME}/bin/python3"; do
  if [[ -x "${candidate}" ]]; then
    PYTHON="${candidate}"
    break
  fi
done

if [[ -z "${PYTHON}" ]]; then
  echo "No Splunk Python interpreter found under ${SPLUNK_HOME}/bin" >&2
  exit 1
fi

mkdir -p "${TARGET}"
"${PYTHON}" -m pip install --upgrade pip
"${PYTHON}" -m pip install --target "${TARGET}" -r "${REQ}"

echo "Installed OpenTelemetry deps into ${TARGET}"
