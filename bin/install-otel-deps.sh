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
PIP=""
for candidate in "${SPLUNK_HOME}/bin/python3.9" "${SPLUNK_HOME}/bin/python3"; do
  if [[ -x "${candidate}" ]] && "${candidate}" -c "import ssl" >/dev/null 2>&1; then
    PYTHON="${candidate}"
    PIP="${candidate} -m pip"
    break
  fi
done

if [[ -z "${PYTHON}" ]]; then
  for candidate in /usr/bin/python3.9 /usr/bin/python3; do
    if [[ -x "${candidate}" ]] && "${candidate}" -c "import ssl" >/dev/null 2>&1; then
      PYTHON="${candidate}"
      PIP="${candidate} -m pip"
      echo "Splunk Python lacks SSL; installing with ${candidate} into ${TARGET}"
      break
    fi
  done
fi

if [[ -z "${PYTHON}" ]]; then
  echo "No Python with SSL found for pip install" >&2
  exit 1
fi

mkdir -p "${TARGET}"
${PIP} install --upgrade pip
${PIP} install --target "${TARGET}" -r "${REQ}"

echo "Installed OpenTelemetry deps into ${TARGET}"
