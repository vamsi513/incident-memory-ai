# Order Processing Queue Consumer Lag

## Summary
A stuck consumer group caused the order-processing message queue to back up for over two hours, delaying order confirmation emails and warehouse fulfillment triggers.

## Impact
Customers placed orders successfully, but confirmation emails and the downstream fulfillment trigger were delayed by up to 2 hours and 15 minutes. No orders were lost — messages remained in the queue — but customer support received a spike in "where is my order confirmation" tickets.

## Root Cause
One consumer in the order-processing consumer group entered an infinite retry loop on a single malformed message (a payload with a null customer_id from an edge case in the checkout service). Because the consumer never acknowledged the message, it kept redelivering to the same partition, and the consumer's retry backoff blocked it from picking up any subsequent messages on that partition. Other partitions were unaffected, but the affected partition handled roughly 40 percent of order volume.

## Mitigation
The on-call engineer identified the stuck partition via consumer lag metrics, manually moved the malformed message to a dead-letter queue, and restarted the consumer. Lag drained within 20 minutes once the blocking message was removed.

## Follow-up Actions
- Add schema validation at the producer side to reject null customer_id before it reaches the queue
- Add a per-partition lag alert, not just aggregate consumer-group lag
- Add a max-retry limit with automatic dead-lettering instead of infinite retry
