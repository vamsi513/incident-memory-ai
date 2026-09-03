# Outbound TLS Certificate Expiry

## Summary
An expired client TLS certificate caused all outbound calls to the payment processor to fail with handshake errors for 34 minutes.

## Impact
Every outbound request from the payment service to the external payment processor failed with a TLS handshake error. Inbound traffic and all other services were unaffected. Approximately 2,800 payment attempts failed during the window and were queued for retry.

## Root Cause
The client certificate used to authenticate the payment service to the processor's mutual-TLS endpoint expired at 03:00 UTC. The certificate rotation job that normally renews this certificate 30 days before expiry had been silently failing for two months due to an unrelated permissions change on the secrets store, and no alert existed for rotation-job failures.

## Mitigation
On-call was paged by the processor's own downtime alert rather than an internal one. The team manually generated a new client certificate, uploaded it to the secrets store, and restarted the payment service to pick up the new cert. Handshakes succeeded immediately after restart.

## Follow-up Actions
- Add an alert on certificate rotation job failures, not just certificate expiry
- Add a dashboard panel showing days-until-expiry for all mTLS client certificates
- Fix the secrets store permissions that broke the rotation job
