"""
Main module for processing ownership data, updating README, and generating charts.
"""

import json
import matplotlib.pyplot as plt
from matplotlib import colormaps as cm
import numpy as np


def generate_pie_chart(user_counts, title, filename):
    """
    Generates a pie chart from a mapping of labels to values.

    Args:
        user_counts (dict): Mapping of labels to counts.
        title (str): Chart title.
        filename (str): Output SVG filename.
    """
    labels = list(user_counts.keys())
    values = list(user_counts.values())

    plt.figure(figsize=(10, 8))
    plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title(title)
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def generate_bar_chart(user_counts, title, filename):
    """
    Generates a bar chart from a mapping of labels to values.

    Args:
        user_counts (dict): Mapping of labels to counts.
        title (str): Chart title.
        filename (str): Output SVG filename.
    """
    labels = list(user_counts.keys())
    values = list(user_counts.values())

    # Use the 'tab10' colormap
    colormap = cm.get_cmap("tab10")
    colors = colormap(np.linspace(0, 1, len(labels)))

    plt.figure()
    bars = plt.bar(labels, values, color=colors)
    plt.xlabel("Users")
    plt.ylabel("Number of Owned Items")
    plt.title(title)
    plt.xticks(rotation=45, ha="right")

    # Annotate each bar with its height
    for rect in bars:
        height = rect.get_height()
        plt.text(
            rect.get_x() + rect.get_width() / 2,
            height + 0.2,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def aggregate_others(user_counts, top_n=10):
    """
    Aggregates all but the top N entries into an 'Others' category.

    Args:
        user_counts (dict): Mapping of labels to counts, assumed sorted descending.
        top_n (int): Number of top entries to keep separately.

    Returns:
        dict: Top N entries plus an 'Others' key summing the rest.
    """
    total = sum(user_counts.values())
    if len(user_counts) <= top_n:
        return user_counts.copy()

    top_n_dict = dict(list(user_counts.items())[:top_n])
    others_count = total - sum(top_n_dict.values())
    top_n_dict["Others"] = others_count
    return top_n_dict


def process_data(file_path):
    """
    Processes the JSON data to compute per-user counts and total count.

    Args:
        file_path (str): Path to the JSON file with an 'owners' field per item.

    Returns:
        tuple: (dict of user->count, int total count)
    """
    user_counts = {}
    total_lims = 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for record in data.values():
        for owner in record.get("owners", []):
            name = owner.get("name")
            count = owner.get("count", 0)
            user_counts[name] = user_counts.get(name, 0) + count
            total_lims += count

    return user_counts, total_lims


def main():
    """
    Main script entry point. Processes data, updates README, and generates charts.
    """
    # Load and process data
    user_counts, total_lims = process_data("owners.json")

    # Update README.md fun fact
    with open("README.md", "r", encoding="ascii") as f:
        lines = f.readlines()
    for idx, line in enumerate(lines):
        if line.startswith("**Fun fact:** There are over "):
            lines[idx] = (
                f"**Fun fact:** There are over **{total_lims}** limited copies!\n"
            )
    with open("README.md", "w", encoding="ascii") as f:
        f.writelines(lines)

    # Sort users descending and prepare top entries
    sorted_counts = dict(sorted(user_counts.items(), key=lambda x: x[1], reverse=True))
    top_10 = dict(list(sorted_counts.items())[:10])
    with_others = aggregate_others(sorted_counts, top_n=10)

    # Generate charts
    generate_pie_chart(
        with_others,
        "Top 10 Item Ownership Distribution by User",
        "top_10_item_ownership_distribution.svg",
    )
    generate_bar_chart(
        top_10,
        "Top 10 Item Ownership Distribution by User",
        "top_10_item_ownership_distribution_bar.svg",
    )


if __name__ == "__main__":
    main()
