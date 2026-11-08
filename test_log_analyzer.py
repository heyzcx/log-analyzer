#!/usr/bin/env python3
"""Smoke tests for log_analyzer.py. Run: python3 test_log_analyzer.py"""

import subprocess
import sys
import tempfile
from pathlib import Path

SAMPLE = """\
2026-11-08 13:00:01 INFO Server started
2026-11-08 13:02:30 ERROR Connection refused to db:5432
2026-11-08 13:02:31 ERROR Connection refused to db:5432
2026-11-08 13:04:44 CRITICAL Out of memory
2026-11-08 13:05:10 DEBUG Retrying request
plain line without a level
"""

SCRIPT = Path(__file__).with_name("log_analyzer.py")


def run(*args, input_text=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          input=input_text, capture_output=True, text=True)


def main():
    with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as fh:
        fh.write(SAMPLE)
        log = fh.name

    out = run(log)
    assert out.returncode == 0, out.stderr
    assert "Total lines: 6" in out.stdout, out.stdout
    assert "ERROR     2" in out.stdout, out.stdout
    assert "CRITICAL  1" in out.stdout, out.stdout
    assert "UNKNOWN   1" in out.stdout, out.stdout
    assert "2x  Connection refused to db:5432" in out.stdout, out.stdout

    out = run(log, "--json")
    assert '"total_lines": 6' in out.stdout, out.stdout
    assert '"first_seen": "2026-11-08T13:00:01"' in out.stdout, out.stdout

    out = run(input_text=SAMPLE)  # stdin mode
    assert out.returncode == 0 and "Total lines: 6" in out.stdout, out.stdout

    out = run(log, "--level", "ERROR", "--top", "1")
    assert "ERROR     2" in out.stdout and "INFO" not in out.stdout, out.stdout

    out = run("/nonexistent.log")
    assert out.returncode == 2, out.returncode

    print("All smoke tests passed.")


if __name__ == "__main__":
    main()
