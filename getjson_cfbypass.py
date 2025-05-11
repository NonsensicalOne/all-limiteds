"""
Module for fetching items and owners from Polytoria with Cloudflare bypass using a local proxy.
"""

import re
import time
import json
import requests

# Global storage for fetched items and their owners
items = {}

# Constants
BASE_API_PROXY = "http://localhost:20080/v1"
ITEMS_URL_TEMPLATE = (
    "https://polytoria.com/api/store/items?"
    "types[]=tool&types[]=face&types[]=hat&search=&sort=createdAt&"
    "order=desc&showOffsale=false&collectiblesOnly=true&page={page}"
)
OWNERS_URL_TEMPLATE = (
    "https://api.polytoria.com/v1/store/{item_id}/owners?limit=100&page={page}"
)
REQUEST_TIMEOUT = 60  # seconds


def fetch_items(page=1):
    """
    Fetch a page of items, retrying on JSON or key errors.

    Args:
        page (int): Page number to fetch.

    Returns:
        str | None: Cleaned JSON string of items, or None on failure.
    """
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            url = ITEMS_URL_TEMPLATE.format(page=page)
            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": REQUEST_TIMEOUT * 1000,
            }
            response = requests.post(
                BASE_API_PROXY,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            data = response.json()
            solution = data["solution"]["response"]
            return re.sub(r"<.*?>", "", solution)
        except (KeyError, json.JSONDecodeError) as e:
            print(
                f"Error fetching items page {page}: {e}. "
                f"Retry {attempt}/{max_retries} in 10 seconds..."
            )
            time.sleep(10)
    print(f"Max retries ({max_retries}) reached for items page {page}. Skipping.")
    return None


def fetch_owners(item_id, page=1):
    """
    Fetch a page of owners for a given item, retrying on JSON or key errors.

    Args:
        item_id (int | str): ID of the item to fetch owners for.
        page (int): Page number to fetch.

    Returns:
        str | None: Cleaned JSON string of owners, or None on failure.
    """
    max_retries = 7
    for attempt in range(1, max_retries + 1):
        try:
            url = OWNERS_URL_TEMPLATE.format(item_id=item_id, page=page)
            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": REQUEST_TIMEOUT * 1000,
            }
            response = requests.post(
                BASE_API_PROXY,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            data = response.json()
            solution = data["solution"]["response"]
            return re.sub(r"<.*?>", "", solution)
        except (KeyError, json.JSONDecodeError) as e:
            print(
                f"Error fetching owners for item {item_id}, page {page}: {e}. "
                f"Retry {attempt}/{max_retries} in 10 seconds..."
            )
            time.sleep(10)
    print(
        f"Max retries ({max_retries}) reached for item {item_id}, page {page}. Skipping."
    )
    return None


def process_all_items():
    """
    Fetch all store items and process their owners into the global 'items' dict.

    Raises:
        ValueError: If API response structure is invalid.
    """
    page = 1
    while True:
        response = fetch_items(page)
        if response is None:
            print(f"Skipping items page {page} due to fetch failure.")
            page += 1
            continue
        try:
            json_data = json.loads(response)
        except json.JSONDecodeError:
            print(f"Error parsing JSON for items page {page}. Retrying...")
            time.sleep(10)
            continue

        data_list = json_data.get("data")
        if not isinstance(data_list, list):
            print(f"Invalid data in items page {page}. Skipping.")
            page += 1
            continue

        for entry in data_list:
            item_id = entry.get("id")
            name = entry.get("name", "")
            items[item_id] = {"name": name, "owners": []}
            process_owners(item_id)

        last_page = json_data.get("meta", {}).get("lastPage", page)
        if page >= last_page:
            break
        page += 1
        time.sleep(0.6)


def process_owners(item_id):
    """
    Fetch and accumulate owner inventories for a single item.

    Args:
        item_id (int | str): ID of the item to process.
    """
    page = 1
    while True:
        response = fetch_owners(item_id, page)
        if response is None:
            print(f"Stopping owner fetch for item {item_id} due to errors.")
            break
        try:
            json_data = json.loads(response)
        except json.JSONDecodeError:
            print(
                f"Error parsing JSON for owners of item {item_id}, page {page}. Retrying..."
            )
            time.sleep(10)
            continue

        inventories = json_data.get("inventories", [])
        if not inventories:
            break

        for inv in inventories:
            username = inv.get("user", {}).get("username", "")
            # Find or append owner count
            for owner in items[item_id]["owners"]:
                if owner["name"] == username:
                    owner["count"] += 1
                    break
            else:
                items[item_id]["owners"].append({"name": username, "count": 1})

        pages = json_data.get("pages", 0)
        if page >= pages:
            break
        page += 1
        time.sleep(0.6)


def save_owners(filepath="owners.json"):
    """
    Save the collected items and owners to a JSON file.

    Args:
        filepath (str): Path to the output JSON file.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=4)


def main():
    """
    Main execution: process items and save results.
    """
    process_all_items()
    save_owners()


if __name__ == "__main__":
    main()
