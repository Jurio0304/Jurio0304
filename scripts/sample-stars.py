"""Record the Star total for the current ten-day slot in Shanghai time."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


def star_total(owner: str) -> tuple[int, int]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-star-history",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/users/{quote(owner, safe='')}/repos?type=owner&per_page=100"
    stars = 0
    projects = 0
    while url:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            for repo in json.load(response):
                if not repo["private"] and not repo["fork"]:
                    stars += repo["stargazers_count"]
                    projects += 1
            links = response.headers.get("Link", "").split(",")
            url = next(
                (link.split(";", 1)[0].strip().strip("<>")
                 for link in links if 'rel="next"' in link),
                "",
            )
    if not projects:
        raise RuntimeError(f"No public, non-fork repositories found for {owner}")
    return stars, projects


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("owner")
    parser.add_argument("history", type=Path)
    args = parser.parse_args()

    stars, projects = star_total(args.owner)
    observed = datetime.now(ZoneInfo("Asia/Shanghai"))
    slot_day = min((observed.day - 1) // 10, 2) * 10 + 1
    slot = observed.date().replace(day=slot_day).isoformat()

    history = json.loads(args.history.read_text(encoding="utf-8"))
    samples = history["samples"]
    previous = samples.get(slot, {})
    # Replace a historical estimate or record a changed count in this slot.
    if previous.get("source") != "snapshot" or previous.get("stars") != stars:
        samples[slot] = {
            "stars": stars,
            "source": "snapshot",
            "observed_at": observed.astimezone(timezone.utc).isoformat(timespec="seconds"),
        }
        args.history.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"{slot}: {stars} stars across {projects} public, non-fork repositories.")


if __name__ == "__main__":
    main()
