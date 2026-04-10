# Robot Architecture Plan

Design notes for evolving gazer from a browser simulation into a deployable robot system with real-time monitoring.

---

## The core problem

Right now the browser **is** the engine. The compositor, spring physics, saccade planner, and renderer all live in one `index.html`. That works fine for development and design iteration, but it has the wrong shape for a real robot:

- The robot needs to run headlessly, without a browser
- A human operator needs to observe what the robot is actually doing, not a separate simulation of it
- Recorded sessions need to be replayable for analysis
- Diagnostic overlays should be addable without touching robot execution

The fix is an architectural inversion: separate execution from observation, and make observation a first-class citizen.

---

## The split

```
┌─────────────────────────────┐
│         Robot hardware       │
│                              │
│  ┌──────────────────────┐   │
│  │   Behavior engine    │   │
│  │  compositor          │   │
│  │  spring physics      │   │
│  │  saccade planner     │   │
│  │  state machine       │   │
│  └──────────┬───────────┘   │
│             │ state tick     │
│  ┌──────────▼───────────┐   │
│  │  Output adapters     │   │
│  │  OLED / servo / LCD  │   │
│  └──────────────────────┘   │
│             │ broadcast      │
└─────────────┼───────────────┘
              │
    ══════════╪══════════════════  WebSocket state channel (out)
              │
    ┌─────────┴──────┬───────────────┐
    │                │               │
┌───▼────┐   ┌───────▼──────┐  ┌────▼────┐
│Browser │   │   Recorder   │  │ Other   │
│sim view│   │  JSONL log   │  │monitors │
│overlays│   │  + playback  │  │         │
└────────┘   └──────────────┘  └─────────┘

    ══════════════════════════════════  WebSocket command channel (in)
              ▲
    ┌─────────┴──────┬───────────────┐
    │                │               │
┌───┴────┐   ┌───────┴──────┐  ┌────┴────┐
│Operator│   │  LLM / audio │  │  Vision │
│console │   │  pipeline    │  │tracking │
└────────┘   └──────────────┘  └─────────┘
```

Two channels. State flows **out** from the robot to all subscribers. Commands flow **in** from operators, pipelines, and sensors to the robot. They never mix.

---

## State broadcast

At the end of every physics tick the behavior engine serializes its full internal state and publishes it. Every subscriber receives the same packet.

```json
{
  "t": 1712784523.441,
  "attn": "alert",
  "affect": "listening",
  "transBlend": 0.73,
  "transDur": 0.06,
  "holdTimer": 0.0,
  "gazeX": 0.21,
  "gazeY": -0.08,
  "saccadePhase": "arc",
  "saccadeTarget": [0.31, -0.12],
  "saccadeProgress": 0.44,
  "head3DYaw": 14.2,
  "head3DYawVel": 38.1,
  "head3DPitch": -2.1,
  "head3DRoll": -4.6,
  "body3DYaw": 6.1,
  "bodyPitchArc": -1.2,
  "lidOpenness": 0.88,
  "browHeight": 0.5,
  "blinkCountdown": 2.3,
  "blinkPhase": "idle"
}
```

Nothing is summarized or processed for the observer's benefit. The observer receives exactly what the robot is experiencing.

---

## Browser sim view

The browser stops running physics. Instead of `update()` computing state, it receives state packets and calls `render(receivedState)`. The canvas and Three.js rendering code barely changes — they already read from a `state` object, they just won't own it.

This means the sim view is always accurate: it cannot drift from robot reality, because it has no independent state to drift.

### Diagnostic overlays

Because the browser is a pure renderer with no execution responsibility, overlays can be added freely without touching robot logic:

| Overlay | What it shows |
|---------|--------------|
| Arc trail | Recent pupil path history |
| Bezier preview | Ghost of the full planned saccade arc before it fires |
| Saccade target indicator | Where the next landing point will be |
| Spring force vectors | Current acceleration on head and body |
| Compositor blend bar | Both layers, with easing curve visualization |
| Behavior pressure bars | Per-state pressure levels (once emotion engine exists) |
| Velocity heatmap | Accumulated dwell density over a session |
| Blink countdown | Time until next blink |
| FPS / frame timing | Render health on hardware |

All of these read from the same incoming state stream. None require changes to the robot.

---

## Recorder

A dead-simple WebSocket subscriber that appends packets to a JSONL file:

```
{"t":1712784523.441,"attn":"alert","gazeX":0.21,...}
{"t":1712784523.457,"attn":"alert","gazeX":0.23,...}
{"t":1712784523.474,"attn":"alert","gazeX":0.26,...}
```

No logic. Just write. Timestamps allow exact replay at original speed or scrubbed at any rate.

**Playback** is the reverse: a process reads the file and feeds packets into the browser renderer at the recorded tick rate. The browser doesn't know the difference between live and playback.

Recorded sessions are useful for:
- Reviewing how a behavior sequence actually looked end-to-end
- Debugging unexpected transitions or physics artifacts
- Measuring things post-hoc (dwell time, saccade frequency, behavior durations)
- Generating training data for the emotion engine

---

## Input pipeline

The command channel accepts the same message types the current WebSocket API already handles: `attn`, `affect`, `param`, `look`, `blink`, `behavior`. Any process that can open a WebSocket can drive the robot.

In practice, inputs come from:

```
Microphone          →  amplitude → blink rate / affect:processing
                    →  wake word → attn:alert + attn:listening
                    →  silence   → affect:waiting

Camera              →  face detected at (x,y) → look:{x,y}, attn:attentive
                    →  face lost             → attn:searching
                    →  multiple faces        → attn:curious

LLM                 →  speaking  → affect:speaking + phoneme stream
                    →  done      → affect:listening
                    →  uncertain → affect:confused

Operator console    →  manual behavior overrides
                    →  parameter tuning during a session
```

Each of these is a small independent process that normalizes its input into command messages. None of them need to know about each other or about the behavior engine internals.

---

## Behavior engine extraction

The current `index.html` needs to be split so the engine can run without a browser:

```
engine.js          — compositor, state machine, spring physics, behaviors, saccade planner
renderer.canvas.js — draws eyes to a 2D canvas (current EyeRenderer)
renderer.three.js  — drives Three.js body scene (current BodyController)
renderer.oled.js   — writes pixel buffer to SSD1306/SH1106 via i2c
renderer.servo.js  — maps gaze/lid values to servo positions via pigpio
main.browser.js    — browser entry point: engine + canvas/three renderers + state receiver
main.robot.js      — robot entry point: engine + hardware renderers + state broadcaster
```

The engine exposes a simple interface:

```javascript
engine.tick(dt)           // advance physics, returns full state object
engine.command(msg)       // receive an incoming command {type, value}
engine.onState(callback)  // register state broadcast subscriber
```

Hardware renderers implement:

```javascript
renderer.render(state, params)  // actuate outputs for this tick
```

---

## Hardware targets

**Pi 4 / Jetson** — full stack: Node.js engine, Chromium kiosk sim view on HDMI, hardware renderer via i2c/GPIO, Python input pipeline processes

**Pi Zero 2W** — headless only: Node.js engine, hardware renderer, no Three.js, sim view runs on a separate machine subscribed over network

**OLED displays** — SSD1306 (128×64) or SH1106; re-implement `EyeRenderer` as a 1-bit pixel buffer writer; compositor output (lidOpenness, pupilX/Y, browHeight) feeds it directly

**Servo eyes** — pan/tilt maps from `gazeX`/`gazeY`; lid servo from `lidOpenness`; head servo group from `head3DYaw`/`head3DPitch`; pigpio or serial to servo controller board

---

## Relationship to current codebase

Nothing in the current `index.html` is wasted. The rendering code, the compositor, the behaviors, the spring physics — all of it ports directly. The work is:

1. Extract engine from HTML into a standalone module
2. Add a state broadcaster to the engine's tick loop (one call at the end of `update()`)
3. Change the browser to receive state rather than compute it
4. Write hardware output adapters
5. Build input pipeline processes

The WebSocket relay (`server.py`) already exists. It mostly needs the data flow direction formalized: robot pushes to a broadcast channel, all subscribers receive it.
