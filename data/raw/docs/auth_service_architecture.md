# Auth Service Architecture

## Services
The auth service handles session validation for existing users internally, but delegates new login, sign-up, and password-reset flows to an external third-party identity provider via OAuth.

## Failure Modes
Common failure modes include the external identity provider's token-issuance endpoint becoming unavailable, which blocks new logins while leaving existing sessions unaffected since session validation does not depend on the external provider.

## Mitigations
Mitigations include user-facing status communication during a provider outage; there is currently no secondary identity provider or fallback path for new logins, which is a known single point of failure.
