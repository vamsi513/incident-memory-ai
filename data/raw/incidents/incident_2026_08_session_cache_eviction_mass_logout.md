# Session Cache Eviction Caused Mass Logout

## Summary
A memory-pressure event on the session cache caused it to evict a large fraction of active sessions at once, logging out an estimated 40 percent of active users simultaneously.

## Impact
Affected users were redirected to the login page mid-session and had to sign in again. Any in-progress checkout or form submission for those users was lost. No payment or data corruption occurred, but the sudden spike in login traffic itself briefly elevated login latency for all users, including those not affected by the original eviction.

## Root Cause
Session data is stored in an in-memory cache with a fixed memory limit and an eviction policy that removes the least-recently-used entries once the limit is reached. A marketing campaign drove an unusually large traffic spike, and the resulting spike in new sessions pushed the cache past its memory limit, triggering mass eviction of older (but still active) sessions rather than just the campaign's new short-lived ones, because session recency was tracked by creation time rather than last-access time.

## Mitigation
On-call increased the session cache's memory limit as an immediate mitigation once the pattern was identified, which stopped further mass evictions. Affected users were not individually notified, since re-login was the only user-visible effect and no data was lost beyond in-progress form state.

## Follow-up Actions
- Switch the eviction policy to track last-access time rather than creation time, so active sessions are protected from eviction regardless of age
- Add capacity alerting on session cache memory usage well before the eviction threshold
- Load-test the session cache against traffic patterns matching a marketing campaign spike, not just steady-state traffic
