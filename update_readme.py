#!/usr/bin/env python3
"""Refresh the latest-releases list in README.md."""
import json
import pathlib
import re
import subprocess

USER = "DanielOu1208"
LIMIT = 5
QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false) {
      nodes {
        name
        releases(first: 5, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes { name tagName url publishedAt isPrerelease isDraft }
        }
      }
    }
  }
}
"""


def latest_releases():
    out = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"login={USER}"],
        check=True, capture_output=True, text=True,
    ).stdout
    releases = []
    for repo in json.loads(out)["data"]["user"]["repositories"]["nodes"]:
        stable = [
            r for r in repo["releases"]["nodes"]
            if r["publishedAt"] and not r["isPrerelease"] and not r["isDraft"]
        ]
        if stable:
            releases.append({**stable[0], "repo": repo["name"]})
    releases.sort(key=lambda r: r["publishedAt"], reverse=True)
    return releases[:LIMIT]


def title(release):
    # "AeriVoice 0.2.2 — Paste fixes" -> "AeriVoice 0.2.2"; bare tags get the repo name.
    name = (release["name"] or "").split(" — ")[0].strip()
    if not name or re.match(r"v?\d", name):
        return f"{release['repo']} {release['tagName']}"
    return name


def render(releases):
    return "\n".join(
        f"- [{title(r)}]({r['url']}) · {r['publishedAt'][:10]}" for r in releases
    )


readme = pathlib.Path(__file__).with_name("README.md")
block = f"<!-- releases:start -->\n{render(latest_releases())}\n<!-- releases:end -->"
readme.write_text(re.sub(
    r"<!-- releases:start -->.*?<!-- releases:end -->",
    lambda _: block, readme.read_text(), flags=re.S,
))
