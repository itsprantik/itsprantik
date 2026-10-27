"""Draw stats.svg, streak.svg, langs.svg and year.svg from the GitHub GraphQL API.

  GITHUB_TOKEN=... python scripts/stats.py            # live data
  python scripts/stats.py --empty                     # zero-state graphics, no network

Public data only. Run once a day by .github/workflows/stats.yml.
"""
import argparse
import json
import os
import urllib.request
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from svgkit import W, fade, svg, text

OUT = Path(__file__).resolve().parent.parent
LOGIN = "itsprantik"

QUERY = """
query($login:String!){
  user(login:$login){
    followers{totalCount}
    contributionsCollection{
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar{
        totalContributions
        weeks{contributionDays{date contributionCount}}
      }
    }
    repositories(first:100, ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false){
      totalCount
      nodes{
        stargazerCount
        primaryLanguage{name}
        languages(first:10, orderBy:{field:SIZE, direction:DESC}){
          edges{size node{name}}
        }
      }
    }
  }
}
"""


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(payload["errors"])
    u = payload["data"]["user"]
    cc = u["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    repos = u["repositories"]["nodes"]
    by_bytes, by_repo = Counter(), Counter()
    for r in repos:
        for e in r["languages"]["edges"]:
            by_bytes[e["node"]["name"]] += e["size"]
        if r["primaryLanguage"]:
            by_repo[r["primaryLanguage"]["name"]] += 1
    return {
        "total": cal["totalContributions"],
        "commits": cc["totalCommitContributions"],
        "prs": cc["totalPullRequestContributions"],
        "issues": cc["totalIssueContributions"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "followers": u["followers"]["totalCount"],
        "weeks": cal["weeks"],
        "days": days,
        "by_bytes": by_bytes,
        "by_repo": by_repo,
    }


def empty():
    return {
        "total": 0, "commits": 0, "prs": 0, "issues": 0, "repos": 0, "stars": 0,
        "followers": 0, "weeks": [], "days": [], "by_bytes": Counter(), "by_repo": Counter(),
    }


def streaks(days):
    parsed = [(datetime.strptime(d["date"], "%Y-%m-%d").date(), d["contributionCount"]) for d in days]
    parsed.sort()
    best = (0, None, None)
    run, start = 0, None
    for dt, n in parsed:
        if n > 0:
            if run == 0:
                start = dt
            run += 1
            if run > best[0]:
                best = (run, start, dt)
        else:
            run = 0
    # current streak: walk back from today; an empty "today" doesn't break it yet
    cur = (0, None, None)
    i = len(parsed) - 1
    if i >= 0 and parsed[i][1] == 0:
        i -= 1
    end = parsed[i][0] if i >= 0 else None
    n = 0
    while i >= 0 and parsed[i][1] > 0:
        n += 1
        start = parsed[i][0]
        i -= 1
    if n:
        cur = (n, start, end)
    return cur, best


def span(a, b):
    if not a:
        return "no streak yet"
    f = lambda d: f"{d.strftime('%b')} {d.day}"
    return f(a) if a == b else f"{f(a)} - {f(b)}"


def stats_svg(s):
    body = [text(0, 52, f"{s['total']:,}", 48, "", 700, extra='opacity="0"') .replace("</text>", fade(0.1) + "</text>")]
    body.append(text(0, 78, "contributions in the last year", 13, "dim"))
    items = [("commits", s["commits"]), ("pull requests", s["prs"]), ("issues", s["issues"]),
             ("public repos", s["repos"]), ("stars", s["stars"]), ("followers", s["followers"])]
    for i, (label, val) in enumerate(items):
        x = 300 + (i % 3) * 107
        y = 34 + (i // 3) * 56
        t = text(x, y, f"{val:,}", 24, "", 700, extra='opacity="0"').replace("</text>", fade(0.2 + i * 0.08) + "</text>")
        body.append(t)
        body.append(text(x, y + 18, label, 11, "dim"))
    return svg(W, 100, "".join(body), "Contributions in the last year")


def streak_svg(s):
    cur, best = streaks(s["days"])
    body = []
    for i, (label, (n, a, b)) in enumerate([("current streak", cur), ("longest streak", best)]):
        x = i * 310
        body.append(
            text(x, 46, str(n), 44, "", 700, extra='opacity="0"').replace("</text>", fade(0.1 + i * 0.15) + "</text>")
        )
        body.append(text(x + 4 + 27 * len(str(n)) + 8, 46, "days", 14, "dim"))
        body.append(text(x, 70, label, 13, ""))
        body.append(text(x, 88, span(a, b), 11, "dim"))
    return svg(W, 100, "".join(body), "Current and longest streak")


def langs_svg(s):
    body = []
    cols = [("by bytes", s["by_bytes"]), ("by repo", s["by_repo"])]
    for ci, (title, counter) in enumerate(cols):
        x0 = ci * 310
        body.append(text(x0, 14, title, 12, "dim"))
        top = counter.most_common(6)
        total = sum(counter.values()) or 1
        if not top:
            body.append(text(x0, 44, "nothing yet", 12, "dim"))
            continue
        peak = top[0][1]
        for i, (name, v) in enumerate(top):
            y = 34 + i * 24
            body.append(text(x0, y + 10, name, 12))
            bw = max(2, 120 * v / peak)
            body.append(
                f'<rect x="{x0 + 100}" y="{y}" width="{bw:.1f}" height="11" rx="2" fill="var(--accent)">'
                f'<animate attributeName="width" from="0" to="{bw:.1f}" begin="{0.1 + i * 0.08:.2f}s" dur="0.7s" fill="freeze"/></rect>'
            )
            body.append(text(x0 + 100 + 128, y + 10, f"{100 * v / total:.0f}%", 11, "dim"))
    return svg(W, 34 + 6 * 24, "".join(body), "Top languages by bytes and by repo")


def year_svg(s):
    weeks = s["weeks"][-53:]
    counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    peak = max(counts, default=0)
    pitch_x, pitch_y, size = 11.5, 15, 13

    def ch(n):
        if n == 0:
            return ".", "faint"
        r = n / peak
        return (":", "dim") if r <= 0.25 else ("+", "") if r <= 0.5 else ("#", "") if r <= 0.75 else ("@", "accent")

    body = []
    for wi, w in enumerate(weeks):
        cells = []
        for d in w["contributionDays"]:
            dow = datetime.strptime(d["date"], "%Y-%m-%d").date().weekday()
            dow = (dow + 1) % 7  # Sunday first, like the GitHub graph
            c, cls = ch(d["contributionCount"])
            cells.append(text(wi * pitch_x + pitch_x / 2, 14 + dow * pitch_y, c, size, cls, 700 if c in "#@" else 400, "middle"))
        body.append(f'<g opacity="0">{"".join(cells)}{fade(wi * 0.02, 0.4)}</g>')
    if not weeks:
        body.append(text(0, 50, "nothing to draw yet - the daily action fills this in", 12, "dim"))
    body.append(text(0, 14 + 7 * pitch_y + 8, ". none    : a little    + some    # lots    @ peak", 11, "dim"))
    return svg(W, 14 + 7 * pitch_y + 20, "".join(body), "The last year, one character per day")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--empty", action="store_true")
    ap.add_argument("--demo", metavar="DIR", help="write fake-data graphics to DIR for layout checks")
    a = ap.parse_args()
    if a.demo:
        import random
        random.seed(1)
        start = date(2025, 10, 26)
        weeks, d = [], start
        for _ in range(53):
            wk = []
            for _ in range(7):
                wk.append({"date": d.isoformat(), "contributionCount": random.choice([0, 0, 0, 1, 2, 4, 7, 12])})
                d = date.fromordinal(d.toordinal() + 1)
            weeks.append({"contributionDays": wk})
        data = empty()
        data.update(total=412, commits=330, prs=21, issues=4, repos=9, stars=3, followers=12,
                    weeks=weeks, days=[x for w in weeks for x in w["contributionDays"]],
                    by_bytes=Counter({"TypeScript": 90000, "Java": 40000, "CSS": 12000, "HTML": 8000}),
                    by_repo=Counter({"TypeScript": 5, "Java": 2, "HTML": 1}))
        OUT = Path(a.demo)
        OUT.mkdir(parents=True, exist_ok=True)
    else:
        data = empty() if a.empty else fetch()
    for name, fn in [("stats", stats_svg), ("streak", streak_svg), ("langs", langs_svg), ("year", year_svg)]:
        (OUT / f"{name}.svg").write_text(fn(data))
        print("wrote", name + ".svg")
