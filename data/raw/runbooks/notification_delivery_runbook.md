# Notification Delivery Runbook

## Symptoms
- Push notification or email sent count drops sharply while the triggering events (orders, shipping updates) continue at normal volume
- Users report not receiving expected notifications
- Notification queue depth grows without draining

## Immediate Checks
- Check the notification queue depth and drain rate in metrics
- Check for authentication or certificate errors in the notification provider's client logs
- Confirm the provider's own status page doesn't show an ongoing outage on their end
- Check certificate or API-key expiry dates for the notification provider integration

## Mitigation Steps
- If a certificate or credential has expired: renew it through the provider's dashboard and confirm delivery resumes
- If the provider is down: confirm notifications are queuing rather than being dropped, so they can be delivered once the provider recovers
- If the queue is draining slower than it fills: temporarily increase worker concurrency for the notification consumer
- Manually verify a sample of queued notifications are delivered correctly before considering the incident resolved

## Escalation
- Escalate to the notification provider's support channel if an outage on their end exceeds 30 minutes
- Escalate internally if queued notifications risk becoming stale or irrelevant (e.g. time-sensitive shipping updates) before they can be delivered
