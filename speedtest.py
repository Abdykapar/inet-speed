#!/usr/bin/env python3
"""Measure download speed by fetching a URL several times sequentially."""

import argparse
import sys
import time
import urllib.error
import urllib.request

CHUNK_SIZE = 64 * 1024
USER_AGENT = "inet-speed/1.0"


def fetch(url: str, timeout: float) -> tuple[int, float]:
    """Download the whole response body. Returns (bytes, seconds)."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            # Avoid cached/compressed responses skewing the numbers.
            "Cache-Control": "no-cache",
            "Accept-Encoding": "identity",
        },
    )
    start = time.perf_counter()
    size = 0
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while chunk := response.read(CHUNK_SIZE):
            size += len(chunk)
    return size, time.perf_counter() - start


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure download speed by requesting a URL N times in a row."
    )
    parser.add_argument("url", help="http(s) address to download, e.g. a large image")
    parser.add_argument(
        "-n", "--requests", type=int, default=10,
        help="number of sequential requests (default: 10)",
    )
    parser.add_argument(
        "-t", "--timeout", type=float, default=30.0,
        help="timeout for each request, in seconds (default: 30)",
    )
    args = parser.parse_args()
    if not args.url.startswith(("http://", "https://")):
        parser.error("URL must start with http:// or https://")
    if args.requests < 1:
        parser.error("--requests must be >= 1")
    if args.timeout <= 0:
        parser.error("--timeout must be > 0")
    return args


def main() -> int:
    args = parse_args()
    total_bytes = 0
    total_time = 0.0

    print(f"URL: {args.url}", flush=True)
    for i in range(1, args.requests + 1):
        try:
            size, elapsed = fetch(args.url, args.timeout)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            print(f"Request {i}/{args.requests} failed: {reason}", file=sys.stderr)
            return 1
        total_bytes += size
        total_time += elapsed
        print(f"  #{i:>2}: {size / 1_000_000:8.2f} MB in {elapsed:6.3f} s", flush=True)

    if total_time == 0 or total_bytes == 0:
        print("Nothing was downloaded, cannot compute speed.", file=sys.stderr)
        return 1

    avg_time = total_time / args.requests
    mbit_per_s = total_bytes * 8 / total_time / 1_000_000
    mbyte_per_s = total_bytes / total_time / 1_000_000

    print()
    print(f"Requests:             {args.requests}")
    print(f"Average request time: {avg_time:.3f} s")
    print(f"Total downloaded:     {total_bytes / 1_000_000:.2f} MB ({total_bytes} bytes)")
    print(f"Download speed:       {mbit_per_s:.2f} Mbit/s ({mbyte_per_s:.2f} MB/s)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
