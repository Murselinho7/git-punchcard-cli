#!/usr/bin/env python3
"""Git commit punchcard. Standard library only.

Reads `git log` from the current repository and prints a 7 by 24 matrix of
author-local weekday and hour, plus the busiest authors.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from datetime import datetime


DAYS = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
GLYPHS = "·░▒▓█"
SEPARATOR = "\x1f"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Print a GitHub-style commit punchcard for the current repository."
    )
    parser.add_argument("--author", help="Author filter, passed to git log --author")
    parser.add_argument("--since", help="Start date, passed to git log --since")
    args = parser.parse_args(argv)
    configure_stdio()
    try:
        commits = load_commits(args.author, args.since)
    except FileNotFoundError:
        print("git was not found on PATH.", file=sys.stderr)
        return 1
    except GitError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(render(commits, args.author, args.since))
    return 0


def configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


class GitError(Exception):
    pass


def load_commits(author, since):
    command = [
        "git",
        "--no-pager",
        "log",
        "-z",
        "--pretty=format:%ad%x1f%an",
        "--date=iso",
    ]
    if author:
        command.extend(["--author", author])
    if since:
        command.extend(["--since", since])
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", "replace").strip()
        lowered = message.lower()
        if "not a git repository" in lowered:
            raise GitError("This directory is not a Git repository.")
        raise GitError(message or "git log failed.")
    commits = []
    for chunk in completed.stdout.split(b"\0"):
        if not chunk.strip():
            continue
        record = chunk.decode("utf-8", "replace").strip()
        when_text, marker, name = record.partition(SEPARATOR)
        if marker != SEPARATOR or not name:
            continue
        when = parse_author_clock(when_text)
        if when is None:
            continue
        commits.append((when, name.strip()))
    return commits


def parse_author_clock(text):
    """Return the author-local clock time, ignoring the numeric offset."""
    text = text.strip()
    if len(text) < 19:
        return None
    try:
        return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def day_index(when):
    return (when.weekday() + 1) % 7


def glyph(count, peak):
    if count <= 0 or peak <= 0:
        return GLYPHS[0]
    level = (count * 4 + peak - 1) // peak
    if level < 1:
        level = 1
    if level > 4:
        level = 4
    return GLYPHS[level]


def render(commits, author, since):
    matrix = [[0 for _hour in range(24)] for _day in range(7)]
    authors = Counter()
    for when, name in commits:
        matrix[day_index(when)][when.hour] += 1
        authors[name] += 1
    lines = ["Git punchcard", filter_line(author, since), ""]
    lines.extend(matrix_lines(matrix))
    lines.append("")
    lines.append(summary_line(commits, authors))
    peak = peak_line(matrix)
    if peak:
        lines.append(peak)
    lines.append("")
    lines.extend(contributor_lines(authors))
    return "\n".join(lines)


def filter_line(author, since):
    parts = []
    if author:
        parts.append("author=" + author)
    if since:
        parts.append("since=" + since)
    if not parts:
        return "all commits in this repository"
    return "filter  " + "  ".join(parts)


def matrix_lines(matrix):
    peak = max(cell for row in matrix for cell in row)
    indent = "     "
    tens = indent + "".join(str(hour // 10) for hour in range(24))
    ones = indent + "".join(str(hour % 10) for hour in range(24))
    lines = [tens, ones]
    for index, name in enumerate(DAYS):
        cells = "".join(glyph(matrix[index][hour], peak) for hour in range(24))
        lines.append("%-5s%s" % (name, cells))
    lines.append("")
    lines.append("· none   ░ low   ▒ medium   ▓ high   █ peak")
    return lines


def summary_line(commits, authors):
    commit_word = "commit" if len(commits) == 1 else "commits"
    author_word = "author" if len(authors) == 1 else "authors"
    return "%d %s · %d %s" % (len(commits), commit_word, len(authors), author_word)


def peak_line(matrix):
    peak = 0
    where = None
    for day, row in enumerate(matrix):
        for hour, count in enumerate(row):
            if count > peak:
                peak = count
                where = (day, hour)
    if not where or peak <= 0:
        return ""
    day, hour = where
    noun = "commit" if peak == 1 else "commits"
    return "Peak  %s %02d:00 · %d %s" % (DAYS[day], hour, peak, noun)


def contributor_lines(authors):
    lines = ["Top contributors"]
    if not authors:
        lines.append("  no commits matched")
        return lines
    ranked = sorted(authors.items(), key=lambda item: (-item[1], item[0].lower()))
    shown = ranked[:8]
    top = shown[0][1]
    count_width = max(len(str(count)) for _name, count in shown)
    for name, count in shown:
        lines.append("  %*d  %s  %s" % (count_width, count, bar(count, top), name))
    hidden = len(ranked) - len(shown)
    if hidden:
        lines.append("  and %d more" % hidden)
    return lines


def bar(count, top, width=16):
    if top <= 0 or count <= 0:
        return "·" * width
    filled = (count * width) // top
    if filled < 1:
        filled = 1
    if filled > width:
        filled = width
    return "█" * filled + "·" * (width - filled)


if __name__ == "__main__":
    sys.exit(main())
