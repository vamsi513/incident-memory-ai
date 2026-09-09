# Notification Service Architecture

## Services
The notification service consumes events (order confirmed, order shipped, price drop on a wishlisted item) and delivers push notifications and emails through third-party providers. Notifications are queued internally before delivery so a provider outage doesn't cause events to be lost.

## Failure Modes
Common failure modes include an expired or misconfigured provider credential/certificate causing delivery to fail outright, and provider-side outages or rate limits causing the internal queue to back up. Because delivery is queued rather than synchronous, a backlog shows up as growing queue depth rather than immediate errors, which can delay detection if queue-depth isn't actively monitored.

## Mitigations
Mitigations include certificate/credential expiry monitoring with advance warning, an end-to-end synthetic notification test that runs on a schedule to catch delivery failures proactively, and queue-depth alerting so a backlog is caught before queued notifications become stale or irrelevant.
