# Load Balancer Weight Misconfiguration

## Summary
A configuration change sent 90 percent of production traffic to a single backend instance, causing widespread 503 errors during a routine deployment.

## Impact
For 11 minutes, the overloaded instance returned 503 Service Unavailable for roughly 60 percent of requests it received, while the remaining healthy instances sat mostly idle. Overall error rate across the fleet peaked at 22 percent.

## Root Cause
A deployment script intended to update health-check paths on all backend instances instead applied a weight override meant for a canary test to the full instance pool, setting one instance's traffic weight to 90 and leaving the rest at their canary-test values of 2 to 3. The load balancer honored the weights exactly as configured and routed traffic accordingly, overwhelming the single instance.

## Mitigation
The on-call engineer noticed the traffic skew in the load balancer dashboard, identified the erroneous weight configuration, and reverted it to equal weighting across all instances. Error rate returned to baseline within 90 seconds of the revert.

## Follow-up Actions
- Separate canary-weight configuration from the general deployment script so they cannot be applied together by mistake
- Add an alert on traffic-weight imbalance across a backend pool
- Require a manual approval step for any load balancer weight change outside of the standard canary rollout tool
