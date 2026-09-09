# CDN Stale Content Runbook

## Symptoms
- Users report seeing outdated prices, copy, or images after a known deploy or content update
- CDN edge cache hit ratio remains high for a path that was just changed
- Origin server returns updated content when queried directly, but the public URL still returns old content

## Immediate Checks
- Fetch the affected URL directly against the origin, bypassing the CDN, and confirm it shows the updated content
- Fetch the same URL through the CDN and compare response headers for cache-status and age
- Check whether the deploy's cache-purge step actually ran and which paths it targeted
- Confirm the affected path matches what the purge step targeted (watch for recent path or route changes)

## Mitigation Steps
- Manually trigger a full-path purge for the affected URL(s) via the CDN dashboard or purge API
- If the purge step's path list is stale, update it to match the current routing before the next deploy
- For urgent cases, temporarily lower the affected path's cache TTL to force faster natural expiry

## Escalation
- Escalate to the CDN provider if a manual purge request does not clear stale content within 15 minutes
- Escalate to the platform team if this is the second stale-content incident tied to the same deploy pipeline step within 30 days
