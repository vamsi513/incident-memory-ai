# Search Latency Incident

## Summary
Search API latency spiked after a cache invalidation bug.

## Impact
p95 latency rose from 220 ms to 2400 ms for 17 minutes.

## Root Cause
A cache invalidation job cleared hot keys too aggressively, causing repeated database reads.

## Mitigation
The team disabled the invalidation worker and restored cached key warmup.

## Follow-up Actions
- Add rate limits to invalidation worker
- Add monitoring for cache hit ratio

