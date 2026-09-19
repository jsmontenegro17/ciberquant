# IQ Option — EXPERIMENTAL / DISABLED

`ENABLE_IQOPTION_EXPERIMENTAL=false` by default. The isolated contract adapter intentionally reports PROVIDER UNAVAILABLE even if enabled: no unverified unofficial SDK, authentication flow or trading surface is included. All capabilities are false. No credentials needed in repository, database, browser, logs or CI.

REGULAR and OTC remain distinct dataset identities. No MT5 substitution is permitted. Failure is isolated by subscription and does not stop Replay or other providers. External smoke NOT RUN / unavailable; this is explicitly allowed by REQ-007, not evidence of a working IQ connection.

Actual IQ OTC before v1.0, if required by product acceptance, is a **conditional v1.0 blocker** for a separately authorized REQ-008 decision. This document records the dependency, does not start REQ-008 or declare external connectivity complete.
