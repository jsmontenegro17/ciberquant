# SEC-001 — Production authentication configuration

Status: BACKLOG
Recorded: 2026-09-19
Origin: REQ-002 final human acceptance
Blocking REQ-002: NO
Required before: production deployment

## Current local-development behavior

Authentication uses an HttpOnly cookie with `secure=False`. CORS allows `http://localhost:5173`. These settings are correct for the supported local-development environment; production hardening is not claimed.

## Future requirement

Introduce validated, environment-aware `COOKIE_SECURE`, `COOKIE_SAMESITE` and `ALLOWED_ORIGINS` configuration. Require HTTPS in production and secure authentication cookies. Validate SameSite/origin combinations against the deployment topology without weakening CSRF protections. Keep explicit allowed origins when credentials are enabled; preserve the documented local development workflow.

## Acceptance evidence required

- Tests cover development and production cookie attributes, configuration validation and credentialed CORS allow/reject behavior.
- Production refuses insecure configuration and enforces HTTPS, including documented reverse-proxy handling where applicable.
- Login, logout and authenticated browser requests pass over HTTPS in the production topology.
- Deployment documentation explains required environment values and verification.

No implementation is included in REQ-002. This debt is not a functional P0/P1 or a blocker for its accepted local-development scope; it must be addressed before production.
