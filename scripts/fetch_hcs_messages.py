"""Fetch HCS (Hedera Consensus Service) messages from Mirror Node API."""

import time
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
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

# Default max runtime in seconds (45 minutes, leaves 15 min buffer for 1-hour timeout)
DEFAULT_MAX_RUNTIME = 45 * 60

# State file for incremental fetching
HCS_STATE_FILE = Path(DATA_DIR) / ".hcs_fetch_state.json"


def load_hcs_state() -> dict:
    """Load incremental fetch state."""
    if HCS_STATE_FILE.exists():
        with open(HCS_STATE_FILE) as f:
            return json.load(f)
    return {}


def save_hcs_state(state: dict):
    """Save incremental fetch state."""
    HCS_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HCS_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_existing_hcs_stats(output_file: str = "hcs_daily_stats.csv") -> dict:
    """Load existing HCS daily stats from CSV, returns dict keyed by date."""
    output_path = Path(DATA_DIR) / output_file
    if not output_path.exists():
        return {}

    existing = {}
    with open(output_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing[row["date"]] = {
                "message_count": int(row["message_count"]),
                "unique_topics": int(row["unique_topics"]),
                "total_message_size": int(row.get("total_message_size", 0)),
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
    return (
        f"{int(start.timestamp())}.000000000",
        f"{int(end.timestamp())}.000000000",
    )


def fetch_topics_with_activity(
    timestamp_start: str,
    timestamp_end: str,
    limit: int = 100,
) -> list[str]:
    """
    Find topics with recent activity by looking at CONSENSUSSUBMITMESSAGE transactions.
    Returns list of topic IDs.
    """
    url = (
        f"{HEDERA_MIRROR_URL}/api/v1/transactions"
        f"?timestamp=gte:{timestamp_start}"
        f"&timestamp=lte:{timestamp_end}"
        f"&transactiontype=CONSENSUSSUBMITMESSAGE"
        f"&limit={limit}"
    )

    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    topics = set()
    for tx in data.get("transactions", []):
        entity_id = tx.get("entity_id")
        if entity_id:
            topics.add(entity_id)

    return list(topics)


def fetch_topic_messages(
    topic_id: str,
    timestamp_start: str | None = None,
    timestamp_end: str | None = None,
) -> Iterator[dict]:
    """
    Fetch all messages for a specific topic.

    Yields individual message records.
    """
    base_url = f"{HEDERA_MIRROR_URL}/api/v1/topics/{topic_id}/messages"
    params = ["limit=100"]

    if timestamp_start:
        params.append(f"timestamp=gte:{timestamp_start}")
    if timestamp_end:
        params.append(f"timestamp=lte:{timestamp_end}")

    url = f"{base_url}?{'&'.join(params)}"
    delay = 1.0 / REQUESTS_PER_SECOND

    while url:
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Error fetching messages for topic {topic_id}: {e}")
            time.sleep(5)
            continue

        for msg in data.get("messages", []):
            msg["topic_id"] = topic_id  # Add topic ID to message
            yield msg

        # Check for next page
        links = data.get("links", {})
        next_link = links.get("next")
        if next_link:
            url = f"{HEDERA_MIRROR_URL}{next_link}"
            time.sleep(delay)
        else:
            url = None


def fetch_all_hcs_messages(
    days: int = DAYS_TO_FETCH,
    topic_ids: list[str] | None = None,
) -> Iterator[dict]:
    """
    Fetch HCS messages for specified topics or discover active topics.

    Yields individual message records with topic_id included.
    """
    timestamp_start, timestamp_end = get_timestamp_range(days)

    # Discover active topics if not provided
    if not topic_ids:
        print("Discovering active topics...")
        topic_ids = fetch_topics_with_activity(timestamp_start, timestamp_end)
        print(f"Found {len(topic_ids)} active topics")

    if not topic_ids:
        print("No active topics found")
        return

    total_messages = 0
    for topic_id in tqdm(topic_ids, desc="Fetching topic messages"):
        for msg in fetch_topic_messages(topic_id, timestamp_start, timestamp_end):
            yield msg
            total_messages += 1

    print(f"Fetched {total_messages} messages from {len(topic_ids)} topics")


def save_hcs_messages_raw(
    output_file: str = "hcs_messages_raw.jsonl",
    topic_ids: list[str] | None = None,
):
    """Save raw HCS messages to JSONL file. (Legacy - use fetch_and_aggregate_hcs instead)"""
    output_path = f"{DATA_DIR}/{output_file}"

    with open(output_path, "w") as f:
        for msg in fetch_all_hcs_messages(topic_ids=topic_ids):
            f.write(json.dumps(msg) + "\n")

    print(f"Saved HCS messages to {output_path}")


def fetch_hcs_for_date_range(
    start_dt: datetime,
    end_dt: datetime,
    daily_stats: dict,
    start_time: float | None = None,
    max_runtime: int = DEFAULT_MAX_RUNTIME,
) -> tuple[int, bool]:
    """
    Fetch HCS messages for a date range and aggregate into daily_stats.

    Returns (message_count, timed_out).
    """
    timestamp_start = f"{int(start_dt.timestamp())}.000000000"
    timestamp_end = f"{int(end_dt.timestamp())}.999999999"

    # First discover active topics in this range
    print(f"Discovering active topics for {start_dt.date()} to {end_dt.date()}...")
    topic_ids = fetch_topics_with_activity(timestamp_start, timestamp_end)
    print(f"Found {len(topic_ids)} active topics")

    if not topic_ids:
        return 0, False

    total_messages = 0
    delay = 1.0 / REQUESTS_PER_SECOND

    for topic_id in tqdm(topic_ids, desc="Fetching topics"):
        # Check timeout before each topic
        if start_time and (time.time() - start_time) >= max_runtime:
            elapsed = int(time.time() - start_time)
            print(f"\nApproaching timeout ({elapsed}s elapsed), stopping gracefully.")
            return total_messages, True

        for msg in fetch_topic_messages(topic_id, timestamp_start, timestamp_end):
            total_messages += 1

            # Parse timestamp and aggregate
            ts = msg.get("consensus_timestamp", "")
            if not ts:
                continue

            seconds = float(ts.split(".")[0])
            dt = datetime.utcfromtimestamp(seconds)
            date_str = dt.strftime("%Y-%m-%d")

            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    "message_count": 0,
                    "topics": set(),
                    "total_message_size": 0,
                }

            stats = daily_stats[date_str]
            stats["message_count"] += 1
            stats["topics"].add(topic_id)

            # Track message size if available
            message = msg.get("message", "")
            if message:
                stats["total_message_size"] += len(message)

    return total_messages, False


def save_hcs_progress(daily_stats: dict, output_file: str = "hcs_daily_stats.csv") -> list:
    """Save current HCS aggregation progress to CSV."""
    output_path = f"{DATA_DIR}/{output_file}"
    rows = []

    for date_str, stats in sorted(daily_stats.items()):
        unique_topics = len(stats["topics"]) if isinstance(stats.get("topics"), set) else stats.get("unique_topics", 0)

        rows.append({
            "date": date_str,
            "message_count": stats["message_count"],
            "unique_topics": unique_topics,
            "total_message_size": stats.get("total_message_size", 0),
        })

    with open(output_path, "w", newline="") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"Saved {len(rows)} days of HCS stats to {output_path}")
    return rows


def fetch_and_aggregate_hcs(
    days: int = DAYS_TO_FETCH,
    output_file: str = "hcs_daily_stats.csv",
    max_runtime: int = DEFAULT_MAX_RUNTIME,
):
    """
    Fetch HCS messages and aggregate into daily stats, with incremental support.

    - Loads existing data from CSV
    - Determines which dates are missing
    - Fetches only missing date ranges
    - Stops gracefully before timeout
    """
    start_time = time.time()
    print(f"Target: last {days} days of HCS data")
    print(f"Max runtime: {max_runtime // 60} minutes")

    # Load existing data
    existing_data = load_existing_hcs_stats(output_file)
    if existing_data:
        print(f"Found existing HCS data for {len(existing_data)} days")

    # Calculate missing date ranges
    missing_ranges = get_missing_date_ranges(set(existing_data.keys()), days)

    if not missing_ranges:
        print("All HCS dates already fetched, nothing to do.")
        return list(existing_data.values())

    total_missing_days = sum(
        (end - start).days + 1 for start, end in missing_ranges
    )
    print(f"Missing {total_missing_days} days across {len(missing_ranges)} range(s)")

    # Start with existing data
    daily_stats = {}
    for date_str, data in existing_data.items():
        daily_stats[date_str] = {
            "message_count": data["message_count"],
            "topics": set(),  # Can't restore from count
            "total_message_size": data.get("total_message_size", 0),
            "_unique_topics_preserved": data["unique_topics"],
        }

    total_messages = 0
    timed_out = False

    for i, (start_dt, end_dt) in enumerate(missing_ranges):
        # Check if we should stop before starting a new range
        elapsed = time.time() - start_time
        if elapsed >= max_runtime:
            print(f"\nApproaching timeout ({int(elapsed)}s elapsed), stopping before next range.")
            timed_out = True
            break

        print(f"\nRange {i+1}/{len(missing_ranges)}: {start_dt.date()} to {end_dt.date()}")

        msgs, range_timed_out = fetch_hcs_for_date_range(
            start_dt, end_dt, daily_stats, start_time, max_runtime
        )
        total_messages += msgs

        # Save progress after each range
        save_hcs_progress(daily_stats, output_file)

        if range_timed_out:
            timed_out = True
            break

    elapsed = int(time.time() - start_time)
    print(f"\nFetched {total_messages:,} HCS messages in {elapsed}s")
    print(f"Total days with HCS data: {len(daily_stats)}")

    if timed_out:
        print("Stopped gracefully before timeout - run again to continue.")
    else:
        # Clear state on successful completion
        if HCS_STATE_FILE.exists():
            HCS_STATE_FILE.unlink()
        print("All missing HCS dates fetched successfully.")

    return save_hcs_progress(daily_stats, output_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch HCS messages")
    parser.add_argument(
        "--days", type=int, default=DAYS_TO_FETCH,
        help=f"Number of days to fetch (default: {DAYS_TO_FETCH})"
    )
    parser.add_argument(
        "--topics", type=str, nargs="*",
        help="Specific topic IDs to fetch (e.g., 0.0.12345)"
    )
    parser.add_argument(
        "--output", type=str, default="hcs_messages_raw.jsonl",
        help="Output filename"
    )
    args = parser.parse_args()

    save_hcs_messages_raw(args.output, topic_ids=args.topics)
