#!/usr/bin/env python3
"""
gazer/send.py — Send a one-shot command to the gazer relay server.

The message is forwarded to all connected browser tabs.

Usage:
    python3 send.py <command> [args…]

Commands:
    behavior <name>                    Set both compositor layers simultaneously
    attn <name>                        Set gaze layer only
    affect <name>                      Set expression layer only
    micro <name> [hold_secs]           Trigger a micro-expression (default hold: 0.25s)
    event <name> [key=val …]           Emit a drive event with optional data payload
    pressure <state> <amount>          Inject pressure directly into a state (0–1)
    param <key> <value>                Set a single param
    params <key=val> [key=val…]        Set multiple params at once
    look <x> <y>                       Trigger a 2D saccade (x,y in -1..1)
    look3D <x> <y> <z> [cat=<name>]   Reposition nearest POI and snap attention
    blink                              Trigger a blink
    color <key> <hex>                  Set a color value
    raw <json>                         Send arbitrary JSON

Behavior names:
    idle  attentive  curious  sleepy  alert  searching
    listening  processing  speaking  waiting
    engaged  confused  pleased  uncomfortable
    waking  resting  interrupted

Drive events (rule engine):
    face_detected    x= y= z= scale=    Face found at world position
    face_lost                            Face no longer visible
    person_entered   x= y= z=           Person entered scene
    person_left                          Person left scene
    person_close     scale=             Person uncomfortably close (scale = proximity 0–1)
    crowd_detected                       Multiple people present
    room_empty                           Nobody visible
    room_still                           No motion for extended period
    motion_detected  x= y= z=           Motion at world position
    startle          scale=             Sudden loud or unexpected stimulus (scale = intensity)
    loud_sound       scale=             Loud audio event
    speech_start                         Voice activity detected
    speech_end                           Voice activity ended
    long_silence                         Extended silence after speech
    wake_word        x= y= z=           Wake word detected (optional speaker position)
    error                                System error occurred
    success                              Task completed successfully
    low_power                            Battery / power warning
    startup                              Robot coming online

Examples:
    python3 send.py behavior attentive
    python3 send.py attn alert
    python3 send.py affect pleased
    python3 send.py micro confused 0.3
    python3 send.py event startle
    python3 send.py event startle scale=1.5
    python3 send.py event face_detected x=-1.2 y=1.5 z=3.0
    python3 send.py event face_detected x=-1.2 y=1.5 z=3.0 scale=0.8
    python3 send.py event motion_detected x=2.0 y=0.8 z=3.5
    python3 send.py pressure curious 0.6
    python3 send.py param gazeSpeed 2.0
    python3 send.py params gazeSpeed=1.5 pupilSize=0.6
    python3 send.py look 0.5 -0.2
    python3 send.py look3D -1.2 1.5 3.0
    python3 send.py look3D -1.2 1.5 3.0 cat=person
    python3 send.py blink
    python3 send.py color eyeColor '#ff0000'
    python3 send.py raw '{"type":"params","data":{"arcCurvature":0.8}}'

Server URL defaults to ws://localhost:8765.
Override with WS_URL env var:
    WS_URL=ws://192.168.1.10:8765 python3 send.py blink
"""

import asyncio
import json
import os
import sys

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

URL = os.environ.get("WS_URL", "ws://localhost:8765")


def parse_kv(pairs: list) -> dict:
    """Parse key=value strings into a dict, coercing numeric values to float."""
    data = {}
    for pair in pairs:
        k, _, v = pair.partition("=")
        try:
            data[k] = float(v)
        except ValueError:
            data[k] = v
    return data


def build_message(args: list) -> dict:
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]

    if cmd == "behavior":
        if len(args) < 2:
            print("usage: behavior <name>")
            sys.exit(1)
        return {"type": "behavior", "value": args[1]}

    elif cmd == "attn":
        if len(args) < 2:
            print("usage: attn <name>")
            sys.exit(1)
        return {"type": "attn", "value": args[1]}

    elif cmd == "affect":
        if len(args) < 2:
            print("usage: affect <name>")
            sys.exit(1)
        return {"type": "affect", "value": args[1]}

    elif cmd == "micro":
        if len(args) < 2:
            print("usage: micro <name> [hold_secs]")
            sys.exit(1)
        msg = {"type": "micro", "value": args[1]}
        if len(args) >= 3:
            msg["hold"] = float(args[2])
        return msg

    elif cmd == "event":
        if len(args) < 2:
            print("usage: event <name> [key=val …]")
            sys.exit(1)
        msg: dict = {"type": "event", "value": args[1]}
        if len(args) > 2:
            msg["data"] = parse_kv(args[2:])
        return msg

    elif cmd == "pressure":
        if len(args) < 3:
            print("usage: pressure <state> <amount>")
            sys.exit(1)
        return {"type": "pressure", "state": args[1], "amount": float(args[2])}

    elif cmd == "param":
        if len(args) < 3:
            print("usage: param <key> <value>")
            sys.exit(1)
        return {"type": "param", "key": args[1], "value": float(args[2])}

    elif cmd == "params":
        if len(args) < 2:
            print("usage: params key1=val1 key2=val2 …")
            sys.exit(1)
        data = {}
        for pair in args[1:]:
            k, _, v = pair.partition("=")
            data[k] = float(v)
        return {"type": "params", "data": data}

    elif cmd == "look":
        if len(args) < 3:
            print("usage: look <x> <y>   (values in -1..1)")
            sys.exit(1)
        return {"type": "look", "x": float(args[1]), "y": float(args[2])}

    elif cmd == "look3D":
        if len(args) < 4:
            print("usage: look3D <x> <y> <z> [cat=<category>]")
            sys.exit(1)
        msg = {"type": "look3D", "x": float(args[1]), "y": float(args[2]), "z": float(args[3])}
        for extra in args[4:]:
            k, _, v = extra.partition("=")
            if k == "cat" or k == "category":
                msg["category"] = v
        return msg

    elif cmd == "blink":
        return {"type": "blink"}

    elif cmd == "color":
        if len(args) < 3:
            print("usage: color <key> <#rrggbb>")
            sys.exit(1)
        return {"type": "color", "key": args[1], "value": args[2]}

    elif cmd == "raw":
        if len(args) < 2:
            print("usage: raw '<json>'")
            sys.exit(1)
        return json.loads(args[1])

    else:
        print(f"Unknown command: {cmd!r}")
        print(__doc__)
        sys.exit(1)


async def send(msg: dict):
    try:
        async with websockets.connect(URL) as ws:
            payload = json.dumps(msg)
            await ws.send(payload)
            print(f"sent → {payload}")
    except OSError as e:
        print(f"connection failed: {e}")
        print(f"is server.py running?  (python3 server.py)")
        sys.exit(1)


if __name__ == "__main__":
    msg = build_message(sys.argv[1:])
    asyncio.run(send(msg))
