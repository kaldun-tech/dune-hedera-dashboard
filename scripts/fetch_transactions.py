"""Fetch transactions from Hedera Mirror Node API and aggregate on the fly."""

import time
import csv
from collections import defaultdict
from datetime import datetime, timedelta

import requests
from tqdm import tqdm

from config import (
    HEDERA_MIRROR_URL,
    DAYS_TO_FETCH,
    DATA_DIR,
    REQUESTS_PER_SECOND,
    REQUEST_TIMEOUT,
    get_tx_category,
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


def parse_consensus_timestamp(ts: str) -> datetime:
    """Parse Hedera consensus timestamp (seconds.nanoseconds) to datetime."""
    seconds = float(ts.split(".")[0])
    return datetime.utcfromtimestamp(seconds)


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


def fetch_and_aggregate(days: int = DAYS_TO_FETCH, output_file: str = "hedera_daily_stats.csv"):
    """
    Fetch transactions and aggregate into daily stats in a single pass.

    This avoids storing millions of raw transactions - we aggregate on the fly.
    """
    timestamp_start, timestamp_end = get_timestamp_range(days)
    print(f"Fetching transactions from {timestamp_start} to {timestamp_end}")
    print(f"Date range: {days} days")

    # Aggregation state
    daily_stats = defaultdict(lambda: {
        "tx_count": 0,
        "tx_type_crypto": 0,
        "tx_type_hcs": 0,
        "tx_type_token": 0,
        "tx_type_contract": 0,
        "tx_type_other": 0,
        "accounts": set(),
        "total_fees": 0,
        "success_count": 0,
        "failure_count": 0,
    })

    next_link = None
    page_count = 0
    tx_count = 0
    delay = 1.0 / REQUESTS_PER_SECOND
    consecutive_errors = 0
    max_consecutive_errors = 10

    with tqdm(desc="Fetching & aggregating", unit=" pages") as pbar:
        while True:
            try:
                data = fetch_transactions_page(
                    timestamp_start, timestamp_end, next_link
                )
                consecutive_errors = 0  # Reset on success
            except requests.RequestException as e:
                consecutive_errors += 1
                print(f"\nError fetching page {page_count}: {e}")
                if consecutive_errors >= max_consecutive_errors:
                    print(f"Too many consecutive errors ({max_consecutive_errors}), stopping.")
                    break
                time.sleep(5)  # Back off on error
                continue

            transactions = data.get("transactions", [])

            # Aggregate each transaction
            for tx in transactions:
                tx_count += 1

                # Parse date
                ts = tx.get("consensus_timestamp", "")
                if not ts:
                    continue

                dt = parse_consensus_timestamp(ts)
                date_str = dt.strftime("%Y-%m-%d")
                stats = daily_stats[date_str]

                # Count transaction
                stats["tx_count"] += 1

                # Categorize transaction type
                tx_name = tx.get("name", "")
                category = get_tx_category(tx_name)
                stats[f"tx_type_{category}"] += 1

                # Track unique accounts (from transfers)
                transfers = tx.get("transfers", [])
                for transfer in transfers:
                    account = transfer.get("account")
                    if account:
                        stats["accounts"].add(account)

                # Sum fees
                fee = tx.get("charged_tx_fee", 0) or 0
                stats["total_fees"] += fee

                # Track success/failure
                result = tx.get("result", "")
                if result == "SUCCESS":
                    stats["success_count"] += 1
                else:
                    stats["failure_count"] += 1

            page_count += 1
            pbar.update(1)
            pbar.set_postfix({
                "txs": f"{tx_count:,}",
                "days": len(daily_stats),
            })

            # Check for next page
            links = data.get("links", {})
            next_link = links.get("next")
            if not next_link:
                break

            time.sleep(delay)

    print(f"\nFetched {tx_count:,} transactions across {page_count:,} pages")
    print(f"Aggregated into {len(daily_stats)} daily records")

    # Write CSV
    output_path = f"{DATA_DIR}/{output_file}"
    rows = []
    for date_str, stats in sorted(daily_stats.items()):
        total_fees_hbar = stats["total_fees"] / 100_000_000  # tinybars to HBAR
        avg_fee = total_fees_hbar / stats["tx_count"] if stats["tx_count"] > 0 else 0

        rows.append({
            "date": date_str,
            "tx_count": stats["tx_count"],
            "tx_type_crypto": stats["tx_type_crypto"],
            "tx_type_hcs": stats["tx_type_hcs"],
            "tx_type_token": stats["tx_type_token"],
            "tx_type_contract": stats["tx_type_contract"],
            "tx_type_other": stats["tx_type_other"],
            "unique_accounts": len(stats["accounts"]),
            "total_fees_hbar": round(total_fees_hbar, 4),
            "avg_fee_hbar": round(avg_fee, 8),
            "success_count": stats["success_count"],
            "failure_count": stats["failure_count"],
        })

    # Write to CSV
    with open(output_path, "w", newline="") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"Saved to {output_path}")

    # Print summary
    if rows:
        total_tx = sum(r["tx_count"] for r in rows)
        total_fees = sum(r["total_fees_hbar"] for r in rows)
        print(f"\nSummary:")
        print(f"  Date range: {rows[0]['date']} to {rows[-1]['date']}")
        print(f"  Total transactions: {total_tx:,}")
        print(f"  Total fees: {total_fees:,.2f} HBAR")

    return rows


# Keep old function for backwards compatibility but mark as legacy
def save_transactions_raw(output_file: str = "transactions_raw.jsonl", days: int = DAYS_TO_FETCH):
    """Legacy: Save raw transactions to JSONL file. Use fetch_and_aggregate instead."""
    import json
    output_path = f"{DATA_DIR}/{output_file}"

    timestamp_start, timestamp_end = get_timestamp_range(days)
    print(f"Fetching transactions from {timestamp_start} to {timestamp_end}")

    next_link = None
    page_count = 0
    tx_count = 0
    delay = 1.0 / REQUESTS_PER_SECOND

    with open(output_path, "w") as f:
        with tqdm(desc="Fetching transactions", unit=" pages") as pbar:
            while True:
                try:
                    data = fetch_transactions_page(
                        timestamp_start, timestamp_end, next_link
                    )
                except requests.RequestException as e:
                    print(f"Error fetching page {page_count}: {e}")
                    time.sleep(5)
                    continue

                transactions = data.get("transactions", [])
                for tx in transactions:
                    f.write(json.dumps(tx) + "\n")
                    tx_count += 1

                page_count += 1
                pbar.update(1)
                pbar.set_postfix({"transactions": tx_count})

                links = data.get("links", {})
                next_link = links.get("next")
                if not next_link:
                    break

                time.sleep(delay)

    print(f"Fetched {tx_count} transactions across {page_count} pages")
    print(f"Saved raw transactions to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch Hedera transactions")
    parser.add_argument(
        "--days", type=int, default=DAYS_TO_FETCH,
        help=f"Number of days to fetch (default: {DAYS_TO_FETCH})"
    )
    parser.add_argument(
        "--output", type=str, default="hedera_daily_stats.csv",
        help="Output filename"
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="Use legacy raw JSONL output (slower, not recommended)"
    )
    args = parser.parse_args()

    if args.raw:
        save_transactions_raw("transactions_raw.jsonl", args.days)
    else:
        fetch_and_aggregate(args.days, args.output)
