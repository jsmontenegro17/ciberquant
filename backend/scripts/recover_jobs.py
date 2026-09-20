"""One-shot operator maintenance; requires drained pre-REQ008 processes. No scheduler."""
import argparse
import json
from app.db import engine
from app.operations import recover


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["import", "backtest", "validation"])
    parser.add_argument("--minimum-age-seconds", type=int, default=300)
    args = parser.parse_args()
    print(json.dumps(recover(engine, args.kind, args.minimum_age_seconds)))


if __name__ == "__main__":
    main()
