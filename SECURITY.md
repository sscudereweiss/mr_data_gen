# Security

This repository generates synthetic Splunk demo data. Treat any credential that was ever committed here as compromised.

## If secrets were exposed

The public git history previously contained demo credentials. If those endpoints were reachable, rotate immediately:

1. **Splunk admin password** — change on every affected instance.
2. **HEC tokens** — revoke and recreate in *Settings → Data Inputs → HTTP Event Collector*.
3. **Review access logs** — check for unauthorized use of rotated credentials.

## Safe configuration

- Never commit real passwords, HEC tokens, or API keys.
- Keep instance-specific values in `local/` on the Splunk server only; use placeholders in git.
- Set environment variables before running `bin/` scripts:
  - `SPLUNK_PASSWORD`
  - `SPLUNK_HEC_TOKEN`
  - `SPLUNK_HOST` (optional, default `localhost`)
  - `SPLUNK_USERNAME` (optional, default `admin`)
- Copy `local/inputs.conf` placeholders (`CHANGE_ME_*`) to real tokens only on the deployment host.
- Leave HEC inputs `disabled = 1` until tokens are configured.

## Reporting issues

If you find sensitive data in this repository, notify the maintainers and rotate affected credentials before public disclosure.
