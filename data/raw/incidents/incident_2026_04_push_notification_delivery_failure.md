# Push Notification Delivery Failure After Certificate Rotation

## Summary
Push notifications to mobile devices stopped being delivered for 6 hours after the certificate used to authenticate with the push notification provider expired and its automated rotation failed silently.

## Impact
Order-status and shipping-update push notifications were not delivered to any mobile app user during the window. No data was lost -- notifications remained queued and were delivered once the certificate was fixed -- but several thousand users received delayed shipping updates.

## Root Cause
The push certificate's automated renewal job depends on an API call to the provider that had recently added a required additional authentication header. The renewal job was not updated for this change, so its renewal calls began failing with an authentication error. The job logged the failure but did not alert anyone, and the old certificate continued working right up until its expiry, at which point delivery stopped abruptly.

## Mitigation
On-call noticed the delivery failure via a drop in the notification-sent metric, identified the expired certificate, manually renewed it through the provider's dashboard, and confirmed delivery resumed. Queued notifications were flushed successfully once the certificate was valid again.

## Follow-up Actions
- Alert on push certificate renewal failures, not just on expiry
- Add a dashboard panel showing days until push certificate expiry
- Add an end-to-end synthetic push notification test that runs hourly and alerts on failure
