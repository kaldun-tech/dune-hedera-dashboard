"""Transform raw Hedera data into aggregated daily stats for Dune upload."""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import DATA_DIR, get_tx_category


def parse_consensus_timestamp(ts: str) -> datetime:
    """Parse Hedera consensus timestamp (seconds.nanoseconds) to datetime."""
    seconds = float(ts.split(".")[0])
    return datetime.utcfromtimestamp(seconds)


def stream_jsonl(filepath: str):
    """Stream records from JSONL file one at a time (memory efficient)."""
    with open(filepath, "r") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def aggregate_daily_transactions(filepath: str) -> pd.DataFrame:
    """
    Aggregate transactions into daily stats.

    Returns DataFrame with columns:
    - date
    - tx_count
    - tx_type_crypto
    - tx_type_hcs
    - tx_type_token
    - tx_type_contract
    - tx_type_other
    - unique_accounts
    - total_fees_tinybars
    - total_fees_hbar
    - avg_fee_hbar
    - success_count
    - failure_count
    """
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

    tx_count = 0
    for tx in stream_jsonl(filepath):
        tx_count += 1
        if tx_count % 1_000_000 == 0:
            print(f"  Processed {tx_count:,} transactions...")
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

    # Convert to DataFrame
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

    print(f"  Total processed: {tx_count:,} transactions")
    return pd.DataFrame(rows)


def aggregate_daily_hcs(filepath: str) -> pd.DataFrame:
    """
    Aggregate HCS messages into daily stats.

    Returns DataFrame with columns:
    - date
    - message_count
    - unique_topics
    - topic_list (comma-separated)
    """
    daily_stats = defaultdict(lambda: {
        "message_count": 0,
        "topics": set(),
    })

    msg_count = 0
    for msg in stream_jsonl(filepath):
        msg_count += 1
        ts = msg.get("consensus_timestamp", "")
        if not ts:
            continue

        dt = parse_consensus_timestamp(ts)
        date_str = dt.strftime("%Y-%m-%d")
        stats = daily_stats[date_str]

        stats["message_count"] += 1

        topic_id = msg.get("topic_id", "")
        if topic_id:
            stats["topics"].add(topic_id)

    rows = []
    for date_str, stats in sorted(daily_stats.items()):
        rows.append({
            "date": date_str,
            "message_count": stats["message_count"],
            "unique_topics": len(stats["topics"]),
            "topic_list": ",".join(sorted(stats["topics"])),
        })

    return pd.DataFrame(rows)


def transform_transactions(
    input_file: str = "transactions_raw.jsonl",
    output_file: str = "hedera_daily_stats.csv",
):
    """Transform raw transactions to daily stats CSV."""
    input_path = Path(DATA_DIR) / input_file
    output_path = Path(DATA_DIR) / output_file

    print(f"Streaming transactions from {input_path}...")
    print("Aggregating daily stats (streaming mode)...")
    df = aggregate_daily_transactions(str(input_path))
    print(f"Generated {len(df)} daily records")

    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")

    # Print summary
    print("\nSummary:")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Total transactions: {df['tx_count'].sum():,}")
    print(f"  Total fees: {df['total_fees_hbar'].sum():,.2f} HBAR")

    return df


def transform_hcs_messages(
    input_file: str = "hcs_messages_raw.jsonl",
    output_file: str = "hedera_hcs_daily.csv",
):
    """Transform raw HCS messages to daily stats CSV."""
    input_path = Path(DATA_DIR) / input_file
    output_path = Path(DATA_DIR) / output_file

    if not input_path.exists():
        print(f"No HCS data found at {input_path}")
        return None

    print(f"Streaming HCS messages from {input_path}...")
    print("Aggregating daily HCS stats (streaming mode)...")
    df = aggregate_daily_hcs(str(input_path))
    print(f"Generated {len(df)} daily records")

    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Transform Hedera data")
    parser.add_argument(
        "--type", choices=["transactions", "hcs", "all"], default="all",
        help="Type of data to transform"
    )
    args = parser.parse_args()

    if args.type in ("transactions", "all"):
        transform_transactions()

    if args.type in ("hcs", "all"):
        transform_hcs_messages()
