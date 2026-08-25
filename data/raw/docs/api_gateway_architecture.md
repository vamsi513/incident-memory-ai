# API Gateway Architecture

## Overview
All external traffic enters the system through the API gateway, which handles authentication, rate limiting, and routing to downstream services.

## Downstream Services
The gateway routes to the checkout service, search service, user service, and payment service. Each downstream service is identified by its internal DNS name.

## Rate Limiting
The gateway enforces per-client rate limits. When a downstream service is degraded, the gateway can reduce the upstream request rate to prevent cascading failures.

## Failure Modes
Common failure modes include misconfigured routing rules, upstream service timeouts, and DNS resolution failures for internal service names. When DNS resolution fails, the gateway cannot forward requests and returns 502 to the client.

## Circuit Breaker
The gateway includes a circuit breaker that opens when a downstream service error rate exceeds 50 percent over a 30-second window. Requests to that service are rejected immediately until the circuit resets.
