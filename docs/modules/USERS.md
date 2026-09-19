# Users
Purpose: identidad y ownership. Tables: `users`, `risk_profiles`; roles ADMIN/USER, status ACTIVE. Seed creates a configurable admin, demo account and 1%/2%/4/80% risk profile. Services: auth dependency. Invariant: every financial query filters user_id. Related: REQ-001.
