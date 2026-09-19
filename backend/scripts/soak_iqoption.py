"""Authorized local real PRACTICE-only multi-close/reconnect test; never run in CI."""

from .smoke_iqoption import main

if __name__ == "__main__":
    raise SystemExit(main(soak=True))
