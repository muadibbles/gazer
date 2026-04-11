#!/usr/bin/env python3
"""
gazer/audio.py — Audio input pipeline

Captures microphone input and fires gazer events based on amplitude and
voice activity detection.

Events fired:
    speech_start                      Voice onset (sustained above threshold)
    speech_end                        Voice end   (sustained silence)
    loud_sound   scale=<0..1>        Loud transient above LOUD_THRESH
    startle      scale=<0..1>        Sudden spike: N× louder than smoothed RMS

Continuous params:
    amplitude  0..1                   Smoothed RMS at ~20 Hz (drives mouth sync)

State machine:
    idle → (ONSET_CHUNKS above threshold) → speaking → (TAIL_CHUNKS below) → idle

Usage:
    python3 audio.py                      Default mic, default server
    python3 audio.py --device 2           Use audio input device index 2
    python3 audio.py --list-devices       Print available audio devices and exit
    python3 audio.py --threshold 0.03     Override speech RMS threshold

Environment:
    WS_URL=ws://host:8765   Override relay URL (default ws://localhost:8765)

Requires:
    pip install sounddevice numpy websockets
"""

import argparse
import asyncio
import json
import os
import queue
import sys
import time

try:
    import numpy as np
except ImportError:
    print("Missing dependency: pip install numpy")
    sys.exit(1)

try:
    import sounddevice as sd
except ImportError:
    print("Missing dependency: pip install sounddevice")
    sys.exit(1)

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

URL            = os.environ.get("WS_URL", "ws://localhost:8765")
SAMPLE_RATE    = 16000
BLOCK_SIZE     = 512        # ~32 ms per chunk at 16kHz
SPEECH_THRESH  = 0.02       # RMS threshold for voice onset
ONSET_CHUNKS   = 3          # consecutive chunks above threshold → speech_start
TAIL_CHUNKS    = 20         # consecutive chunks below threshold → speech_end
LOUD_THRESH    = 0.15       # RMS threshold for loud_sound event
STARTLE_THRESH = 0.50       # RMS threshold for startle event
STARTLE_MULT   = 5.0        # spike must be N× smoothed level to count as startle
AMP_HZ         = 20         # amplitude param send rate
AMP_SCALE      = 8.0        # RMS → 0..1 amplitude scale factor (tune to taste)

# ── Audio capture ─────────────────────────────────────────────────────────────

_audio_q: queue.Queue = queue.Queue()


def _audio_callback(indata, frames, time_info, status):
    _audio_q.put(indata[:, 0].copy())  # mono slice, copy to avoid mutation


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

async def run(device, threshold):
    global SPEECH_THRESH
    if threshold is not None:
        SPEECH_THRESH = threshold

    ws = await ws_connect()

    vad_state     = "idle"   # idle | speaking
    onset_count   = 0
    tail_count    = 0
    smooth        = 0.0      # exponentially smoothed RMS
    prev_smooth   = 0.0
    last_amp_sent = 0.0
    amp_interval  = 1.0 / AMP_HZ

    stream = sd.InputStream(
        device=device,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        dtype="float32",
        callback=_audio_callback,
    )

    print(f"listening — device={'default' if device is None else device}")
    print(f"  speech threshold : {SPEECH_THRESH:.3f} RMS")
    print(f"  loud threshold   : {LOUD_THRESH:.3f} RMS")
    print(f"  startle threshold: {STARTLE_THRESH:.3f} RMS")
    print()

    with stream:
        while True:
            # Drain the audio queue accumulated since last iteration
            chunks = []
            try:
                while True:
                    chunks.append(_audio_q.get_nowait())
            except queue.Empty:
                pass

            if not chunks:
                await asyncio.sleep(0.01)
                continue

            for chunk in chunks:
                rms = float(np.sqrt(np.mean(chunk ** 2)))

                # Smooth: fast attack, slow release
                alpha   = 0.35 if rms > smooth else 0.05
                prev_smooth = smooth
                smooth  = smooth * (1.0 - alpha) + rms * alpha

                now = time.monotonic()

                # ── Startle ────────────────────────────────────────────────────
                if (rms >= STARTLE_THRESH
                        and prev_smooth > 0.001
                        and rms / prev_smooth >= STARTLE_MULT):
                    scale = round(min(2.0, rms / STARTLE_THRESH), 2)
                    print(f"startle   rms={rms:.3f}  scale={scale}")
                    ws = await send(ws, {
                        "type": "event", "value": "startle",
                        "data": {"scale": scale},
                    })

                # ── Loud sound ─────────────────────────────────────────────────
                elif rms >= LOUD_THRESH:
                    scale = round(min(2.0, rms / LOUD_THRESH), 2)
                    ws = await send(ws, {
                        "type": "event", "value": "loud_sound",
                        "data": {"scale": scale},
                    })

                # ── Voice activity state machine ───────────────────────────────
                if vad_state == "idle":
                    if rms >= SPEECH_THRESH:
                        onset_count += 1
                        if onset_count >= ONSET_CHUNKS:
                            vad_state   = "speaking"
                            onset_count = 0
                            tail_count  = 0
                            print("speech start")
                            ws = await send(ws, {"type": "event", "value": "speech_start"})
                    else:
                        onset_count = 0

                elif vad_state == "speaking":
                    if rms < SPEECH_THRESH:
                        tail_count += 1
                        if tail_count >= TAIL_CHUNKS:
                            vad_state  = "idle"
                            tail_count = 0
                            print("speech end")
                            ws = await send(ws, {"type": "event", "value": "speech_end"})
                    else:
                        tail_count = 0

                # ── Amplitude param ────────────────────────────────────────────
                if now - last_amp_sent >= amp_interval:
                    amp = round(min(1.0, smooth * AMP_SCALE), 3)
                    ws = await send(ws, {"type": "params", "data": {"amplitude": amp}})
                    last_amp_sent = now

            await asyncio.sleep(0.01)


def main():
    p = argparse.ArgumentParser(description="gazer audio input pipeline")
    p.add_argument("--device",       type=int,   default=None,
                   help="Audio input device index (default: system default)")
    p.add_argument("--list-devices", action="store_true",
                   help="Print available audio devices and exit")
    p.add_argument("--threshold",    type=float, default=None,
                   help=f"Speech RMS onset threshold (default {SPEECH_THRESH})")
    args = p.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        sys.exit(0)

    print("gazer audio")
    print(f"  server : {URL}")
    print()

    try:
        asyncio.run(run(args.device, args.threshold))
    except KeyboardInterrupt:
        pass
    print("\nstopped")


if __name__ == "__main__":
    main()
