# API Gateway Routing Config Change Sent Traffic to Wrong Backend

## Summary
A routing configuration change intended to add a new API path instead altered an existing path's routing rule, sending roughly 15 percent of search-API traffic to the recommendations service backend for 12 minutes.

## Impact
Requests to the search API that were misrouted received recommendation results instead of search results, or a 404 if the recommendations service didn't recognize the request shape at all. Overall search error rate rose during the window; recommendations-service load also increased unexpectedly, though it stayed within capacity.

## Root Cause
The gateway's routing rules are matched by longest-prefix match. The new path added for a recommendations feature used a prefix that, due to a trailing-slash inconsistency, unintentionally matched a broader set of URLs than intended, overlapping with an existing search-API path pattern and taking priority over it because it was defined later in the rule list, which the gateway treats as higher priority on ties.

## Mitigation
On-call identified the misrouted traffic via the search API's error-rate dashboard, correlated it with the recent routing change, and reverted the change, restoring correct routing within a few minutes.

## Follow-up Actions
- Add a routing-rule validation step in CI that checks for prefix overlaps against all existing rules before a change is allowed to merge
- Normalize trailing slashes before prefix matching in the gateway
- Add a canary step for routing changes that sends a small percentage of traffic through the new rule before a full rollout
