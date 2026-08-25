# User Service Memory Leak Incident

## Summary
The user service experienced repeated OOM restarts over a 45-minute window, causing intermittent 503 errors for authenticated endpoints.

## Impact
Approximately 12 percent of requests to authenticated endpoints returned 503 for 45 minutes. Session lookups and profile fetches were most affected.

## Root Cause
A pull request introduced an unbounded in-memory cache for session tokens. The cache had no eviction policy, causing heap memory to grow until the container hit its 512 MB limit and was killed by the OOM killer. Each restart temporarily cleared the heap, producing a sawtooth pattern in memory metrics.

## Mitigation
The on-call engineer identified the memory growth pattern in container metrics, traced it to the session cache via heap profiling, and deployed a hotfix that replaced the unbounded map with an LRU cache capped at 10,000 entries. Restarts stopped within two minutes of the hotfix deploy.

## Follow-up Actions
- Add memory usage alert at 80 percent of container limit
- Enforce eviction policy review in code review checklist
- Add heap profiling to staging load test suite
