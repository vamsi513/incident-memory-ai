# Cache Failure Runbook

## Symptoms
- Sudden spike in database CPU or query latency
- Drop in cache hit ratio below 60 percent
- Elevated error rate on read-heavy endpoints
- Redis keyspace size drops sharply in metrics

## Immediate Checks
- Confirm Redis is reachable: redis-cli ping
- Check cache hit ratio in metrics dashboard
- Check if a Redis restart or flush occurred recently
- Check application logs for repeated cache miss warnings

## Mitigation Steps
- If database is overwhelmed: reduce upstream request rate via API gateway
- If Redis is down: restart Redis and monitor keyspace recovery
- Run cache warming script to pre-populate critical keys if available
- Enable read replica offloading temporarily to reduce primary database load

## Escalation
- Escalate to infrastructure team if Redis cannot be recovered within 10 minutes
- Escalate to database owner if primary database CPU remains above 90 percent for more than 5 minutes
