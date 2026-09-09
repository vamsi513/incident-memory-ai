# Circuit Breaker Misfire Blocked Healthy Traffic

## Summary
A misconfigured circuit breaker on the recommendations-service client tripped during a brief, unrelated network blip and stayed open for 20 minutes, blocking all recommendation requests even after the underlying network issue had fully resolved.

## Impact
The homepage's "recommended for you" section fell back to a generic, non-personalized product list for all users during the window. This is an intended graceful-degradation behavior, so no errors were shown to users, but personalized-recommendation click-through rate dropped to the generic-fallback baseline for 20 minutes.

## Root Cause
The circuit breaker's half-open retry interval, which controls how soon it attempts a test request after tripping to check if the dependency has recovered, was configured to 20 minutes instead of the intended 20 seconds due to a units mismatch when the config was migrated from seconds to a duration-string format during an unrelated refactor. The underlying network blip that originally tripped the breaker resolved within seconds, but the breaker did not attempt to check again until the full 20-minute interval had elapsed.

## Mitigation
On-call noticed the sustained generic-fallback rate on the recommendations dashboard, identified the misconfigured retry interval, and manually reset the circuit breaker to closed, restoring personalized recommendations immediately.

## Follow-up Actions
- Fix the units mismatch in the circuit breaker's retry-interval config and add a unit test asserting the parsed value matches the intended duration
- Add a dashboard panel showing current circuit breaker state (open/half-open/closed) and time-in-state for each protected dependency
- Add an alert for any circuit breaker remaining open longer than its configured retry interval would suggest is expected
