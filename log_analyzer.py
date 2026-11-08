#!/usr/bin/env python3
"""log-analyzer: summarize log files by severity, top errors and time range.

Usage:
    python3 log_analyzer.py app.log [other.log ...]
    cat app.log | python3 log_analyzer.py
    python3 log_analyzer.py app.log --level ERROR --top 5 --json

Zero dependencies, standard library only.
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime

LEVELS = ("CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG", "TRACE")
# A severity token at the start of a line, or bracketed/after a timestamp.
LEVEL_RE = re.compile(
    r"(?:^|\s|\[)(CRITICAL|FATAL|ERROR|WARN(?:ING)?|INFO|DEBUG|TRACE)(?:\b|\])",
    re.IGNORECASE,
)
# Common timestamp shapes: 2026-11-08 13:15:00, 2026-11-08T13:15:00Z, 11/08/2026 13:15:00
TS_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})"
    r"|(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})"
)
TS_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
              "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y %H:%M:%S")


def normalize_level(raw):
    """Map a matched severity token to its canonical name."""
    upper = raw.upper()
    if upper == "WARNING":
        return "WARN"
    if upper == "FATAL":
        return "CRITICAL"
    return upper


def parse_timestamp(line):
    """Return a datetime if the line starts with a recognizable timestamp."""
    match = TS_RE.search(line)
    if not match:
        return None
    text = match.group(0)
    for fmt in TS_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def message_after_level(line, level):
    """Strip timestamp and severity token, leaving the message text."""
    text = TS_RE.sub("", line, count=1)
    text = re.sub(r"(?i)\b" + level + r"\b", "", text, count=1)
    text = re.sub(r"^[\s\[\]:|-]+", "", text)
    return text.strip()[:200]


def analyze(lines):
    counts = Counter()
    messages = Counter()
    first_ts = last_ts = None
    total = 0
    for line in lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        total += 1
        ts = parse_timestamp(line)
        if ts is not None:
            first_ts = ts if first_ts is None or ts < first_ts else first_ts
            last_ts = ts if last_ts is None or ts > last_ts else last_ts
        match = LEVEL_RE.search(line)
        if match:
            level = normalize_level(match.group(1))
            counts[level] += 1
            if level in ("ERROR", "CRITICAL"):
                msg = message_after_level(line, match.group(1))
                if msg:
                    messages[msg] += 1
        else:
            counts["UNKNOWN"] += 1
    return {
        "total_lines": total,
        "by_level": dict(counts),
        "top_errors": messages.most_common(10),
        "first_seen": first_ts.isoformat() if first_ts else None,
        "last_seen": last_ts.isoformat() if last_ts else None,
    }


def read_lines(paths):
    if not paths:
        yield from sys.stdin
        return
    for path in paths:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                yield from fh
        except OSError as exc:
            print(f"log-analyzer: cannot read {path}: {exc}", file=sys.stderr)
            sys.exit(2)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Summarize log files: counts by severity, top errors, time range.")
    parser.add_argument("files", nargs="*", help="log files to analyze (default: stdin)")
    parser.add_argument("--level", choices=[lv for lv in LEVELS if lv != "WARNING"] + ["UNKNOWN"],
                        help="only count lines of this severity in the top-errors list")
    parser.add_argument("--top", type=int, default=10,
                        help="how many top error messages to show (default: 10)")
    parser.add_argument("--json", action="store_true", help="print the summary as JSON")
    args = parser.parse_args(argv)

    result = analyze(read_lines(args.files))
    if args.level:
        result["by_level"] = {args.level: result["by_level"].get(args.level, 0)}
    result["top_errors"] = result["top_errors"][: args.top]

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    print(f"Total lines: {result['total_lines']}")
    if result["first_seen"]:
        print(f"Time range:  {result['first_seen']} .. {result['last_seen']}")
    print("By severity:")
    order = ["CRITICAL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE", "UNKNOWN"]
    for level in order:
        count = result["by_level"].get(level, 0)
        if count:
            print(f"  {level:<9} {count}")
    if result["top_errors"]:
        print(f"Top {len(result['top_errors'])} error messages:")
        for msg, count in result["top_errors"]:
            print(f"  {count:>4}x  {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
