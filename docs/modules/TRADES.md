# Trades
Purpose: record execution evidence, never send orders. Table: `trades`; API `/api/v1/trades` and `/api/v1/sessions/{id}/trades`. Rules: payout stored historically and cannot be below the session snapshot minimum; results WIN/LOSS/DRAW/CANCELLED, market_type separates REGULAR/OTC. Ledger records realized P&L.
