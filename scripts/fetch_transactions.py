"""Fetch transactions from Hedera Mirror Node API and aggregate on the fly."""

import time
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

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

# State file for incremental fetching
STATE_FILE = Path(DATA_DIR) / ".fetch_state.json"


def load_state() -> dict:
    """Load incremental fetch state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    """Save incremental fetch state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_existing_stats(output_file: str) -> dict:
    """Load existing daily stats from CSV, returns dict keyed by date."""
    output_path = Path(DATA_DIR) / output_file
    if not output_path.exists():
        return {}

    existing = {}
    with open(output_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing[row["date"]] = {
                "tx_count": int(row["tx_count"]),
                "tx_type_crypto": int(row["tx_type_crypto"]),
                "tx_type_hcs": int(row["tx_type_hcs"]),
                "tx_type_token": int(row["tx_type_token"]),
                "tx_type_contract": int(row["tx_type_contract"]),
                "tx_type_other": int(row["tx_type_other"]),
                "unique_accounts": int(row["unique_accounts"]),
                "total_fees_hbar": float(row["total_fees_hbar"]),
                "avg_fee_hbar": float(row["avg_fee_hbar"]),
                "success_count": int(row["success_count"]),
                "failure_count": int(row["failure_count"]),
            }
    return existing


def get_missing_date_ranges(existing_dates: set, target_days: int) -> list[tuple[datetime, datetime]]:
    """
    Determine which date ranges need to be fetched.
    Returns list of (start, end) datetime tuples for missing ranges.
    Prioritizes recent dates first.
    """
    today = datetime.utcnow().date()
    target_dates = {today - timedelta(days=i) for i in range(target_days)}
    missing_dates = target_dates - {datetime.strptime(d, "%Y-%m-%d").date() for d in existing_dates}

    if not missing_dates:
        return []

    # Sort missing dates (most recent first for priority)
    sorted_missing = sorted(missing_dates, reverse=True)

    # Group into contiguous ranges
    ranges = []
    range_start = sorted_missing[0]
    range_end = sorted_missing[0]

    for date in sorted_missing[1:]:
        if (range_end - date).days == 1:
            range_end = date
        else:
            # End current range, start new one
            ranges.append((
                datetime.combine(range_end, datetime.min.time()),
                datetime.combine(range_start, datetime.max.time())
            ))
            range_start = date
            range_end = date

    # Don't forget the last range
    ranges.append((
        datetime.combine(range_end, datetime.min.time()),
        datetime.combine(range_start, datetime.max.time())
    ))

    return ranges


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


def fetch_date_range(
    start_dt: datetime,
    end_dt: datetime,
    daily_stats: dict,
    max_pages: int | None = None,
) -> tuple[int, int, str | None]:
    """
    Fetch transactions for a specific date range and aggregate into daily_stats.

    Returns (pages_fetched, tx_count, last_next_link_if_interrupted).
    """
    timestamp_start = f"{int(start_dt.timestamp())}.000000000"
    timestamp_end = f"{int(end_dt.timestamp())}.999999999"

    next_link = None
    page_count = 0
    tx_count = 0
    delay = 1.0 / REQUESTS_PER_SECOND
    consecutive_errors = 0
    max_consecutive_errors = 10

    with tqdm(desc=f"Fetching {start_dt.date()} to {end_dt.date()}", unit=" pages") as pbar:
        while True:
            try:
                data = fetch_transactions_page(
                    timestamp_start, timestamp_end, next_link
                )
                consecutive_errors = 0
            except requests.RequestException as e:
                consecutive_errors += 1
                print(f"\nError fetching page {page_count}: {e}")
                if consecutive_errors >= max_consecutive_errors:
                    print(f"Too many consecutive errors ({max_consecutive_errors}), stopping range.")
                    return page_count, tx_count, next_link
                time.sleep(5)
                continue

            transactions = data.get("transactions", [])

            for tx in transactions:
                tx_count += 1

                ts = tx.get("consensus_timestamp", "")
                if not ts:
                    continue

                dt = parse_consensus_timestamp(ts)
                date_str = dt.strftime("%Y-%m-%d")

                # Initialize stats for this date if needed
                if date_str not in daily_stats:
                    daily_stats[date_str] = {
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
                    }

                stats = daily_stats[date_str]
                stats["tx_count"] += 1

                tx_name = tx.get("name", "")
                category = get_tx_category(tx_name)
                stats[f"tx_type_{category}"] += 1

                transfers = tx.get("transfers", [])
                for transfer in transfers:
                    account = transfer.get("account")
                    if account:
                        stats["accounts"].add(account)

                fee = tx.get("charged_tx_fee", 0) or 0
                stats["total_fees"] += fee

                result = tx.get("result", "")
                if result == "SUCCESS":
                    stats["success_count"] += 1
                else:
                    stats["failure_count"] += 1

            page_count += 1
            pbar.update(1)
            pbar.set_postfix({"txs": f"{tx_count:,}"})

            links = data.get("links", {})
            next_link = links.get("next")
            if not next_link:
                break

            if max_pages and page_count >= max_pages:
                print(f"\nReached max pages ({max_pages}), will resume next run.")
                return page_count, tx_count, next_link

            time.sleep(delay)

    return page_count, tx_count, None


def fetch_and_aggregate(days: int = DAYS_TO_FETCH, output_file: str = "hedera_daily_stats.csv"):
    """
    Fetch transactions and aggregate into daily stats, with incremental support.

    - Loads existing data from CSV
    - Determines which dates are missing
    - Fetches only missing date ranges
    - Merges new data with existing
    - Saves state for resuming interrupted fetches
    """
    print(f"Target: last {days} days of data")

    # Load existing data
    existing_data = load_existing_stats(output_file)
    if existing_data:
        print(f"Found existing data for {len(existing_data)} days")

    # Check for interrupted fetch state
    state = load_state()

    # Calculate missing date ranges
    missing_ranges = get_missing_date_ranges(set(existing_data.keys()), days)

    if not missing_ranges:
        print("All dates already fetched, nothing to do.")
        print("Run with --force to re-fetch all data.")
        return list(existing_data.values())

    total_missing_days = sum(
        (end - start).days + 1 for start, end in missing_ranges
    )
    print(f"Missing {total_missing_days} days across {len(missing_ranges)} range(s)")

    # Aggregation state - start with existing data converted back to raw format
    daily_stats = {}
    for date_str, data in existing_data.items():
        daily_stats[date_str] = {
            "tx_count": data["tx_count"],
            "tx_type_crypto": data["tx_type_crypto"],
            "tx_type_hcs": data["tx_type_hcs"],
            "tx_type_token": data["tx_type_token"],
            "tx_type_contract": data["tx_type_contract"],
            "tx_type_other": data["tx_type_other"],
            "accounts": set(),  # Can't restore unique accounts from count
            "total_fees": int(data["total_fees_hbar"] * 100_000_000),
            "success_count": data["success_count"],
            "failure_count": data["failure_count"],
            "_unique_accounts_preserved": data["unique_accounts"],  # Preserve old count
        }

    total_pages = 0
    total_tx = 0

    # Fetch each missing range
    for i, (start_dt, end_dt) in enumerate(missing_ranges):
        print(f"\nRange {i+1}/{len(missing_ranges)}: {start_dt.date()} to {end_dt.date()}")

        pages, txs, interrupted_link = fetch_date_range(start_dt, end_dt, daily_stats)
        total_pages += pages
        total_tx += txs

        # Save progress after each range
        save_progress(daily_stats, output_file)

        if interrupted_link:
            # Save state for resuming
            save_state({
                "interrupted_range": [start_dt.isoformat(), end_dt.isoformat()],
                "next_link": interrupted_link,
            })
            print(f"\nInterrupted - progress saved. Run again to continue.")
            break

    print(f"\nFetched {total_tx:,} transactions across {total_pages:,} pages")
    print(f"Total days with data: {len(daily_stats)}")

    # Clear state on successful completion
    if STATE_FILE.exists():
        STATE_FILE.unlink()

    return save_progress(daily_stats, output_file)


def save_progress(daily_stats: dict, output_file: str) -> list:
    """Save current aggregation progress to CSV."""
    output_path = f"{DATA_DIR}/{output_file}"
    rows = []

    for date_str, stats in sorted(daily_stats.items()):
        total_fees_hbar = stats["total_fees"] / 100_000_000
        avg_fee = total_fees_hbar / stats["tx_count"] if stats["tx_count"] > 0 else 0

        # Use preserved unique_accounts count if we didn't fetch new data for this date
        unique_accounts = len(stats["accounts"]) if stats["accounts"] else stats.get("_unique_accounts_preserved", 0)

        rows.append({
            "date": date_str,
            "tx_count": stats["tx_count"],
            "tx_type_crypto": stats["tx_type_crypto"],
            "tx_type_hcs": stats["tx_type_hcs"],
            "tx_type_token": stats["tx_type_token"],
            "tx_type_contract": stats["tx_type_contract"],
            "tx_type_other": stats["tx_type_other"],
            "unique_accounts": unique_accounts,
            "total_fees_hbar": round(total_fees_hbar, 4),
            "avg_fee_hbar": round(avg_fee, 8),
            "success_count": stats["success_count"],
            "failure_count": stats["failure_count"],
        })

    with open(output_path, "w", newline="") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"Saved {len(rows)} days to {output_path}")

    if rows:
        total_tx = sum(r["tx_count"] for r in rows)
        total_fees = sum(r["total_fees_hbar"] for r in rows)
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
