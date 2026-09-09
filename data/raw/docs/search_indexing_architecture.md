# Search Indexing Architecture

## Services
The search index is kept up to date by an asynchronous indexing pipeline that consumes a stream of product-change events (created, updated, price changed, delisted) and applies them to the search index. This is decoupled from the product catalog's own database so search can scale and be queried independently.

## Failure Modes
The main failure mode is indexing lag: if the indexer falls behind (due to a schema mismatch with producers, a backlog, or an outage), newly published or updated products don't appear in search even though they exist correctly in the catalog and are reachable by direct link. A stricter risk is event rejection due to schema incompatibility, which can silently drop updates rather than merely delaying them if rejected events aren't captured for reprocessing.

## Mitigations
Mitigations include making the indexer's event parser tolerant of new or missing optional fields rather than rejecting the whole event, routing rejected events to a dead-letter queue for reprocessing instead of dropping them, and a compatibility check in CI for changes to the product-change event schema shared between producers and the indexer.
