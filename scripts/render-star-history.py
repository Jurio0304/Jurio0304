#!/usr/bin/env python3
"""Render the most recent 12 calendar months of GitHub star samples."""

import argparse
from datetime import date
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

SAMPLE_DAYS = (1, 11, 21)
MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
BLUE = "#2563eb"
TEXT = "#566170"


def month_number(day):
    return day.year * 12 + day.month - 1


def read_samples(history_path):
    entries = json.loads(history_path.read_text(encoding="utf-8"))["samples"]
    samples = {}
    for key, entry in entries.items():
        day = date.fromisoformat(key)
        count = entry["stars"]
        if day.day not in SAMPLE_DAYS or type(count) is not int or count < 0:
            raise ValueError(f"Invalid star sample: {key}")
        samples[day] = count
    if not samples:
        raise ValueError("No star samples to plot")
    return samples


def render(samples, output_path):
    first_month = month_number(max(samples)) - 11
    points = [float("nan")] * 36
    observed = []
    # Missing slots stay empty so gaps cannot be mistaken for observations.
    for day, count in sorted(samples.items()):
        month_offset = month_number(day) - first_month
        if 0 <= month_offset < 12:
            position = month_offset * 3 + SAMPLE_DAYS.index(day.day)
            points[position] = count
            observed.append((position, count))

    month_labels = []
    for month in range(first_month, first_month + 12):
        year, index = divmod(month, 12)
        label = MONTH_NAMES[index]
        if index == 0 or month == first_month:
            label = f"{label} '{year % 100:02d}"
        month_labels.append(label)

    fig, ax = plt.subplots(figsize=(17.85, 4.59), dpi=100, facecolor="#fcfdfe")
    ax.set_facecolor("#fcfdfe")
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#e4e9ef", linewidth=1)
    ax.fill_between(range(36), points, color="#dbeafe", alpha=0.75)
    ax.plot(range(36), points, color=BLUE, linewidth=2.6, marker="o", markersize=5,
            markeredgewidth=0.6, markeredgecolor="white")
    ax.set_xlim(-0.6, 35.7)
    ax.set_ylim(0, max(10, max(count for _, count in observed) * 1.14))
    ax.set_xticks(range(1, 36, 3), labels=month_labels)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True, min_n_ticks=4))
    ax.set_ylabel("Cumulative stars", fontsize=15, labelpad=15, color=TEXT)
    ax.tick_params(axis="both", length=0, pad=11, labelsize=15, colors=TEXT)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.spines["bottom"].set_color("#cbd5e1")
    position, count = observed[-1]
    ax.annotate(str(count), (position, count), textcoords="offset points", xytext=(0, 10),
                ha="center", fontsize=15, fontweight="bold", color="#1d4ed8")
    fig.subplots_adjust(left=0.062, right=0.996, top=0.96, bottom=0.105)
    fig.savefig(output_path)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("history", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(read_samples(args.history), args.output)


if __name__ == "__main__":
    main()
