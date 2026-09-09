# Scheduled Jobs Architecture

## Services
Periodic tasks (nightly inventory reconciliation, thumbnail re-processing, cleanup jobs) run on a schedule, historically via host-level cron entries. Each job is expected to report a success or failure status after each run.

## Failure Modes
The main failure mode is a job silently ceasing to run without anyone noticing, most commonly after an infrastructure migration where the new host's cron configuration is provisioned from a template that doesn't include every job that existed on the old host. Because host-level cron has no independent monitoring of whether a job actually ran, this kind of gap can persist for days before downstream data drift makes it visible.

## Mitigations
Mitigations include a dead-man's-switch style alert per job that fires if it hasn't reported success within its expected interval plus a margin, and moving scheduled jobs off host-level cron into a centrally managed scheduler that isn't tied to any single host's provisioning template.
