# Log Volume Disk Space Exhaustion

## Summary
Unrotated debug logging filled the search service's local disk, causing the service to crash-loop for 40 minutes.

## Impact
The search service became unavailable, returning connection errors for all search queries. Other services that depend on search results (product listing pages, the checkout recommendation widget) degraded to showing cached or empty results rather than failing outright.

## Root Cause
A debug logging flag had been left enabled after a prior investigation and was never reverted. Debug-level logs, including full request and response bodies, accumulated at roughly 4 GB per hour. Log rotation was configured but had a bug that skipped rotation when the log file exceeded a certain size threshold, so the file grew unbounded until the disk filled completely and the process crashed on write failure, then crash-looped on restart since the disk stayed full.

## Mitigation
On-call identified the full disk via host metrics, manually truncated the oversized log file, disabled the debug logging flag, and restarted the service. Search availability recovered immediately after restart.

## Follow-up Actions
- Fix the log rotation bug that skips rotation above a certain file size
- Add an alert on disk usage above 85 percent, not just service-level error rate
- Add an automatic expiry on debug logging flags so they cannot be left on indefinitely
