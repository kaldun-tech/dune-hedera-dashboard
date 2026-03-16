"""Fetch transactions from Hedera Mirror Node API."""

import time
import json
from datetime import datetime, timedelta
from typing import Iterator

import requests
from tqdm import tqdm

from config import (
    HEDERA_MIRROR_URL,
    DAYS_TO_FETCH,
    DATA_DIR,
    REQUESTS_PER_SECOND,
    REQUEST_TIMEOUT,
)


def get_timestamp_range(days: int) -> tuple[str, str]:
    """Get timestamp range for the last N days."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    # Hedera timestamps are in seconds.nanoseconds format
    return (
        f"{int(start.timestamp())}.000000000",
        f"{int(end.timestamp())}.000000000",
    )


def fetch_transactions_page(
    timestamp_start: str,
    timestamp_end: str,
    next_link: str | None = None,
) -> dict:
    """Fetch a single page of transactions."""
    if next_link:
        url = f"{HEDERA_MIRROR_URL}{next_link}"
    else:
        url = (
            f"{HEDERA_MIRROR_URL}/api/v1/transactions"
            f"?timestamp=gte:{timestamp_start}"
            f"&timestamp=lte:{timestamp_end}"
            f"&limit=100"
            f"&order=asc"
        )

    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_all_transactions(days: int = DAYS_TO_FETCH) -> Iterator[dict]:
    """
    Fetch all transactions for the specified period.

    Yields individual transaction records.
    """
    timestamp_start, timestamp_end = get_timestamp_range(days)
    print(f"Fetching transactions from {timestamp_start} to {timestamp_end}")

    next_link = None
    page_count = 0
    tx_count = 0
    delay = 1.0 / REQUESTS_PER_SECOND

    with tqdm(desc="Fetching transactions", unit=" pages") as pbar:
        while True:
            try:
                data = fetch_transactions_page(
                    timestamp_start, timestamp_end, next_link
                )
            except requests.RequestException as e:
                print(f"Error fetching page {page_count}: {e}")
                time.sleep(5)  # Back off on error
                continue

            transactions = data.get("transactions", [])
            for tx in transactions:
                yield tx
                tx_count += 1

            page_count += 1
            pbar.update(1)
            pbar.set_postfix({"transactions": tx_count})

            # Check for next page
            links = data.get("links", {})
            next_link = links.get("next")
            if not next_link:
                break

            time.sleep(delay)

    print(f"Fetched {tx_count} transactions across {page_count} pages")


def save_transactions_raw(output_file: str = "transactions_raw.jsonl"):
    """Save raw transactions to JSONL file."""
    output_path = f"{DATA_DIR}/{output_file}"

    with open(output_path, "w") as f:
        for tx in fetch_all_transactions():
            f.write(json.dumps(tx) + "\n")

    print(f"Saved raw transactions to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch Hedera transactions")
    parser.add_argument(
        "--days", type=int, default=DAYS_TO_FETCH,
        help=f"Number of days to fetch (default: {DAYS_TO_FETCH})"
    )
    parser.add_argument(
        "--output", type=str, default="transactions_raw.jsonl",
        help="Output filename"
    )
    args = parser.parse_args()

    # Update days if specified
    if args.days != DAYS_TO_FETCH:
        print(f"Fetching {args.days} days of data")

    save_transactions_raw(args.output)
