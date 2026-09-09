# Feature Flag Misconfiguration Exposed Unfinished Checkout Redesign

## Summary
A feature flag intended to enable a new checkout redesign for 1 percent of users was misconfigured and instead enabled it for 100 percent of users, exposing an incomplete UI to the entire customer base for 25 minutes.

## Impact
All users attempting checkout during the window saw the redesigned, unfinished checkout flow, which was missing a working "apply discount code" button. Discount-code usage during the window dropped to zero, and several users abandoned checkout entirely rather than pay full price.

## Root Cause
The feature-flagging system's rollout-percentage field accepts a value from 0 to 100. The engineer configuring the rollout intended to enter "1" for 1 percent but the change was applied through a script that read the value from a config file where a decimal point had been dropped during a prior refactor of that file's format, turning "1.0" into "10" and, due to a separate unit mismatch in the same script, effectively "100" by the time it reached the flagging system.

## Mitigation
On-call noticed the spike in checkout abandonment and discount-code failure metrics, checked the feature flag dashboard, found the rollout percentage was 100 instead of 1, and immediately set it back to 1 percent, restoring the original checkout flow for nearly all users within minutes.

## Follow-up Actions
- Add a confirmation step in the rollout script showing the exact percentage before applying it
- Add a maximum single-step rollout-percentage change limit (e.g. no jump larger than 10 percentage points without explicit override)
- Add alerting on sudden drops in discount-code usage as a proxy for checkout-flow regressions
