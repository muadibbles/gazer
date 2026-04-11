#!/usr/bin/env python3
"""
gazer/replay.py — Replay a recorded JSONL session through the relay server.

Reads a session file written by recorder.py, re-sends each state packet
to the relay at the original cadence.  Connect a browser tab in Renderer Mode
to watch the playback.

Usage:
    python3 replay.py <session.jsonl>
    python3 replay.py <session.jsonl> --speed 2      Double speed
    python3 replay.py <session.jsonl> --speed 0.5    Half speed
    python3 replay.py <session.jsonl> --loop         Repeat until Ctrl-C
    python3 replay.py <session.jsonl> --speed 2 --loop

Environment:
    WS_URL=ws://host:8765   Override relay URL (default ws://localhost:8765)

Requires:
    pip install websockets
"""

import asyncio
import json
import os
import sys
import time

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

URL = os.environ.get("WS_URL", "ws://localhost:8765")


def load_packets(path: str) -> list:
    packets = []
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                pkt = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  skipping line {lineno}: {e}")
                continue
            if pkt.get("type") == "state":
                packets.append(pkt)
    return packets


async def ws_connect():
    delay = 2
    while True:
        try:
            ws = await websockets.connect(URL)
            return ws
        except OSError as e:
            print(f"connect failed: {e}  retrying in {delay}s…")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)


async def replay_once(packets: list, speed: float, ws) -> object:
    """Replay packet list once. Returns (possibly reconnected) ws."""
    for i, pkt in enumerate(packets):
        if i > 0:
            dt_ms = packets[i]["t"] - packets[i - 1]["t"]
            # Guard against negative deltas (clock jumps) and runaway gaps (> 5s)
            dt_s = max(0.0, min(dt_ms, 5000)) / 1000.0 / speed
            if dt_s > 0:
                await asyncio.sleep(dt_s)

        try:
            await ws.send(json.dumps(pkt))
        except Exception:
            print("connection lost — reconnecting…")
            ws = await ws_connect()
            await ws.send(json.dumps(pkt))

        if i % 200 == 0 and i > 0:
            d   = pkt.get("data", {})
            beh = d.get("behavior", "—")
            poi = d.get("poiLabel", "—")
            pct = i / len(packets) * 100
            print(f"  {i:>6}/{len(packets)}  ({pct:4.0f}%)   beh={beh:<18} poi={poi}")

    return ws


async def run(path: str, speed: float, loop: bool):
    packets = load_packets(path)
    if not packets:
        print("No state packets found in file.")
        sys.exit(1)

    duration_s = (packets[-1]["t"] - packets[0]["t"]) / 1000.0
    print(f"gazer replay")
    print(f"  file     : {path}")
    print(f"  packets  : {len(packets)}")
    print(f"  duration : {duration_s:.1f}s  →  playback {duration_s/speed:.1f}s at {speed}×")
    print(f"  server   : {URL}")
    print(f"  loop     : {'yes' if loop else 'no'}")
    print()

    ws = await ws_connect()
    print(f"connected — playing…\n")

    run_n = 0
    try:
        while True:
            run_n += 1
            if loop and run_n > 1:
                print(f"\n── loop {run_n} ──")
            ws = await replay_once(packets, speed, ws)
            if not loop:
                break
            # Brief pause between loops
            await asyncio.sleep(1.0)
    except asyncio.CancelledError:
        pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


def main():
    import argparse
    p = argparse.ArgumentParser(description="Replay a gazer JSONL session")
    p.add_argument("file",          help="Path to .jsonl session file")
    p.add_argument("--speed", "-s", type=float, default=1.0,
                   help="Playback speed multiplier (default 1.0)")
    p.add_argument("--loop",  "-l", action="store_true",
                   help="Loop the recording until Ctrl-C")
    args = p.parse_args()

    try:
        asyncio.run(run(args.file, args.speed, args.loop))
    except KeyboardInterrupt:
        pass
    print("\nplayback stopped")


if __name__ == "__main__":
    main()
