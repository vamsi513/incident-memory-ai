# Internal DNS Resolution Failure

## Summary
An internal DNS misconfiguration caused service-to-service calls to fail across the production cluster for 19 minutes.

## Impact
All inter-service HTTP calls relying on internal service names failed with connection refused or name resolution errors. Public traffic served by cached routes was unaffected, but any request requiring a live service call returned 502.

## Root Cause
A routine infrastructure change updated the internal DNS search domain in the cluster config. The new value contained a trailing dot that caused the resolver to misformat fully-qualified names. Internal hostnames such as user-service.internal resolved to user-service.internal.. (with a double dot), which returned NXDOMAIN. Services using IP-based routing were unaffected.

## Mitigation
The infrastructure team identified the malformed search domain by reproducing the resolution failure with nslookup inside a pod. The trailing dot was removed and the CoreDNS deployment was rolled. All services resumed normal name resolution within 90 seconds of the rollout.

## Follow-up Actions
- Add DNS resolution smoke test to post-deploy validation suite
- Lint cluster config changes for trailing dot in domain fields
- Add alert on elevated NXDOMAIN rate in CoreDNS metrics
