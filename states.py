#!/usr/bin/env python3
"""
gazer/states.py — State scenario tester for gazer.

Fires sequences of events to exercise the task system, POI affordances,
and drive engine. Use this to test interactions without needing real sensors.

Usage:
    python3 states.py                        Interactive REPL
    python3 states.py scenario <name>        Run a named scenario
    python3 states.py list                   List scenarios and POI indices

POI indices (match window.pois order in index.html):
    0  Person      — utility, social, command, greeting
    1  Child       — social, play_request, greeting
    2  Cat         — cat_greeting, beg_play
    3  Dog         — dog_begging, dog_play_request, greeting
    4  TV          — watch
    5  Window      — watch
    6  Food Bowl   — fill_request
    7  Front Door  — arrival, departure

Task modes:
    utility   Transactional: acknowledge → process → wait for task_complete
    social    Open-ended: listen → engage → wait for task_complete

Interactive commands:
    scenario <name>                      Run a named scenario
    task <source_idx> <target_idx> <action> [mode] [interrupt]
                                         Assign a task
    complete                             Complete active task
    event <name> [key=val …]             Fire a raw drive event
    poi                                  List POIs
    list                                 List scenarios
    help                                 Show this help
    quit / exit                          Exit

Examples:
    scenario dog_hungry
    task 0 3 feed utility
    task 0 1 play social
    event dog_begging
    event startle scale=1.5
    event face_detected x=-1.8 y=1.5 z=3.0
    complete
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

# ── POI reference (mirrors POI_INIT in index.html) ──────────────────────────

POIS = [
    {"idx": 0, "label": "Person",     "category": "person", "affordances": ["utility", "social", "command", "greeting"]},
    {"idx": 1, "label": "Child",      "category": "person", "affordances": ["social", "play_request", "greeting"]},
    {"idx": 2, "label": "Cat",        "category": "pet",    "affordances": ["cat_greeting", "beg_play"]},
    {"idx": 3, "label": "Dog",        "category": "pet",    "affordances": ["dog_begging", "dog_play_request", "greeting"]},
    {"idx": 4, "label": "TV",         "category": "object", "affordances": ["watch"]},
    {"idx": 5, "label": "Window",     "category": "object", "affordances": ["watch"]},
    {"idx": 6, "label": "Food Bowl",  "category": "object", "affordances": ["fill_request"]},
    {"idx": 7, "label": "Front Door", "category": "object", "affordances": ["arrival", "departure"]},
]

# ── Scenarios ────────────────────────────────────────────────────────────────
# Each step: (delay_seconds, message_dict)
# delay is relative to the previous step.

SCENARIOS = {
    "dog_hungry": {
        "desc": "Dog begs for food; person tells robot to feed it; robot completes task",
        "steps": [
            (0.0, {"type": "event", "value": "dog_begging"}),
            (2.0, {"type": "event", "value": "assign_task",
                   "data": {"source": 0, "target": 3, "action": "feed", "mode": "utility"}}),
            (5.0, {"type": "event", "value": "task_complete"}),
        ],
    },
    "dog_play": {
        "desc": "Dog wants to play; child asks robot to play with dog; task completes",
        "steps": [
            (0.0, {"type": "event", "value": "dog_play_request"}),
            (1.5, {"type": "event", "value": "assign_task",
                   "data": {"source": 1, "target": 3, "action": "play", "mode": "utility"}}),
            (6.0, {"type": "event", "value": "task_complete"}),
        ],
    },
    "cat_hello": {
        "desc": "Cat wanders over; robot notices and greets",
        "steps": [
            (0.0, {"type": "event", "value": "cat_greeting"}),
            (3.0, {"type": "event", "value": "success"}),
        ],
    },
    "person_utility": {
        "desc": "Person gives a command (turn on TV); robot acknowledges and executes",
        "steps": [
            (0.0, {"type": "event", "value": "wake_word",
                   "data": {"x": -1.8, "y": 1.5, "z": 3.0}}),
            (1.2, {"type": "event", "value": "assign_task",
                   "data": {"source": 0, "target": 4, "action": "watch_tv", "mode": "utility"}}),
            (4.5, {"type": "event", "value": "task_complete"}),
        ],
    },
    "person_social": {
        "desc": "Person starts a social conversation; robot listens then engages",
        "steps": [
            (0.0, {"type": "event", "value": "person_entered",
                   "data": {"x": -1.8, "y": 1.5, "z": 3.0}}),
            (1.0, {"type": "event", "value": "speech_start"}),
            (2.0, {"type": "event", "value": "assign_task",
                   "data": {"source": 0, "target": 0, "action": "converse", "mode": "social"}}),
            (9.0, {"type": "event", "value": "task_complete"}),
        ],
    },
    "kid_play": {
        "desc": "Child asks to play a game; robot engages socially",
        "steps": [
            (0.0, {"type": "event", "value": "kid_play_request"}),
            (1.0, {"type": "event", "value": "assign_task",
                   "data": {"source": 1, "target": 1, "action": "play_game", "mode": "social"}}),
            (8.0, {"type": "event", "value": "task_complete"}),
        ],
    },
    "multi_task": {
        "desc": "Two tasks queued: feed dog, then play with kid",
        "steps": [
            (0.0, {"type": "event", "value": "assign_task",
                   "data": {"source": 0, "target": 3, "action": "feed", "mode": "utility"}}),
            (0.5, {"type": "event", "value": "assign_task",
                   "data": {"source": 1, "target": 1, "action": "play_game", "mode": "social"}}),
            (5.0, {"type": "event", "value": "task_complete"}),  # completes 'feed'
            (9.0, {"type": "event", "value": "task_complete"}),  # completes 'play_game'
        ],
    },
    "interrupt": {
        "desc": "Task in progress; urgent command interrupts it",
        "steps": [
            (0.0, {"type": "event", "value": "assign_task",
                   "data": {"source": 1, "target": 1, "action": "play_game", "mode": "social"}}),
            (3.0, {"type": "event", "value": "assign_task",
                   "data": {"source": 0, "target": 3, "action": "feed", "mode": "utility",
                            "interrupt": True}}),
            (6.0, {"type": "event", "value": "task_complete"}),  # completes 'feed' (interrupted task)
            (9.0, {"type": "event", "value": "task_complete"}),  # resumes 'play_game'
        ],
    },
    "startle_recovery": {
        "desc": "Sudden loud noise; robot startles then recovers",
        "steps": [
            (0.0, {"type": "event", "value": "startle", "data": {"scale": 1.2}}),
            (1.5, {"type": "event", "value": "success"}),
        ],
    },
    "arrival_and_greet": {
        "desc": "Someone comes through the front door; robot tracks and greets",
        "steps": [
            (0.0, {"type": "event", "value": "arrival"}),
            (2.0, {"type": "event", "value": "face_detected",
                   "data": {"x": -0.9, "y": 1.5, "z": 3.5}}),
            (3.0, {"type": "event", "value": "assign_task",
                   "data": {"source": 0, "target": 0, "action": "greet", "mode": "social"}}),
            (6.0, {"type": "event", "value": "task_complete"}),
        ],
    },
    "low_power": {
        "desc": "Battery warning; robot winds down",
        "steps": [
            (0.0, {"type": "event", "value": "low_power"}),
            (4.0, {"type": "event", "value": "room_empty"}),
        ],
    },
}

# ── Transport ────────────────────────────────────────────────────────────────

async def send_one(msg: dict):
    async with websockets.connect(URL) as ws:
        payload = json.dumps(msg)
        await ws.send(payload)
        print(f"  → {payload}")


async def run_scenario(name: str):
    scenario = SCENARIOS.get(name)
    if not scenario:
        print(f"Unknown scenario: {name!r}. Run 'list' to see available scenarios.")
        return

    print(f"\nScenario: {name}")
    print(f"  {scenario['desc']}")
    print(f"  {len(scenario['steps'])} steps\n")

    try:
        for i, (delay, msg) in enumerate(scenario["steps"]):
            if i > 0 and delay > 0:
                print(f"  waiting {delay}s…")
                await asyncio.sleep(delay)
            print(f"  step {i+1}/{len(scenario['steps'])}:", end=" ")
            await send_one(msg)
    except OSError as e:
        print(f"\nconnection failed: {e}")
        print(f"is server.py running?  (python3 server.py)")
        return

    print("\nDone.")


def parse_kv(pairs: list) -> dict:
    data = {}
    for pair in pairs:
        k, _, v = pair.partition("=")
        try:
            data[k] = float(v)
        except ValueError:
            if v.lower() in ("true", "yes", "1"):
                data[k] = True
            elif v.lower() in ("false", "no", "0"):
                data[k] = False
            else:
                data[k] = v
    return data


def print_pois():
    print("\nPOI index reference:")
    for p in POIS:
        print(f"  {p['idx']}  {p['label']:<12} ({p['category']:<6})  {', '.join(p['affordances'])}")
    print()


def print_scenarios():
    print("\nAvailable scenarios:")
    for name, s in SCENARIOS.items():
        print(f"  {name:<22}  {s['desc']}")
    print()


# ── Interactive REPL ─────────────────────────────────────────────────────────

async def repl():
    print("Gazer state tester — type 'help' for commands")
    print(f"Connecting to {URL}\n")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()

        if cmd in ("quit", "exit", "q"):
            break

        elif cmd == "help":
            print(__doc__)

        elif cmd == "list":
            print_scenarios()

        elif cmd == "poi":
            print_pois()

        elif cmd == "scenario":
            if len(parts) < 2:
                print("usage: scenario <name>")
                print_scenarios()
            else:
                await run_scenario(parts[1])

        elif cmd == "task":
            # task <source> <target> <action> [mode] [interrupt]
            if len(parts) < 4:
                print("usage: task <source_idx> <target_idx> <action> [utility|social] [interrupt]")
                continue
            data = {
                "source":    int(parts[1]),
                "target":    int(parts[2]),
                "action":    parts[3],
                "mode":      parts[4] if len(parts) > 4 else "utility",
                "interrupt": len(parts) > 5 and parts[5].lower() in ("interrupt", "true", "1"),
            }
            msg = {"type": "event", "value": "assign_task", "data": data}
            try:
                await send_one(msg)
            except OSError as e:
                print(f"connection failed: {e}")

        elif cmd == "complete":
            msg = {"type": "event", "value": "task_complete"}
            try:
                await send_one(msg)
            except OSError as e:
                print(f"connection failed: {e}")

        elif cmd == "event":
            if len(parts) < 2:
                print("usage: event <name> [key=val …]")
                continue
            msg: dict = {"type": "event", "value": parts[1]}
            if len(parts) > 2:
                msg["data"] = parse_kv(parts[2:])
            try:
                await send_one(msg)
            except OSError as e:
                print(f"connection failed: {e}")

        else:
            print(f"Unknown command: {cmd!r}  (type 'help' for commands)")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        asyncio.run(repl())

    elif args[0] == "list":
        print_scenarios()
        print_pois()

    elif args[0] == "scenario" and len(args) >= 2:
        try:
            asyncio.run(run_scenario(args[1]))
        except OSError as e:
            print(f"connection failed: {e}")
            print("is server.py running?  (python3 server.py)")
            sys.exit(1)

    else:
        print(__doc__)
        sys.exit(1)
