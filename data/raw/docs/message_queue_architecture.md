# Message Queue Architecture

## Services
Order processing depends on a message queue between the checkout service, which publishes order-created events, and a pool of consumers in the order-processing service that handle fulfillment, confirmation emails, and inventory updates.

## Failure Modes
Common failure modes include a stuck consumer blocking its partition on a malformed or unprocessable message, consumer group lag building up under high order volume, and producer-side schema drift sending payloads consumers cannot handle.

## Mitigations
Mitigations include dead-lettering messages that exceed a retry limit instead of retrying indefinitely, per-partition lag alerting, and schema validation at the producer to reject malformed payloads before they reach the queue.
