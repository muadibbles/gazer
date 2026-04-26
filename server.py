#!/usr/bin/env python3
"""
gazer/server.py — WebSocket relay server

All connected clients form a single broadcast group: every message is
forwarded to every OTHER connected client.

Roles (by convention, not enforced):
  browser    connects on load; receives commands, sends state packets
  sender     send.py / states.py; sends commands, disconnects immediately
  recorder   recorder.py; receives state packets, never sends

State packets (type="state") are logged at most once per second to avoid
terminal flood at 20 Hz. All other message types are logged verbosely.

Usage:
    python3 server.py [port]          default port: 8765

Install deps:
    pip install websockets
"""

import asyncio
import json
import sys
import time

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
clients: set = set()


async def handler(websocket):
    clients.add(websocket)
    addr = websocket.remote_address
    print(f"[+] connected    {addr}  ({len(clients)} total)")

    state_count = 0          # state packets received from this connection
    last_state_log = 0.0     # wall-clock time of last state-packet log line

    try:
        async for raw in websocket:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                print(f"[!] invalid JSON from {addr}: {raw!r}")
                continue

            if data.get("type") == "state":
                # High-frequency — log at most once per second
                state_count += 1
                now = time.monotonic()
                if now - last_state_log >= 1.0:
                    last_state_log = now
                    poi   = data.get("data", {}).get("poiLabel", "—")
                    beh   = data.get("data", {}).get("behavior", "—")
                    print(f"[S] state  #{state_count:>6}  beh={beh:<18} poi={poi}")
            else:
                print(f"[>] {addr}  {data}")

            # Relay to every OTHER connected client
            targets = [c for c in clients if c is not websocket]
            if targets:
                await asyncio.gather(
                    *[c.send(raw) for c in targets],
                    return_exceptions=True,
                )

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.discard(websocket)
        suffix = f"  ({state_count} state packets)" if state_count else ""
        print(f"[-] disconnected {addr}  ({len(clients)} total){suffix}")


async def main():
    print(f"gazer relay — ws://localhost:{PORT}")
    print("waiting for connections…\n")
    async with websockets.serve(handler, "localhost", PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nshutdown")
