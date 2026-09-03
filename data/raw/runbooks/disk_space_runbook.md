# Disk Space Runbook

## Symptoms
- Service crash-looping with write-failure errors in logs
- Disk usage alert above 85 percent on a host
- Log rotation appears stalled or absent
- Sudden inability to write temp files or upload buffers

## Immediate Checks
- Check disk usage on the affected host: df -h
- Identify the largest directories consuming space: du -sh /var/log/* or equivalent
- Check whether log rotation is running and whether any log file exceeds its expected rotation threshold
- Check for any debug or verbose logging flags left enabled

## Mitigation Steps
- If a single oversized log file is the cause, truncate or compress it to free immediate space
- Disable any debug logging flags contributing to excessive log volume
- Manually trigger log rotation if the scheduled job appears stuck
- Restart the affected service once sufficient disk space is confirmed available

## Escalation
- Escalate to infrastructure team if disk usage cannot be reduced below 85 percent within 15 minutes
- Escalate to the owning service team if the root cause is unclear after initial checks
