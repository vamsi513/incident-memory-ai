# Nightly Reconciliation Job Silent Failure

## Summary
The nightly job that reconciles inventory counts between the warehouse system and the storefront silently stopped running for eight days without anyone noticing, causing storefront inventory to drift from actual stock.

## Impact
By the time the drift was noticed, roughly 3 percent of listed products showed as in-stock when they were actually sold out, leading to a backlog of orders that had to be manually canceled and refunded.

## Root Cause
The reconciliation job was scheduled via a cron entry on a host that was replaced during a routine infrastructure migration. The new host's cron configuration was provisioned from an older template that predated the reconciliation job's addition, so the job was never scheduled on the new host. Because the job had no independent "last successful run" monitoring, nothing detected that it had stopped running.

## Mitigation
Once discovered via a customer-reported out-of-stock order, the job was manually re-added to the new host's cron configuration and run immediately to correct the drift. Affected orders were identified by comparing timestamps and manually processed.

## Follow-up Actions
- Add a dead-man's-switch alert that fires if the reconciliation job has not reported success within 26 hours
- Move scheduled jobs out of host-level cron and into a centrally managed scheduler that isn't tied to a specific host's provisioning template
- Audit all other cron-based jobs for the same host-migration exposure
