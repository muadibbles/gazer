#!/usr/bin/env python3
"""
gazer/recorder.py — Record gazer state packets to JSONL.

Connects to the relay server, listens for state broadcasts from the browser,
and appends each packet as a line of JSON to a timestamped file.

Normal mode records only `type: "state"` packets.
Verbose mode (-v / --verbose) also:
  - Records ALL message types (events, commands, state) so you can see
    what triggered a behavior change.
  - Prints real-time transition alerts whenever attn, affect, POI, or
    task changes.
  - Prints a pressure dashboard every 5 s showing the full behavior
    pressure ranking.

Usage:
    python3 recorder.py                         write state to ./recordings/
    python3 recorder.py <output_dir>            write to specified directory
    python3 recorder.py -v                      verbose: all messages + live dashboard
    python3 recorder.py -v <output_dir>         verbose + custom output dir
    python3 recorder.py -q                      quiet: record with no console output

Override server URL:
    WS_URL=ws://192.168.1.10:8765 python3 recorder.py -v

Output file: <output_dir>/session_YYYYMMDD_HHMMSS.jsonl

Requires:
    pip install websockets
"""

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

# ── Argument parsing (keep it simple, no argparse dependency) ──────────────
args       = sys.argv[1:]
VERBOSE    = any(a in ("-v", "--verbose") for a in args)
QUIET      = any(a in ("-q", "--quiet")   for a in args)
pos_args   = [a for a in args if not a.startswith("-")]
OUTPUT_DIR = pos_args[0] if pos_args else "recordings"
URL        = os.environ.get("WS_URL", "ws://localhost:8765")

# Behavior pressure bar width
BAR_WIDTH  = 16
# How many state packets between pressure snapshots in verbose mode (~5 s at 20 Hz)
PRESSURE_EVERY = 100


def bar(value: float, width: int = BAR_WIDTH) -> str:
    """Render a float 0..1 as a filled ASCII bar."""
    filled = round(value * width)
    return "█" * filled + "░" * (width - filled)


def fmt_pressure(pressure: dict, active_attn: str) -> str:
    """Format the full pressure map sorted by value, highlighting the active state."""
    if not pressure:
        return "  (no pressure data)"
    sorted_p = sorted(pressure.items(), key=lambda x: x[1], reverse=True)
    lines = []
    for name, val in sorted_p:
        marker = " ← ACTIVE" if name == active_attn else ""
        lines.append(f"  {name:<14} {bar(val)}  {val:.3f}{marker}")
    return "\n".join(lines)


def elapsed(start_t: float) -> str:
    """Format seconds since start as MM:SS.mmm"""
    s = time.time() - start_t
    m = int(s // 60)
    return f"{m:02d}:{s % 60:06.3f}"


async def record():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix  = "_verbose" if VERBOSE else ""
    path    = os.path.join(OUTPUT_DIR, f"session_{ts}{suffix}.jsonl")

    total        = 0
    state_count  = 0
    reconnect_s  = 2
    start_t      = time.time()

    # Previous-state tracking for transition detection
    prev_attn    = None
    prev_affect  = None
    prev_poi     = None
    prev_task    = None
    last_pressure_snap = 0  # state packet count of last pressure printout

    if not QUIET:
        mode_str = "VERBOSE" if VERBOSE else "normal"
        print(f"gazer recorder  [{mode_str}]")
        print(f"  output : {path}")
        print(f"  server : {URL}")
        if VERBOSE:
            print(f"  recording: ALL message types")
            print(f"  console:   transitions + pressure every {PRESSURE_EVERY} state packets")
        print()

    while True:
        try:
            async with websockets.connect(URL) as ws:
                reconnect_s = 2
                if not QUIET:
                    print(f"[{elapsed(start_t)}] connected — recording…  (Ctrl-C to stop)")

                with open(path, "a") as f:
                    async for raw in ws:
                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        msg_type = msg.get("type", "unknown")
                        total   += 1

                        # ── Decide what to write ──────────────────────────
                        if VERBOSE:
                            # Save everything — tag with received timestamp
                            msg["_rx"] = time.time()
                            f.write(json.dumps(msg) + "\n")
                        elif msg_type == "state":
                            f.write(raw + "\n")
                        else:
                            continue  # non-verbose: skip non-state messages

                        # ── Verbose console output ────────────────────────
                        if VERBOSE and not QUIET and msg_type != "state":
                            # Print non-state messages immediately — these are
                            # events and commands that drive behavior changes.
                            val   = msg.get("value", "")
                            data  = msg.get("data", {})
                            extra = ""
                            if data:
                                extra = "  " + "  ".join(f"{k}={v}" for k, v in data.items()
                                                         if k not in ("type",))
                            print(f"[{elapsed(start_t)}] >> {msg_type:<10} {val}{extra}")

                        # ── State packet processing ───────────────────────
                        if msg_type != "state":
                            continue

                        state_count += 1
                        d = msg.get("data", {})

                        if not QUIET:
                            cur_attn   = d.get("attn")
                            cur_affect = d.get("affect")
                            cur_poi    = d.get("poiLabel")
                            cur_task   = d.get("activeTask")
                            cur_task_k = cur_task.get("action") if cur_task else None

                            if VERBOSE:
                                # ── Transition alerts ─────────────────────
                                if cur_attn != prev_attn:
                                    print(f"[{elapsed(start_t)}] attn:   {prev_attn or '—':<16} → {cur_attn}")
                                if cur_affect != prev_affect:
                                    print(f"[{elapsed(start_t)}] affect: {prev_affect or '—':<16} → {cur_affect}")
                                if cur_poi != prev_poi:
                                    print(f"[{elapsed(start_t)}] poi:    {prev_poi or 'none':<16} → {cur_poi or 'none'}")
                                if cur_task_k != prev_task:
                                    if cur_task_k:
                                        mode = cur_task.get("mode", "?")
                                        src  = d.get("pois", [{}])[cur_task.get("source", -1) or -1].get("label", "?") if cur_task.get("source") is not None else "?"
                                        tgt  = d.get("pois", [{}])[cur_task.get("target", -1) or -1].get("label", "?") if cur_task.get("target") is not None else "?"
                                        print(f"[{elapsed(start_t)}] task START: {cur_task_k}  {src}→{tgt}  [{mode}]")
                                    else:
                                        print(f"[{elapsed(start_t)}] task END")

                                # ── Periodic pressure dashboard ───────────
                                if state_count - last_pressure_snap >= PRESSURE_EVERY:
                                    last_pressure_snap = state_count
                                    pressure = d.get("drive", {}).get("pressure", {})
                                    gx = d.get("gazeX", 0)
                                    gy = d.get("gazeY", 0)
                                    hy = d.get("head3DYaw",   0)
                                    hp = d.get("head3DPitch", 0)
                                    by_ = d.get("body3DYaw",  0)
                                    print(f"\n[{elapsed(start_t)}] ── pressure snapshot  "
                                          f"(gaze {gx:+.2f},{gy:+.2f}  "
                                          f"head yaw={hy:+.1f}° pitch={hp:+.1f}°  "
                                          f"body={by_:+.1f}°) ──")
                                    print(fmt_pressure(pressure, cur_attn))
                                    print()

                            else:
                                # Normal mode: print progress every 200 state packets
                                if state_count % 200 == 0:
                                    beh = d.get("behavior", "—")
                                    poi = d.get("poiLabel", "—") or "—"
                                    print(f"  {state_count:>6} packets   attn={cur_attn:<16} poi={poi}")

                            prev_attn   = cur_attn
                            prev_affect = cur_affect
                            prev_poi    = cur_poi
                            prev_task   = cur_task_k

                        # Periodic flush to disk
                        if state_count % 100 == 0:
                            f.flush()

        except (OSError, websockets.exceptions.ConnectionClosed) as e:
            if not QUIET:
                print(f"[{elapsed(start_t)}] disconnected: {e}")
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
    if not QUIET:
        print("\nrecording stopped")


if __name__ == "__main__":
    main()
