# Payment Provider Rate Limit Incident

## Summary
The payment service began receiving HTTP 429 responses from the third-party payment provider during a promotional flash sale, causing checkout failures for a subset of users.

## Impact
Roughly 8 percent of checkout attempts failed with payment errors for 31 minutes. Revenue impact was estimated at approximately $14,000 during the window.

## Root Cause
The flash sale generated a 6x spike in payment authorization requests. The payment service had no per-second throttle and submitted requests to the provider at the raw rate they arrived. The provider enforced a rate limit of 200 requests per second; the service was peaking at approximately 1,100 per second. Requests above the limit were rejected with 429 responses that the service surfaced to users as checkout errors.

## Mitigation
The on-call team added a token bucket rate limiter in the payment service capped at 180 requests per second and introduced a retry queue for rejected requests. Within 10 minutes, the error rate dropped to zero.

## Follow-up Actions
- Implement retry queue with exponential backoff for 429 responses
- Add alerting on payment provider HTTP 4xx rate
- Coordinate capacity increase with provider before future promotions
