# CDN and Caching Architecture

## Services
Static assets and select cacheable pages (product listings, the pricing page) are served through a CDN in front of the origin servers. The deploy pipeline calls the CDN's purge API for a fixed list of paths as part of releasing changes to cached pages.

## Failure Modes
The most common failure mode is stale content: if a page's path changes or the purge step's target list falls out of sync with actual routing, the CDN continues serving pre-update content until the cache entry's TTL naturally expires, which can be hours depending on the path's configured TTL.

## Mitigations
Mitigations include deriving the purge step's path list from the live routing configuration rather than a hardcoded list, and a post-deploy check that compares CDN edge responses against origin responses for key pages to catch staleness immediately after a release rather than waiting for a user report.
