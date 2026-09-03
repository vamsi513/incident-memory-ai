# Third-Party Auth Provider Outage

## Summary
An outage at the external identity provider blocked all new user logins for 52 minutes, though already-authenticated sessions were unaffected.

## Impact
Users who were not already logged in could not sign in, sign up, or reset passwords. Existing sessions with a valid, unexpired token continued to work normally since session validation does not call the identity provider on every request. Roughly 15 percent of daily active users attempted to log in during the outage window and were blocked.

## Root Cause
The external identity provider had a regional outage affecting its OAuth token-issuance endpoint. The auth service has no fallback identity provider and no cached credential path for new logins, so every login attempt synchronously depended on that single external endpoint being available.

## Mitigation
The team confirmed the outage via the provider's public status page, communicated the outage to users via a banner, and waited for the provider to recover — there was no internal mitigation available. Logins resumed automatically once the provider's endpoint came back online.

## Follow-up Actions
- Evaluate adding a secondary identity provider for login redundancy
- Add a status-page banner that can be triggered automatically from auth service error rates
- Document the current single point of failure explicitly for future incident response
