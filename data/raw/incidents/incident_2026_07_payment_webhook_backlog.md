# Payment Provider Webhook Backlog Delayed Order Confirmations

## Summary
A backlog in processing payment-confirmation webhooks from the payment provider delayed order-confirmation emails and order fulfillment triggers by up to 90 minutes.

## Impact
Payments themselves succeeded normally at the provider, but roughly 1,800 orders had their confirmation email and fulfillment-start trigger delayed. Several customers contacted support believing their payment had failed because no confirmation arrived promptly.

## Root Cause
The webhook receiver processes each incoming webhook synchronously, including a call to the internal order service to mark the order as paid. The order service experienced elevated latency during the window due to an unrelated database issue, and because the webhook receiver has no timeout on that internal call, each webhook took far longer to process than normal. Since webhooks were arriving faster than they could be processed under the elevated latency, a backlog built up in the provider's retry queue.

## Mitigation
Once the order service's latency issue was resolved independently, the webhook backlog drained on its own as the provider retried unprocessed webhooks. On-call also manually queried the payment provider's API for a list of confirmed-but-unprocessed payments to confirm no webhooks were permanently lost.

## Follow-up Actions
- Add a timeout on the webhook receiver's call to the order service, queuing the webhook for async processing on timeout rather than blocking
- Decouple webhook receipt from webhook processing entirely using an internal queue
- Add alerting on payment-webhook processing latency, not just on webhook receipt errors
