# Search Indexing Lag Hid New Products

## Summary
Newly published products did not appear in search results for up to 4 hours due to a backlog in the search indexing pipeline, though they were visible via direct product-page links.

## Impact
Merchandising teams reported that newly launched products were getting far less search traffic than expected during the affected window; several time-limited promotional launches lost most of their intended visibility.

## Root Cause
The search indexing pipeline consumes a stream of product-change events and indexes them asynchronously. A downstream schema change to the product-change event added a new required field, and the indexer's event parser rejected every event missing that field -- which was every event during the rollout window, since producers and the indexer were deployed at different times. Rejected events were dropped rather than retried, so the indexer fell further behind until the parser was fixed.

## Mitigation
On-call identified the parsing errors in the indexer's logs, deployed a fix that treated the new field as optional with a default, and manually re-ran indexing for products published during the affected window using the product catalog as the source of truth.

## Follow-up Actions
- Make the indexer's event parser tolerant of new optional fields by default (ignore unknown fields, default missing ones) instead of rejecting the whole event
- Route rejected events to a dead-letter queue for reprocessing instead of dropping them
- Coordinate schema changes to the product-change event across producers and consumers with a compatibility check in CI
