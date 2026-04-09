#!/usr/bin/env python3
"""
gazer/server.py — WebSocket relay server

The browser connects here and receives commands forwarded from any other
connected client (e.g. send.py or an LLM inference process).

Usage:
    python3 server.py [port]   (default: 8765)

Install deps:
    pip install websockets
"""

import asyncio
import json
import sys

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
    try:
        async for raw in websocket:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                print(f"[!] invalid JSON from {addr}: {raw!r}")
                continue

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
        print(f"[-] disconnected {addr}  ({len(clients)} total)")


async def main():
    print(f"gazer relay server — ws://localhost:{PORT}")
    print("waiting for connections…\n")
    async with websockets.serve(handler, "localhost", PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nshutdown")
