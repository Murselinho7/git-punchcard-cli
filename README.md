# Git Punchcard

![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)
![Git](https://img.shields.io/badge/git-log-F05032?logo=git&logoColor=white)
![Chart](https://img.shields.io/badge/chart-7%C3%9724%20punchcard-0F766E)
![Dependencies](https://img.shields.io/badge/dependencies-zero-success)
![License](https://img.shields.io/badge/license-MIT-blue)

A small Git analytics CLI. From any repository it reads `git log` and prints a weekday-by-hour punchcard, the commit total, and the most active authors. There is no install step and no third-party package. The script uses `argparse`, `subprocess`, `collections`, `datetime`, and `sys` from the standard library.

## Run

`git` must be on `PATH`. Open a terminal whose current directory is the repository:

```bash
python path/to/9-git-punchcard-cli/punchcard.py
```

If you are already inside this folder and it is itself a Git checkout, `python punchcard.py` is enough. The tool reads the repository you are standing in, not the folder that contains the script.

```bash
python punchcard.py --author Hopper
python punchcard.py --since "2026-01-05 00:00"
python punchcard.py --author Ada --since "1 year ago"
```

`--author` is passed straight to `git log --author`, so it is a Git regular expression matched against the author name. `--since` is passed straight to `git log --since`. A date with no clock time is filled in by Git's date parser using the current time of day, so `2026-01-05` does not mean midnight. Pass an explicit time when the boundary matters.

Outside a repository the command exits with status 1 and prints `This directory is not a Git repository.`

## How the matrix is counted

Each commit contributes one mark to the weekday and hour stored on its author date. That clock is the author's local time, the offset Git recorded, not the timezone of the machine running the report. Rows run Sunday through Saturday. Columns run `00` through `23`.

The darkest cell in the current result is the peak. Every other non-empty cell is scaled against that peak:

| Glyph | Meaning |
| --- | --- |
| `·` | no commits |
| `░` | low |
| `▒` | medium |
| `▓` | high |
| `█` | peak |

The author list shows up to eight names, ordered by commit count. The bar is scaled to the busiest author in that list.

## Example

This is the report for a 12-commit sample history. Ada commits on Sunday night and Monday morning, Grace on Wednesday afternoon, and Linus on Friday evening and Saturday.

```text
Git punchcard
all commits in this repository

     000000000011111111112222
     012345678901234567890123
Sun  ······················▒·
Mon  ·········█·▒············
Tue  ··············▒·········
Wed  ···············█▒·······
Thu  ··········▒·············
Fri  ··················▒··▒··
Sat  ············▒···········

· none   ░ low   ▒ medium   ▓ high   █ peak

12 commits · 3 authors
Peak  Mon 09:00 · 2 commits

Top contributors
  5  ████████████████  Ada Lovelace
  4  ████████████····  Grace Hopper
  3  █████████·······  Linus Torvalds
```

The same history filtered with `--author Hopper`:

```text
Git punchcard
filter  author=Hopper

     000000000011111111112222
     012345678901234567890123
Sun  ························
Mon  ························
Tue  ························
Wed  ···············█▒·······
Thu  ··········▒·············
Fri  ························
Sat  ························

· none   ░ low   ▒ medium   ▓ high   █ peak

4 commits · 1 author
Peak  Wed 15:00 · 2 commits

Top contributors
  4  ████████████████  Grace Hopper
```

The two hour header rows are tens and ones, so column `15` is the `1` above the `5`. Wednesday's `█` sits on 15:00 and the following `▒` sits on 16:00.
