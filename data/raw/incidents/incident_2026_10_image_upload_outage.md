# Product Image Upload Outage

## Summary
Sellers were unable to upload new product images for 50 minutes after the image-processing service's storage bucket ran out of available connections.

## Impact
New product listings and image updates to existing listings failed with an upload error during the window. Existing product images already live on the storefront were unaffected, since they are served from a separate read path.

## Root Cause
The image-processing service opens a new connection to the storage bucket for each upload rather than reusing a connection pool. A batch re-processing job that re-generates thumbnail sizes for older images was running concurrently with normal upload traffic and, combined, the two exceeded the storage provider's per-account connection limit, causing new connection attempts (including normal seller uploads) to be rejected.

## Mitigation
On-call identified the batch job as the concurrent load source, paused it, and connections recovered within a few minutes as existing ones were released. The batch job was rescheduled to run overnight instead.

## Follow-up Actions
- Migrate the image-processing service to use a shared, bounded connection pool instead of opening a new connection per upload
- Cap the batch re-processing job's concurrency so it cannot approach the account-wide connection limit on its own
- Add alerting on storage-provider connection rejection errors specifically, not just generic upload failure rate
