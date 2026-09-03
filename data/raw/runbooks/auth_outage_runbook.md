# Auth Outage Runbook

## Symptoms
- Spike in login failures with no corresponding change to internal auth service error rate
- Password reset requests failing
- New user sign-ups failing while existing sessions remain valid
- Elevated error rate specifically on OAuth token-issuance calls

## Immediate Checks
- Check the external identity provider's public status page for a known outage
- Check auth service logs for timeouts or errors specifically on calls to the external provider
- Confirm whether existing authenticated sessions are still functioning normally
- Check auth service error rate broken down by internal errors versus upstream provider errors

## Mitigation Steps
- If the external identity provider is down: post a status banner informing users of the outage and estimated impact
- Confirm there is no viable internal fallback for new logins during a provider outage
- Monitor the provider's status page for recovery and confirm login success rate returns to baseline once resolved
- Do not restart the auth service if the root cause is confirmed external — a restart will not resolve provider-side outages

## Escalation
- Escalate to the identity provider's support channel if the outage exceeds 30 minutes with no public acknowledgement
- Escalate internally to product/support teams to coordinate customer communication for outages longer than 15 minutes
