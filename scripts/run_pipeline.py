#!/usr/bin/env python3
"""
Run the complete Hedera data pipeline.

Usage:
    python run_pipeline.py              # Full pipeline (fetch, transform, upload)
    python run_pipeline.py --fetch      # Only fetch data
    python run_pipeline.py --transform  # Only transform
    python run_pipeline.py --upload     # Only upload
    python run_pipeline.py --days 7     # Fetch last 7 days instead of 90
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DUNE_API_KEY, DATA_DIR


def run_fetch(days: int = 90, skip_hcs: bool = False):
    """Fetch data from Hedera Mirror Node and aggregate on the fly."""
    print("=" * 60)
    print("STEP 1: Fetching data from Hedera Mirror Node")
    print("=" * 60)

    from fetch_transactions import fetch_and_aggregate
    fetch_and_aggregate(days=days)

    if not skip_hcs:
        print("\n")
        from fetch_hcs_messages import save_hcs_messages_raw
        save_hcs_messages_raw()


def run_transform():
    """Transform raw data into aggregated CSVs."""
    print("\n" + "=" * 60)
    print("STEP 2: Transforming data")
    print("=" * 60)

    from pathlib import Path
    from transform import transform_transactions, transform_hcs_messages

    # Skip transaction transform if already aggregated during fetch
    stats_file = Path(DATA_DIR) / "hedera_daily_stats.csv"
    raw_file = Path(DATA_DIR) / "transactions_raw.jsonl"

    if stats_file.exists() and not raw_file.exists():
        print("Transaction stats already aggregated during fetch, skipping transform")
    elif raw_file.exists():
        print("Found raw transactions, running legacy transform...")
        transform_transactions()
    else:
        print("No transaction data found")

    transform_hcs_messages()


def run_upload():
    """Upload CSVs to Dune."""
    print("\n" + "=" * 60)
    print("STEP 3: Uploading to Dune")
    print("=" * 60)

    if not DUNE_API_KEY:
        print("ERROR: DUNE_API_KEY not set")
        print("Copy scripts/.env.example to scripts/.env and add your key")
        return False

    from upload_to_dune import main as upload_main
    upload_main()
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Hedera data pipeline for Dune Analytics"
    )
    parser.add_argument(
        "--fetch", action="store_true",
        help="Only run fetch step"
    )
    parser.add_argument(
        "--transform", action="store_true",
        help="Only run transform step"
    )
    parser.add_argument(
        "--upload", action="store_true",
        help="Only run upload step"
    )
    parser.add_argument(
        "--days", type=int, default=90,
        help="Number of days to fetch (default: 90)"
    )
    parser.add_argument(
        "--skip-hcs", action="store_true",
        help="Skip HCS message fetching"
    )
    args = parser.parse_args()

    # If no specific step requested, run all
    run_all = not (args.fetch or args.transform or args.upload)

    print("Hedera Data Pipeline")
    print(f"Data directory: {DATA_DIR}")
    print()

    if args.fetch or run_all:
        run_fetch(args.days, args.skip_hcs)

    if args.transform or run_all:
        run_transform()

    if args.upload or run_all:
        run_upload()

    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
