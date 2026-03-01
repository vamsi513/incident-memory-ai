# Checkout Timeout Incident

## Summary
Users experienced elevated checkout timeout errors.

## Impact
Checkout success rate dropped by 18 percent for 22 minutes.

## Root Cause
A deployment changed database connection pool behavior, causing saturation.

## Mitigation
The on-call engineer rolled back the deployment and increased connection pool size.

## Follow-up Actions
- Add load test for connection pool saturation
- Add alert on pool exhaustion

