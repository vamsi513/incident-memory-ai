# Scheduled Job Failure Runbook

## Symptoms
- Data that depends on a nightly or periodic job looks stale or drifted (e.g. inventory counts, reconciliation reports)
- No recent "job completed successfully" log entry or metric for the expected schedule
- Downstream systems that consume the job's output are operating on outdated data

## Immediate Checks
- Check the job scheduler (cron, workflow orchestrator) for the job's last recorded run time and exit status
- Confirm the job is still actually scheduled on the expected host or scheduler instance, especially after any recent infrastructure migration
- Check the job's logs for the most recent run, successful or not
- Compare the job's expected schedule against its actual run history to see how long it has been missing

## Mitigation Steps
- If the job is missing from the scheduler: re-add it and trigger an immediate manual run
- If the job ran but failed: review the failure logs, fix the underlying issue, and re-run manually
- After a manual run, reconcile any data drift that accumulated while the job was not running
- Confirm the job's next scheduled run occurs as expected before closing out

## Escalation
- Escalate to the team that owns the affected downstream data if drift has led to customer-visible incorrect information
- Escalate to infrastructure if the job's absence traces back to a host or scheduler migration, so other jobs can be audited for the same gap
