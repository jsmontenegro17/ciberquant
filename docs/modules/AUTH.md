# Auth
Purpose: autenticación segura multiusuario. Responsibilities: login/logout/current user, JWT HttpOnly. Non-responsibilities: autorización de dominio. Entities: User. API: `/api/v1/auth/*`. Rules: passwords hashed, secrets env, inactive users denied. Tests: `backend/tests` and API checks. Limitations: refresh token rotation pending.
