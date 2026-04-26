#!/usr/bin/env python3
"""
gazer/simulate.py — Synthetic sensor simulator for the gazer sim.

Generates realistic fake sensor events so you can watch the robot react
without a webcam, microphone, or physical hardware.

Simulates:
    - A virtual person who enters, wanders around the scene, occasionally
      speaks, sometimes gets close, then leaves after a while
    - Random environmental sounds (loud_sound, occasional startle)
    - Room-still event when no one is present for a while

Person lifecycle:
    away (idle) → arriving → present (wandering) → leaving → away …

While present the person:
    - Wanders on a smooth XZ path near the robot (look3D at 5 Hz)
    - Occasionally triggers speech bursts (speech_start / speech_end + amplitude)
    - Sometimes walks close (person_close)
    - After PRESENT_S seconds, departs

Usage:
    python3 simulate.py                   Run indefinitely
    python3 simulate.py --once            One full person visit then exit
    python3 simulate.py --seed 42         Reproducible random sequence
    python3 simulate.py --fast            Compressed time (3× speed)

Environment:
    WS_URL=ws://host:8765   Override relay URL (default ws://localhost:8765)

Requires:
    pip install websockets
"""

import argparse
import asyncio
import json
import math
import os
import random
import sys
import time

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

URL = os.environ.get("WS_URL", "ws://localhost:8765")

# ── Timing constants (seconds, real-time; --fast divides by FAST_FACTOR) ──────

AWAY_MIN       =  8.0   # min time between visits
AWAY_MAX       = 20.0   # max time between visits
PRESENT_MIN    = 20.0   # min visit duration
PRESENT_MAX    = 50.0   # max visit duration
APPROACH_DIST  =  1.2   # metres — person_close threshold
TRACK_HZ       =  5     # look3D commands per second while present
SPEECH_EVERY_MIN = 10.0 # min gap between speech events while present
SPEECH_EVERY_MAX = 20.0 # max gap
SPEECH_DUR_MIN =  2.5   # min speech duration
SPEECH_DUR_MAX =  8.0   # max speech duration
SOUND_EVERY_MIN = 15.0  # min gap between random sound events
SOUND_EVERY_MAX = 40.0  # max gap
STILL_AFTER    = 12.0   # seconds after person leaves → room_still
FAST_FACTOR    =  3.0   # time compression for --fast mode


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
        print("reconnecting…")
        return await ws_connect()


def _log(msg: str):
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}]  {msg}")


# ── Person path generator ─────────────────────────────────────────────────────

class PersonPath:
    """
    Smooth wandering path in XZ plane around a home position.
    Uses two overlaid sine waves for organic movement.
    """

    def __init__(self, home_x=0.0, home_z=3.0, radius=1.2):
        self.home_x  = home_x
        self.home_z  = home_z
        self.radius  = radius
        self.t       = random.uniform(0, math.tau)
        # Two sine components with incommensurate periods
        self.freq_a  = random.uniform(0.08, 0.14)   # rad/s
        self.freq_b  = random.uniform(0.05, 0.09)
        self.phase_b = random.uniform(0, math.tau)
        self.y       = 1.65                          # fixed head height

    def step(self, dt: float) -> tuple:
        self.t += dt
        x = self.home_x + self.radius * (
            0.6 * math.sin(self.freq_a * self.t) +
            0.4 * math.sin(self.freq_b * self.t + self.phase_b)
        )
        z = self.home_z + self.radius * 0.5 * (
            0.5 * math.cos(self.freq_a * self.t * 0.7) +
            0.5 * math.cos(self.freq_b * self.t * 1.3 + self.phase_b)
        )
        z = max(0.6, z)
        dist = math.sqrt(x ** 2 + z ** 2)
        scale = round(max(0.2, min(2.0, 2.5 / z)), 2)
        return round(x, 2), round(self.y, 2), round(z, 2), scale, round(dist, 2)


# ── Speech amplitude envelope ─────────────────────────────────────────────────

async def play_speech(ws, duration: float, speed: float) -> object:
    """Send speech_start, amplitude envelope, speech_end."""
    ws = await send(ws, {"type": "event", "value": "speech_start"})

    steps    = max(4, int(duration * 10))
    interval = duration / steps / speed

    for i in range(steps):
        t   = i / (steps - 1)
        # Amplitude: sine envelope with random bumps
        amp = 0.4 + 0.5 * math.sin(t * math.pi)
        amp += random.uniform(-0.1, 0.1)
        amp  = round(max(0.0, min(1.0, amp)), 3)
        ws   = await send(ws, {"type": "params", "data": {"amplitude": amp}})
        await asyncio.sleep(interval)

    ws = await send(ws, {"type": "params", "data": {"amplitude": 0.0}})
    ws = await send(ws, {"type": "event", "value": "speech_end"})
    return ws


# ── Simulation coroutines ─────────────────────────────────────────────────────

async def person_visit(ws, speed: float) -> object:
    """Simulate one complete person visit: arrive, wander, leave."""
    path = PersonPath(
        home_x=random.uniform(-1.5, 1.5),
        home_z=random.uniform(2.5, 4.0),
        radius=random.uniform(0.8, 1.5),
    )
    present_dur = random.uniform(PRESENT_MIN, PRESENT_MAX) / speed

    _log(f"person arriving  (visit duration ~{present_dur*speed:.0f}s real)")

    # Arrival
    x, y, z, scale, dist = path.step(0)
    ws = await send(ws, {"type": "event", "value": "person_entered",
                         "data": {"x": x, "y": y, "z": z}})
    ws = await send(ws, {"type": "event", "value": "face_detected",
                         "data": {"x": x, "y": y, "z": z, "scale": scale}})

    track_interval   = 1.0 / TRACK_HZ
    next_speech      = time.monotonic() + random.uniform(SPEECH_EVERY_MIN, SPEECH_EVERY_MAX) / speed
    next_face_detect = time.monotonic() + 3.0 / speed   # periodic pressure refresh
    last_track       = 0.0
    last_close_sent  = 0.0
    end_t            = time.monotonic() + present_dur
    speaking         = False

    while time.monotonic() < end_t:
        now = time.monotonic()
        x, y, z, scale, dist = path.step(track_interval)

        # look3D at TRACK_HZ
        if now - last_track >= track_interval:
            ws = await send(ws, {"type": "look3D", "x": x, "y": y, "z": z,
                                 "category": "person"})
            last_track = now

        # face_detected refresh
        if now >= next_face_detect:
            ws = await send(ws, {"type": "event", "value": "face_detected",
                                 "data": {"x": x, "y": y, "z": z, "scale": scale}})
            next_face_detect = now + 3.0 / speed

        # person_close
        if z < APPROACH_DIST and now - last_close_sent >= 2.0:
            _log(f"person close  z={z:.1f}m")
            ws = await send(ws, {"type": "event", "value": "person_close",
                                 "data": {"scale": scale}})
            last_close_sent = now

        # Speech burst
        if not speaking and now >= next_speech:
            speaking    = True
            speech_dur  = random.uniform(SPEECH_DUR_MIN, SPEECH_DUR_MAX)
            _log(f"speech start  (~{speech_dur:.1f}s)")
            ws = await play_speech(ws, speech_dur, speed)
            _log("speech end")
            speaking        = False
            next_speech     = now + random.uniform(SPEECH_EVERY_MIN, SPEECH_EVERY_MAX) / speed

        await asyncio.sleep(track_interval / speed)

    # Departure
    _log("person leaving")
    ws = await send(ws, {"type": "event", "value": "face_lost"})
    ws = await send(ws, {"type": "event", "value": "person_left"})
    return ws


async def ambient_sounds(ws_holder: list, speed: float):
    """Coroutine: fire random environmental sounds independently."""
    while True:
        gap = random.uniform(SOUND_EVERY_MIN, SOUND_EVERY_MAX) / speed
        await asyncio.sleep(gap)
        ws  = ws_holder[0]

        kind = random.choices(["loud", "startle"], weights=[0.85, 0.15])[0]
        if kind == "startle":
            scale = round(random.uniform(1.0, 1.8), 2)
            _log(f"startle  scale={scale}")
            ws_holder[0] = await send(ws, {"type": "event", "value": "startle",
                                           "data": {"scale": scale}})
        else:
            scale = round(random.uniform(0.5, 1.3), 2)
            _log(f"loud_sound  scale={scale}")
            ws_holder[0] = await send(ws, {"type": "event", "value": "loud_sound",
                                           "data": {"scale": scale}})


async def run(once: bool, speed: float):
    ws = await ws_connect()

    # Shared mutable holder so ambient_sounds can update ws on reconnect
    ws_holder = [ws]

    print()
    _log("simulator started")
    print()

    # Start ambient sound coroutine
    sound_task = asyncio.create_task(ambient_sounds(ws_holder, speed))

    visit_count = 0
    try:
        while True:
            # Wait between visits
            away = random.uniform(AWAY_MIN, AWAY_MAX) / speed
            _log(f"room empty  (next visit in ~{away*speed:.0f}s)")

            # room_still after a while
            still_t = min(away * 0.7, STILL_AFTER / speed)
            await asyncio.sleep(still_t)
            ws_holder[0] = await send(ws_holder[0],
                                      {"type": "event", "value": "room_still"})

            remaining = away - still_t
            if remaining > 0:
                await asyncio.sleep(remaining)

            # Person visit
            visit_count += 1
            ws_holder[0] = await person_visit(ws_holder[0], speed)

            if once:
                break

    except asyncio.CancelledError:
        pass
    finally:
        sound_task.cancel()
        try:
            await ws_holder[0].close()
        except Exception:
            pass


def main():
    p = argparse.ArgumentParser(description="gazer synthetic sensor simulator")
    p.add_argument("--once",        action="store_true",
                   help="Run one visit cycle then exit")
    p.add_argument("--seed",        type=int,   default=None,
                   help="Random seed for reproducible sequences")
    p.add_argument("--fast",        action="store_true",
                   help=f"Compress time {FAST_FACTOR:.0f}× (good for quick testing)")
    p.add_argument("--speed", "-s", type=float, default=None,
                   help="Explicit time multiplier (overrides --fast)")
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    speed = args.speed if args.speed else (FAST_FACTOR if args.fast else 1.0)

    print("gazer simulator")
    print(f"  server : {URL}")
    print(f"  speed  : {speed}×{'  (--fast)' if args.fast and not args.speed else ''}")
    print(f"  mode   : {'one visit' if args.once else 'continuous'}")
    if args.seed is not None:
        print(f"  seed   : {args.seed}")

    try:
        asyncio.run(run(args.once, speed))
    except KeyboardInterrupt:
        pass
    print("\nstopped")


if __name__ == "__main__":
    main()
