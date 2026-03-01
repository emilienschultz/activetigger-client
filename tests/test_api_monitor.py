"""
Continuous API monitor — pings every ~1s, shows a live terminal chart.
Usage: python tests/test_api_monitor.py
Stop with Ctrl+C to see summary stats.
"""

import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from atclient.automate import load_api

INTERVAL = 1.0  # seconds between pings
BAR_CHAR = "\u2588"  # full block character


def render(results, term_width, term_height):
    """Build the terminal display string."""
    # Reserve lines: header(2) + blank(1) + stats(1) + blank(1) = 5
    max_rows = term_height - 5
    visible = results[-max(max_rows, 1) :]

    times = [r["response_time_ms"] for r in results if r["available"]]
    max_time = max(times) if times else 1
    errors = sum(1 for r in results if not r["available"])

    # Column layout: "  123 ms |████████"
    label_width = 10  # "  123 ms "
    separator = "| "
    bar_max = term_width - label_width - len(separator)
    if bar_max < 1:
        bar_max = 1

    lines = []
    lines.append(
        f"ActiveTigger API Monitor  (every {INTERVAL:.0f}s, {len(results)} pings)"
    )
    lines.append("")

    for r in visible:
        if r["available"]:
            ms = r["response_time_ms"]
            bar_len = max(1, int(ms / max_time * bar_max))
            label = f"{ms:6.0f} ms "
            lines.append(f"{label}{separator}{BAR_CHAR * bar_len}")
        else:
            label = "    -- ms "
            lines.append(f"{label}{separator}FAIL")

    lines.append("")
    if times:
        avg = sum(times) / len(times)
        lines.append(
            f"avg {avg:.0f} ms | min {min(times):.0f} ms | max {max(times):.0f} ms | errors {errors}/{len(results)}"
        )
    else:
        lines.append(f"No successful pings yet | errors {errors}/{len(results)}")

    return "\n".join(lines)


def main():
    api = load_api()
    results = []

    print("Starting API monitor (Ctrl+C to stop)...")
    try:
        while True:
            start = time.monotonic()
            result = api.ping()
            results.append(result)

            term = shutil.get_terminal_size((80, 24))
            output = render(results, term.columns, term.lines)

            os.system("clear" if os.name != "nt" else "cls")
            print(output)

            elapsed = time.monotonic() - start
            remaining = max(0.0, INTERVAL - elapsed)
            time.sleep(remaining)

    except KeyboardInterrupt:
        pass

    # Final summary
    print("\n--- Monitor Summary ---")
    print(f"Total pings: {len(results)}")
    times = [r["response_time_ms"] for r in results if r["available"]]
    errors = sum(1 for r in results if not r["available"])
    if times:
        print(f"Avg: {sum(times) / len(times):.0f} ms")
        print(f"Min: {min(times):.0f} ms")
        print(f"Max: {max(times):.0f} ms")
    print(f"Errors: {errors}/{len(results)}")


if __name__ == "__main__":
    main()
