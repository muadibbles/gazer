#!/usr/bin/env python3
"""
gazer/time_scheduler.py — Time-of-day drive profile scheduler

Fires pressure commands on a day curve to shift the robot's baseline
temperament throughout the day.  Runs continuously, injecting pressure
every INTERVAL_S seconds; the drive engine's natural decay means the
effect fades quickly if the scheduler is stopped.

Day curve (hour ranges, local time):
    05–09  morning   curious↑  alert↑           — bright, alert, exploratory
    09–17  day       (neutral baseline)          — steady working temperament
    17–21  evening   idle↑                      — winding down, calm
    21–05  night     sleepy↑  resting↑          — drowsy, minimal reactivity

Usage:
    python3 time_scheduler.py                    Run with defaults
    python3 time_scheduler.py --interval 90      Fire every 90 s (default 120)
    python3 time_scheduler.py --dry-run          Print schedule without sending

Environment:
    WS_URL=ws://host:8765   Override relay URL (default ws://localhost:8765)
    TZ=America/New_York     Set timezone for local-time calculation

Requires:
    pip install websockets
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

URL        = os.environ.get("WS_URL", "ws://localhost:8765")
INTERVAL_S = 120    # seconds between pressure injections

# Pressure injections per time-of-day period.
# Each entry: (behavior, amount) — amount is added to current pressure.
# Positive amounts boost states above their driveProfile baseline.
# Values decay toward driveProfile targets between injections.
PERIODS = {
    #  hour range   label       pressures to inject
    "morning": {
        "hours":   (5, 9),
        "label":   "morning",
        "boosts":  [("curious", 0.20), ("alert", 0.15)],
    },
    "day": {
        "hours":   (9, 17),
        "label":   "day",
        "boosts":  [],   # driveProfile baseline (idle+curious) is sufficient
    },
    "evening": {
        "hours":   (17, 21),
        "label":   "evening",
        "boosts":  [("idle", 0.20)],
    },
    "night": {
        "hours":   (21, 29),  # 29 = wraps to 5 (handled below)
        "label":   "night",
        "boosts":  [("sleepy", 0.40), ("resting", 0.25)],
    },
}


def current_period() -> dict:
    """Return the PERIODS entry that matches the current local hour."""
    h = datetime.now().hour
    for period in PERIODS.values():
        lo, hi = period["hours"]
        # Night wraps past midnight: hours 21–24 or 0–5
        if lo >= 24:
            lo -= 24
        if hi > 24:
            # e.g. (21, 29) → matches h >= 21 OR h < 5
            if h >= lo or h < (hi - 24):
                return period
        else:
            if lo <= h < hi:
                return period
    # Fallback: day
    return PERIODS["day"]


# ── WebSocket helpers ─────────────────────────────────────────────────────────

async def ws_connect():
    delay = 2
    while True:
        try:
            ws = await websockets.connect(URL)
            print(f"connected to {URL}")
            return ws
        except OSError as e:
            print(f"connect failed: {e}  retrying in {delay}s…")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)


async def send(ws, msg: dict):
    try:
        await ws.send(json.dumps(msg))
        return ws
    except Exception:
        return await ws_connect()


# ── Main loop ─────────────────────────────────────────────────────────────────

async def run(interval: int, dry_run: bool):
    ws = None if dry_run else await ws_connect()

    print("gazer time scheduler running — Ctrl-C to stop\n")
    prev_label = None

    while True:
        period = current_period()
        label  = period["label"]
        boosts = period["boosts"]

        if label != prev_label:
            print(f"period: {label}  ({datetime.now().strftime('%H:%M')})")
            prev_label = label

        if boosts:
            for behavior, amount in boosts:
                msg = {"type": "pressure", "state": behavior, "amount": amount}
                if dry_run:
                    print(f"  [dry-run] → {msg}")
                else:
                    print(f"  pressure {behavior} +{amount}")
                    ws = await send(ws, msg)
        else:
            if dry_run:
                print(f"  [dry-run] no boosts ({label} baseline)")

        await asyncio.sleep(interval)


def main():
    p = argparse.ArgumentParser(description="gazer time-of-day scheduler")
    p.add_argument("--interval", type=int,   default=INTERVAL_S,
                   help=f"Seconds between injections (default {INTERVAL_S})")
    p.add_argument("--dry-run",  action="store_true",
                   help="Print what would be sent without connecting")
    args = p.parse_args()

    h = datetime.now().hour
    period = current_period()
    print("gazer time scheduler")
    print(f"  server   : {URL}")
    print(f"  interval : {args.interval}s")
    print(f"  time     : {datetime.now().strftime('%H:%M')}  → period: {period['label']}")
    print()

    try:
        asyncio.run(run(args.interval, args.dry_run))
    except KeyboardInterrupt:
        pass
    print("\nstopped")


if __name__ == "__main__":
    main()
