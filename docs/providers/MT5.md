# MetaTrader5Provider — optional terminal-local read-only adapter

Run the dedicated Python worker on Windows where an authenticated MT5 terminal and its optional `MetaTrader5` SDK are installed. The SDK is deliberately absent from core Linux/Docker/CI dependencies. API/PostgreSQL may run separately; normalized ProviderFrame is the internal boundary, not an external unauthenticated ingestion endpoint.

Set `ENABLE_MT5_PROVIDER=true`, `MT5_BROKER` to the exact terminal account server, and timezone-aware `MT5_CANONICAL_ORIGIN` to a real available first candle. Dataset source must be MT5 and market_type REGULAR. Terminal server is checked on reads, so changing accounts to another server cannot silently relabel prices. Authenticate in the terminal; no broker password/token is persisted, returned or logged by this adapter. No order methods exist.

Historical bootstrap uses UTC `copy_rates_range`; missing configured origin or an exceeded source cap fails closed as insufficient history. Never seed recursive indicators from an arbitrary short trailing window. Closed and forming are separated by close timestamp. Payout is unsupported. Terminal connectivity is available; authoritative broker clock and authoritative market-open status are not, so local UTC is explicitly a proxy and delta/market status remain unavailable.

Official reference: [MT5 copy_rates_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py), including UTC and terminal history limits.

Optional smoke: configure terminal/server/origin and dataset, enable worker, create a dataset-compatible validated item (or explicitly labelled research item), verify bootstrap/closed/forming/health and source identity. Record terminal/build/server/symbol/timeframe and UTC timestamps without credentials. Real smoke NOT RUN in automated acceptance; fake read-only SDK tests cover isolation, Decimal conversion, UTC, terminal state and missing origin. No claim of broker execution realism.

Single-node ownership: do not run a Compose worker and terminal worker against the same PostgreSQL simultaneously. The database advisory singleton lock admits one owner. Distributed provider sidecars and broker-specific session calendars are future scope.
