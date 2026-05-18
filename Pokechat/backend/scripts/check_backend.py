#!/usr/bin/env python3
"""
Smoke test the running Flask API: GET /chat/hello, then GET /chat/query with a sample question.

Requires the server already running (e.g. `make backend`). Uses only the standard library.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="http://127.0.0.1:3001",
        help="Backend base URL (default: %(default)s)",
    )
    parser.add_argument(
        "--query",
        default="What is HCI?",
        help="Question passed as q= to /chat/query (default: %(default)s)",
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")

    # --- /chat/hello
    hello_url = f"{base}/chat/hello"
    try:
        with urllib.request.urlopen(hello_url, timeout=15) as resp:
            hello_body = resp.read().decode()
    except urllib.error.URLError as e:
        print(f"Failed to reach {hello_url}: {e}", file=sys.stderr)
        print("Start the API first (e.g. make backend).", file=sys.stderr)
        return 2

    if "Hello" not in hello_body:
        print(f"Unexpected /chat/hello body: {hello_body!r}", file=sys.stderr)
        return 1
    print(f"OK /chat/hello → {hello_body.strip()}")

    # --- /chat/query
    q = urllib.parse.quote(args.query, safe="")
    query_url = f"{base}/chat/query?q={q}"
    try:
        with urllib.request.urlopen(query_url, timeout=120) as resp:
            raw = resp.read().decode()
    except urllib.error.URLError as e:
        print(f"Failed /chat/query: {e}", file=sys.stderr)
        return 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"/chat/query non-JSON body:\n{raw}", file=sys.stderr)
        return 1

    if isinstance(data, dict) and "error" in data:
        print(f"/chat/query error: {data['error']}", file=sys.stderr)
        return 1

    print(f"OK /chat/query?q={args.query!r} →")
    print(json.dumps(data, indent=2) if isinstance(data, (list, dict)) else data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
