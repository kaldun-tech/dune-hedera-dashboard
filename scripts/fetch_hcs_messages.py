"""Fetch HCS (Hedera Consensus Service) messages from Mirror Node API."""

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
    """Save raw HCS messages to JSONL file."""
    output_path = f"{DATA_DIR}/{output_file}"

    with open(output_path, "w") as f:
        for msg in fetch_all_hcs_messages(topic_ids=topic_ids):
            f.write(json.dumps(msg) + "\n")

    print(f"Saved HCS messages to {output_path}")


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
