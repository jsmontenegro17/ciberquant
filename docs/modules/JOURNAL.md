# Journal
Purpose: qualitative trading notes. Table: `journal_entries`; API `GET/POST /api/v1/journal`. Ownership is user scoped; entries can relate to sessions/trades. Frontend journal is chronological; rich search pending.

REQ-002 validates ownership of both relations and rejects a trade/session mismatch. A trade-linked note inherits the trade's session when omitted. No duplicate note subsystem or new journal table was introduced. Date/session/trade filters run on the user-scoped chronological list in the frontend. Session notes can be added before or after closure, refresh immediately, and survive reload. Rich text/search and pagination are future enhancements.
