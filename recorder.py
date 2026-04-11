#!/usr/bin/env python3
"""
gazer/recorder.py — Record gazer state packets to JSONL.

Connects to the relay server, listens for state broadcasts from the browser,
and appends each packet as a line of JSON to a timestamped file.

Each line is a complete state snapshot:
  {"type":"state","t":<ms>,"data":{...}}

The "data" object contains:
  attn, affect, behavior     — current behavior state
  poiIdx, poiLabel           — attended POI
  gazeX, gazeY               — eye gaze (-1..1)
  head3DYaw, head3DPitch     — head orientation (degrees)
  body3DYaw                  — body yaw (degrees)
  blinking                   — bool
  amplitude                  — smoothed mouth amplitude (0..1)
  drive.enabled              — drive system active
  drive.pressure             — {behavior: float} pressure map
  activeTask                 — null | {action, mode, source, target, phase}
  pois[]                     — [{label, familiarity, attention}]

Usage:
    python3 recorder.py                   write to ./recordings/
    python3 recorder.py <output_dir>      write to specified directory

Output file: <output_dir>/session_YYYYMMDD_HHMMSS.jsonl

Override server URL with WS_URL env var:
    WS_URL=ws://192.168.1.10:8765 python3 recorder.py

Requires:
    pip install websockets
"""

import asyncio
import json
import os
import sys
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

URL        = os.environ.get("WS_URL", "ws://localhost:8765")
OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "recordings"


async def record():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"session_{ts}.jsonl")

    total        = 0
    reconnect_s  = 2

    print(f"gazer recorder")
    print(f"  output : {path}")
    print(f"  server : {URL}")
    print()

    while True:
        try:
            async with websockets.connect(URL) as ws:
                reconnect_s = 2  # reset backoff on successful connection
                print(f"connected — recording…  (Ctrl-C to stop)")
                with open(path, "a") as f:
                    async for raw in ws:
                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        if msg.get("type") != "state":
                            continue  # ignore commands relayed from other clients

                        f.write(raw + "\n")
                        total += 1

                        if total % 200 == 0:
                            # Flush and print progress every 200 packets (~10 s at 20 Hz)
                            f.flush()
                            d    = msg.get("data", {})
                            beh  = d.get("behavior", "—")
                            poi  = d.get("poiLabel", "—")
                            print(f"  {total:>6} packets   beh={beh:<18} poi={poi}")

        except (OSError, websockets.exceptions.ConnectionClosed) as e:
            print(f"disconnected: {e}")
            print(f"  retrying in {reconnect_s}s…")
            await asyncio.sleep(reconnect_s)
            reconnect_s = min(reconnect_s * 2, 30)

        except asyncio.CancelledError:
            break


def main():
    try:
        asyncio.run(record())
    except KeyboardInterrupt:
        pass
    print("\nrecording stopped")


if __name__ == "__main__":
    main()
