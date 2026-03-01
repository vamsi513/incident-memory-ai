# Database Latency Runbook

## Symptoms
- Elevated p95 latency
- Increased timeout rate
- Connection pool saturation

## Immediate Checks
- Check database CPU
- Check active connections
- Check recent deploys

## Mitigation Steps
- Roll back recent deploys
- Increase connection pool size temporarily
- Shift read traffic to replicas if available

## Escalation
- Escalate to database owner if saturation persists for more than 10 minutes

