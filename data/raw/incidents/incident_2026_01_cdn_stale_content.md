# CDN Stale Content After Deploy

## Summary
A product-pricing update did not take effect for most users for over three hours because the CDN continued serving a stale cached version of the pricing page.

## Impact
Roughly 70 percent of pricing-page requests, based on edge-cache hit-rate metrics, served prices that had already been superseded by a promotional update. No incorrect checkout charges occurred, since checkout re-validates price server-side, but customer support received a spike of confused-pricing tickets.

## Root Cause
The deploy pipeline's cache-invalidation step calls the CDN's purge API for a fixed list of URL paths, but the pricing page had recently been moved to a new path as part of an unrelated refactor. The purge step still targeted the old path, so the new path's cached copies were never invalidated and continued serving the pre-promotion content until their normal TTL (4 hours) expired.

## Mitigation
On-call manually triggered a full-path cache purge via the CDN dashboard once the discrepancy was reported, which cleared the stale content within minutes.

## Follow-up Actions
- Derive the purge step's path list from the routing config at deploy time instead of a hardcoded list
- Add a post-deploy check that fetches the CDN edge response and diffs it against the origin response for key pages
- Reduce the pricing page's cache TTL
