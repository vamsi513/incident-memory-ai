# Checkout Architecture

## Services
The checkout flow depends on the API gateway, checkout service, payment service, and PostgreSQL database.

## Failure Modes
Common failure modes include connection pool saturation, downstream payment timeout, and slow database queries.

## Mitigations
Mitigations include rollback, traffic shaping, and increasing temporary connection pool limits.

