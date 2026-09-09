# Duplicate Order Processing After Consumer Restart

## Summary
A restart of the order-processing consumer during a deployment caused roughly 200 orders to be processed twice, resulting in duplicate fulfillment triggers and, for a subset of orders, duplicate charges.

## Impact
About 200 orders had duplicate fulfillment requests sent to the warehouse system, and 45 of those also resulted in a duplicate charge to the customer's payment method, since charge deduplication relied on the same processing step that ran twice.

## Root Cause
The order-processing consumer reads messages from a queue and commits its read offset only after fully processing a batch, not after each message. During a deployment, the consumer was restarted mid-batch; because the offset for that batch had not yet been committed, the new consumer instance re-read and reprocessed the entire batch, including messages that had already been fully processed (and charged) by the old instance before it was killed.

## Mitigation
On-call identified the duplicate charges via a spike in payment-provider refund requests from customers, cross-referenced order IDs against the payment provider's transaction log to find all duplicates, and issued refunds for the 45 duplicate charges. Duplicate fulfillment requests were caught and canceled at the warehouse system before shipment in all but 3 cases, which were handled as return requests.

## Follow-up Actions
- Make order processing idempotent per order ID (check-then-process against a processed-orders table) rather than relying solely on queue offset commits
- Commit queue offsets per-message or in smaller batches to shrink the reprocessing window on restart
- Add a reconciliation check that flags any order ID processed more than once
