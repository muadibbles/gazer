#!/usr/bin/env python3
"""
gazer/face_detect.py — Face detection input pipeline

Uses MediaPipe Face Detection to track faces via webcam and fires gazer
drive events via the relay server.

Events fired:
    face_detected  x= y= z= scale=   On first detection and every REFRESH_S
    face_lost                         When face disappears (debounced 1.2 s)
    person_close   scale=             When estimated distance < CLOSE_M

Position tracking:
    Sends look3D commands at 5 Hz while a face is visible, updating the
    Person POI position without re-triggering micro-expressions.

Coordinate system:
    Robot at origin looking in +Z direction.  Camera at CAM_HEIGHT metres.
    Face right of frame centre → positive X.
    Face above  frame centre  → higher Y.
    Z estimated from bounding box width — larger box = nearer.

Usage:
    python3 face_detect.py                    Default webcam, display window
    python3 face_detect.py --camera 1         Camera index 1
    python3 face_detect.py --no-display       Headless (no OpenCV window)
    python3 face_detect.py --hfov 90          Set camera H-FOV in degrees

Environment:
    WS_URL=ws://host:8765   Override relay URL (default ws://localhost:8765)

Requires:
    pip install mediapipe opencv-python websockets
"""

import argparse
import asyncio
import json
import math
import os
import sys
import time

try:
    import cv2
except ImportError:
    print("Missing dependency: pip install opencv-python")
    sys.exit(1)

try:
    import mediapipe as mp
except ImportError:
    print("Missing dependency: pip install mediapipe")
    sys.exit(1)

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

URL        = os.environ.get("WS_URL", "ws://localhost:8765")
HFOV_DEG   = 60.0    # Camera horizontal field of view — tune per camera
CAM_HEIGHT = 0.8     # Camera mounting height in metres (robot eye level)
HEAD_W_M   = 0.16    # Typical face width in metres (for depth estimate)
CLOSE_M    = 1.5     # Distance below which person_close fires
REFRESH_S  = 3.0     # Re-fire face_detected every N seconds (pressure refresh)
LOST_S     = 1.2     # Seconds without detection before face_lost fires
TRACK_HZ   = 5       # look3D position-update commands per second


# ── 3D world position estimate ────────────────────────────────────────────────

def estimate_world(cx: float, cy: float, w_norm: float, aspect: float) -> tuple:
    """
    Convert normalised face bbox to (x, y, z, scale) in world metres.

    cx, cy   — bbox centre, normalised 0–1 from top-left
    w_norm   — bbox width,  normalised 0–1 of frame width
    aspect   — frame width / height
    """
    hfov = math.radians(HFOV_DEG)
    tan_h = math.tan(hfov / 2)

    # Depth from angular size of face
    w_norm = max(w_norm, 0.001)
    z = HEAD_W_M / (2.0 * w_norm * tan_h)
    z = max(0.3, min(10.0, z))

    # Horizontal offset (negative = left of robot)
    x = (cx - 0.5) * 2.0 * tan_h * z

    # Vertical offset — faces above frame centre → higher world Y
    vfov = hfov / aspect
    y = CAM_HEIGHT + (0.5 - cy) * 2.0 * math.tan(vfov / 2) * z
    y = max(0.5, min(3.0, y))

    # Scale: proximity proxy (1.0 at 2.5 m, higher when closer)
    scale = max(0.2, min(2.0, 2.5 / z))

    return round(x, 2), round(y, 2), round(z, 2), round(scale, 2)


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
        # Reconnect inline; caller replaces ws reference
        return await ws_connect()


# ── Main loop ─────────────────────────────────────────────────────────────────

async def run(camera_idx: int, display: bool):
    cap = cv2.VideoCapture(camera_idx)
    if not cap.isOpened():
        print(f"Cannot open camera {camera_idx}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    fd       = mp.solutions.face_detection
    detector = fd.FaceDetection(model_selection=0, min_detection_confidence=0.6)

    ws = await ws_connect()

    face_visible     = False
    last_face_t      = 0.0   # monotonic time of last good detection
    last_detect_sent = 0.0   # time of last face_detected event
    last_track_sent  = 0.0   # time of last look3D command
    last_close_sent  = 0.0   # time of last person_close event
    track_interval   = 1.0 / TRACK_HZ

    print("running — Ctrl-C to stop\n")
    loop = asyncio.get_event_loop()

    try:
        while True:
            ret, frame = await loop.run_in_executor(None, cap.read)
            if not ret:
                await asyncio.sleep(0.05)
                continue

            h, w   = frame.shape[:2]
            aspect = w / h

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = detector.process(rgb)

            now        = time.monotonic()
            detections = res.detections or []

            if detections:
                det = max(detections, key=lambda d: d.score[0])
                bb  = det.location_data.relative_bounding_box

                cx = bb.xmin + bb.width  / 2.0
                cy = bb.ymin + bb.height / 2.0
                x, y, z, scale = estimate_world(cx, cy, bb.width, aspect)

                last_face_t = now

                if not face_visible:
                    face_visible     = True
                    last_detect_sent = 0.0   # force immediate face_detected
                    print(f"face detected  z={z:.1f}m  x={x:+.2f}  y={y:.2f}  scale={scale:.2f}")

                # face_detected — initial detection + periodic pressure refresh
                if now - last_detect_sent >= REFRESH_S:
                    ws = await send(ws, {
                        "type":  "event",
                        "value": "face_detected",
                        "data":  {"x": x, "y": y, "z": z, "scale": scale},
                    })
                    last_detect_sent = now

                # look3D — continuous position tracking (no side effects)
                if now - last_track_sent >= track_interval:
                    ws = await send(ws, {
                        "type": "look3D", "x": x, "y": y, "z": z, "category": "person",
                    })
                    last_track_sent = now

                # person_close — throttled to once per 2 s
                if z < CLOSE_M and now - last_close_sent >= 2.0:
                    ws = await send(ws, {
                        "type":  "event",
                        "value": "person_close",
                        "data":  {"scale": scale},
                    })
                    last_close_sent = now

                if display:
                    x1 = int(bb.xmin * w)
                    y1 = int(bb.ymin * h)
                    x2 = int((bb.xmin + bb.width)  * w)
                    y2 = int((bb.ymin + bb.height) * h)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (74, 247, 196), 2)
                    cv2.putText(frame, f"z={z:.1f}m  x={x:+.2f}",
                                (x1, max(y1 - 8, 12)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (74, 247, 196), 1)

            else:
                # No detection this frame
                if face_visible and (now - last_face_t) >= LOST_S:
                    face_visible = False
                    print("face lost")
                    ws = await send(ws, {"type": "event", "value": "face_lost"})

            if display:
                label = "TRACKING" if face_visible else "searching…"
                color = (74, 247, 196) if face_visible else (100, 100, 100)
                cv2.putText(frame, f"gazer face detect  {label}",
                            (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                cv2.imshow("gazer face detect", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            await asyncio.sleep(0)

    except asyncio.CancelledError:
        pass
    finally:
        cap.release()
        detector.close()
        if display:
            cv2.destroyAllWindows()
        try:
            await ws.close()
        except Exception:
            pass


def main():
    p = argparse.ArgumentParser(description="gazer face detection pipeline")
    p.add_argument("--camera",     type=int,   default=0,
                   help="Camera device index (default 0)")
    p.add_argument("--no-display", action="store_true",
                   help="Headless mode — no OpenCV window")
    p.add_argument("--hfov",       type=float, default=60.0,
                   help="Camera horizontal FOV in degrees (default 60)")
    args = p.parse_args()

    global HFOV_DEG
    HFOV_DEG = args.hfov

    print("gazer face detect")
    print(f"  camera  : {args.camera}")
    print(f"  server  : {URL}")
    print(f"  hfov    : {HFOV_DEG}°")
    print(f"  display : {'off' if args.no_display else 'on'}")
    print()

    try:
        asyncio.run(run(args.camera, not args.no_display))
    except KeyboardInterrupt:
        pass
    print("\nstopped")


if __name__ == "__main__":
    main()
