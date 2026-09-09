# Search Indexing Lag Runbook

## Symptoms
- Newly published or updated products don't appear in search results, though they load correctly via direct link
- Search indexing lag metric (time between product-change event and index update) rises above normal baseline
- Indexer logs show a rising rate of parse or validation errors on incoming events

## Immediate Checks
- Check the search indexing pipeline's consumer lag against the product-change event stream
- Check the indexer's logs for parse errors, and note whether they correlate with a recent schema change to the event
- Confirm producers and the indexer are running compatible versions of the event schema
- Spot-check a few recently published products directly in the search index to confirm the scope of the lag

## Mitigation Steps
- If a schema mismatch is the cause: deploy a fix to the indexer to tolerate the new field, or roll back the producer change, whichever is faster
- Manually re-index affected products using the product catalog as the source of truth once the underlying cause is fixed
- If events were dropped rather than dead-lettered, identify the affected time window from logs and replay from the catalog rather than the event stream

## Escalation
- Escalate to the team owning the product-change event schema if repeated indexer breakage traces back to uncoordinated schema changes
- Escalate to merchandising if a live promotional launch is affected, so they can extend or adjust the promotion
