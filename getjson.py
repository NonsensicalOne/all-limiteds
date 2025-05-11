"""
Module for fetching items and owners from Polytoria's API.
"""

import time
import json
import requests

# Global storage for fetched items and their owners
items = {}

# API endpoints
ITEMS_URL_TEMPLATE = (
    "https://polytoria.com/api/store/items?"
    "types[]=tool&types[]=face&types[]=hat&search=&sort=createdAt&"
    "order=desc&showOffsale=false&collectiblesOnly=true&page={page}"
)
OWNERS_URL_TEMPLATE = (
    "https://api.polytoria.com/v1/store/{item_id}/owners?limit=100&page={page}"
)

# Request settings
REQUEST_TIMEOUT = 30  # seconds
RATE_LIMIT_DELAY = 10  # seconds between retries on 429
PAGE_DELAY = 0.6  # seconds between successful page fetches


def fetch_items(page=1):
    """
    Fetch a page of store items.

    Args:
        page (int): Page number to fetch.

    Returns:
        requests.Response: HTTP response object.
    """
    url = ITEMS_URL_TEMPLATE.format(page=page)
    return requests.get(url, timeout=REQUEST_TIMEOUT)


def fetch_owners(item_id, page=1):
    """
    Fetch owner inventories for a given item and page.

    Args:
        item_id (int | str): Store item ID.
        page (int): Page number to fetch.

    Returns:
        requests.Response: HTTP response object.
    """
    url = OWNERS_URL_TEMPLATE.format(item_id=item_id, page=page)
    return requests.get(url, timeout=REQUEST_TIMEOUT)


def handle_rate_limit(response):
    """
    Wait and retry if rate limited (HTTP 429).

    Args:
        response (requests.Response): Initial response.

    Returns:
        requests.Response: Final non-429 response.
    """
    while response.status_code == 429:
        time.sleep(RATE_LIMIT_DELAY)
        response = requests.get(response.url, timeout=REQUEST_TIMEOUT)
    return response


def process_all_items():
    """
    Iterate through all item pages, process each item's owners.
    """
    page = 1
    while True:
        response = fetch_items(page)
        response = handle_rate_limit(response)
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"Error parsing items page {page}. Retrying...")
            time.sleep(RATE_LIMIT_DELAY)
            continue

        for entry in data.get("data", []):
            item_id = entry.get("id")
            items[item_id] = {"name": entry.get("name", ""), "owners": []}
            process_owners(item_id)

        last_page = data.get("meta", {}).get("lastPage", page)
        if page >= last_page:
            return
        page += 1
        time.sleep(PAGE_DELAY)


def process_owners(item_id):
    """
    Process all owner inventory pages for a specific item.

    Args:
        item_id (int | str): Store item ID.
    """
    page = 1
    while True:
        response = fetch_owners(item_id, page)
        response = handle_rate_limit(response)
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"Error parsing owners for item {item_id}, page {page}. Retrying...")
            time.sleep(RATE_LIMIT_DELAY)
            continue

        inventories = data.get("inventories", [])
        if not inventories:
            return

        for inv in inventories:
            user = inv.get("user", {})
            username = user.get("username", "")
            for owner in items[item_id]["owners"]:
                if owner["name"] == username:
                    owner["count"] += 1
                    break
            else:
                items[item_id]["owners"].append({"name": username, "count": 1})

        pages = data.get("pages", 0)
        if page >= pages:
            return
        page += 1
        time.sleep(PAGE_DELAY)


def main():
    """
    Main execution: process items and write owners.json with UTF-8 encoding.
    """
    process_all_items()
    with open("owners.json", "w", encoding="utf-8") as f:
        json.dump(items, f, indent=4)


if __name__ == "__main__":
    main()
