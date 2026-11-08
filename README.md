# log-analyzer

Summarize log files at a glance: counts by severity, the most frequent error
messages, and the time range covered. Zero-dependency Python CLI — just
Python 3.8+.

## Install

No installation needed. Clone and run:

```bash
git clone https://github.com/mrzhoucx/log-analyzer.git
cd log-analyzer
python3 log_analyzer.py --help
```

## Usage

```bash
# Analyze one or more log files
python3 log_analyzer.py /var/log/app.log

# Pipe logs in from stdin
tail -n 1000 /var/log/app.log | python3 log_analyzer.py

# JSON output for scripting
python3 log_analyzer.py app.log --json

# Only ERROR lines, show the top 5 messages
python3 log_analyzer.py app.log --level ERROR --top 5
```

## Example output

```
Total lines: 10
Time range:  2026-11-08T13:00:01 .. 2026-11-08T13:06:00
By severity:
  CRITICAL  1
  ERROR     3
  WARN      1
  INFO      3
  DEBUG     1
  UNKNOWN   1
Top 2 error messages:
     3x  Connection refused to db:5432
     1x  Out of memory, shutting down worker
```

## How it works

- Severity is detected case-insensitively (`CRITICAL`, `ERROR`, `WARN`/`WARNING`,
  `INFO`, `DEBUG`, `TRACE`); lines with no recognizable level count as `UNKNOWN`.
- Timestamps in `YYYY-MM-DD HH:MM:SS`, ISO 8601, or `MM/DD/YYYY HH:MM:SS`
  form are used for the reported time range.
- Error messages are deduplicated after stripping the timestamp and severity
  token, so repeated failures collapse into one line with a count.

## Tests

```bash
python3 test_log_analyzer.py
```
