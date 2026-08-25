# Cache Stampede After Redis Restart

## Summary
A planned Redis maintenance restart triggered a cache stampede that overwhelmed the primary database for 11 minutes.

## Impact
Database CPU peaked at 98 percent and query latency rose from a baseline of 15 ms to over 3,000 ms. Error rates on product listing and search endpoints reached 22 percent.

## Root Cause
When Redis was restarted for a planned memory configuration change, all cached keys were evicted simultaneously. The application had no cache-aside protection: every request that missed the empty cache immediately issued a database query. With 40,000 active users, this produced a thundering herd of concurrent reads against the primary database that exceeded its query throughput capacity.

## Mitigation
The on-call engineer temporarily reduced the upstream request rate via the API gateway rate limiter, giving the database time to recover. Redis was confirmed healthy and keys began repopulating from application traffic. The rate limit was lifted once database latency returned to baseline.

## Follow-up Actions
- Implement cache warming script to pre-populate critical keys before planned restarts
- Add probabilistic early expiration to prevent synchronized key expiry
- Add alert on Redis keyspace drop greater than 50 percent within 60 seconds
