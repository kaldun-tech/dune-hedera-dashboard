"""Upload CSV data to Dune Analytics as community tables."""

import sys
from pathlib import Path

import requests

from config import DUNE_API_KEY, DUNE_UPLOAD_URL, DUNE_USERNAME, DATA_DIR


def upload_csv_to_dune(
    csv_path: str,
    table_name: str,
    description: str = "",
) -> dict:
    """
    Upload a CSV file to Dune as a community table.

    Args:
        csv_path: Path to the CSV file
        table_name: Name for the table (Dune will prefix with dataset_)
        description: Optional description for the table

    Returns:
        API response as dict
    """
    if not DUNE_API_KEY:
        raise ValueError(
            "DUNE_API_KEY not set. Add it to .env or set environment variable."
        )

    if not DUNE_USERNAME:
        raise ValueError(
            "DUNE_USERNAME not set. Add it to .env or set environment variable."
        )

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Read CSV content
    with open(csv_path, "r") as f:
        csv_content = f.read()

    # Prepare request (new /v1/uploads/csv endpoint)
    headers = {
        "X-Dune-Api-Key": DUNE_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "table_name": table_name,
        "data": csv_content,
        "is_private": False,
    }

    if description:
        payload["description"] = description

    print(f"Uploading {csv_path.name} to dune.{DUNE_USERNAME}.dataset_{table_name}...")

    response = requests.post(
        DUNE_UPLOAD_URL,
        headers=headers,
        json=payload,
        timeout=120,
    )

    if response.status_code in (200, 201):
        print(f"Successfully uploaded to dune.{DUNE_USERNAME}.dataset_{table_name}")
        return response.json()
    else:
        print(f"Upload failed: {response.status_code}")
        print(response.text)
        # Try to provide helpful error info
        try:
            error_detail = response.json()
            if "error" in error_detail:
                print(f"Error detail: {error_detail['error']}")
        except Exception:
            pass
        response.raise_for_status()


def upload_hedera_daily_stats():
    """Upload hedera_daily_stats.csv to Dune."""
    csv_path = Path(DATA_DIR) / "hedera_daily_stats.csv"

    return upload_csv_to_dune(
        csv_path=csv_path,
        table_name="hedera_daily_stats",
        description=(
            "Daily aggregated Hedera network statistics including transaction counts, "
            "fees, active accounts, and transaction type breakdown. "
            "Data sourced from Hedera Mirror Node API."
        ),
    )


def upload_hedera_hcs_daily():
    """Upload hedera_hcs_daily.csv to Dune."""
    csv_path = Path(DATA_DIR) / "hedera_hcs_daily.csv"

    if not csv_path.exists():
        print(f"HCS data not found at {csv_path}, skipping...")
        return None

    return upload_csv_to_dune(
        csv_path=csv_path,
        table_name="hedera_hcs_daily",
        description=(
            "Daily Hedera Consensus Service (HCS) message statistics. "
            "Includes message counts and active topics per day. "
            "Data sourced from Hedera Mirror Node API."
        ),
    )


def main():
    """Upload all Hedera data to Dune."""
    if not DUNE_API_KEY:
        print("Error: DUNE_API_KEY not set")
        print("Set it in .env file or as environment variable")
        sys.exit(1)

    if not DUNE_USERNAME:
        print("Error: DUNE_USERNAME not set")
        print("Set it in .env file or as environment variable")
        sys.exit(1)

    print(f"Uploading to Dune account: {DUNE_USERNAME}")
    print("-" * 50)

    # Upload daily stats
    try:
        upload_hedera_daily_stats()
    except FileNotFoundError as e:
        print(f"Skipping daily stats: {e}")
    except Exception as e:
        print(f"Error uploading daily stats: {e}")

    print("-" * 50)

    # Upload HCS data
    try:
        upload_hedera_hcs_daily()
    except Exception as e:
        print(f"Error uploading HCS data: {e}")

    print("-" * 50)
    print("Upload complete!")
    print(f"\nQuery your data with:")
    print(f"  SELECT * FROM dune.{DUNE_USERNAME}.dataset_hedera_daily_stats")
    print(f"  SELECT * FROM dune.{DUNE_USERNAME}.dataset_hedera_hcs_daily")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload Hedera data to Dune")
    parser.add_argument(
        "--file", type=str,
        help="Specific CSV file to upload"
    )
    parser.add_argument(
        "--table", type=str,
        help="Table name for custom upload"
    )
    args = parser.parse_args()

    if args.file and args.table:
        upload_csv_to_dune(args.file, args.table)
    else:
        main()
