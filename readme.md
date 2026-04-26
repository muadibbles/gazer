# gazer 👁️

An exploration of the 12 principles of animation applied to robotics — using a 3D robot with expressive eyes as the test subject. The goal is to understand what makes a robot feel alive rather than mechanical: how motion, timing, and expression create the impression of weight, intention, and personality. A secondary thread is robot personality implementation: how independent behavioral layers, state machines, and a drive system can give a robot a coherent inner life that shapes how it moves and responds over time. Browser-based, designed to eventually run on embedded hardware (Raspberry Pi, Jetson, etc).

---

## Quick start

```bash
# 1. Start the relay server
python3 server.py

# 2. Open the sim in a browser
open index.html          # or: python3 -m http.server 8080

# 3. Run the synthetic simulator to see the robot react immediately
python3 simulate.py
```

That's enough to watch the full system in action — no camera or microphone needed.

---

## What it does

- **Smooth arc saccades** — eye movement follows quadratic bezier curves, not linear paths, so it feels alive
- **Compositor** — two independent layers: *gaze* (controls saccade pattern) and *expression* (controls lids, brows, mouth); any behavior can be used as either layer, mixed freely
- **Transition blending** — each state defines its own blend-in duration and easing curve; pair-specific overrides for dramatic shifts; `interrupted` snaps in and auto-returns after 0.5s
- **Blink system** — natural blink timing per behavior, with anticipation and follow-through spring
- **3D robot body** — Three.js scene; face canvas mapped as a texture on the head
- **3-phase head motion** — anticipation wind-up → S-curve move → overshoot settle; only fires for turns above a tunable threshold; all parameters exposed in the UI
- **Arc motion in 3D** — head tilts into yaw turns, body leans during rotation; motion traces curves through space, not flat angular sweeps
- **Multi-camera views** — Face / POV / Ceiling / Perspective / Travel Cam and 4-up grid; POV camera mounts at the robot eye; Travel Cam is fully orbit-controllable and follows the robot as it moves
- **Mobility system** — differential drive with realistic arc turns; robot wanders autonomously when curious/alert, stands and looks around when idle, holds still when resting; obstacle avoidance via potential fields; spatial memory biases destinations toward unvisited areas
- **Battery system** — drains from movement and mental activity; robot finishes current leg then returns to the Charger POI when low; critical level triggers immediate return; sleeps on charger 9 pm–7 am
- **Drive system** — pressure-based behavior selection; rule engine fires on events (`face_detected`, `speech_start`, `startle`, etc.); novelty decay prevents getting stuck
- **Task system** — queued directed interactions; utility (transactional) and social (open-ended) modes; interrupt support
- **World model** — 9 named POIs (Person, Child, Cat, Dog, TV, Window, Food Bowl, Front Door, Charger); draggable in 3D scene; familiarity and attention tracking per POI
- **Floor heatmap** — canvas texture overlaid on the floor showing where the robot has travelled; yellow = fresh, fades to red then transparent over 5 min; toggle via "Show heatmap" checkbox
- **Session timer** — elapsed time display in the left panel from page load
- **State broadcast** — engine serializes full state at 20 Hz over WebSocket; Renderer Mode lets a second browser tab display state received from the network rather than computing it locally

---

## Behaviors

17 behaviors across five groups: Classic, Attention, Conversational, Affective, and Operational. Each defines gaze parameters (range, speed, easing) and expression parameters (lids, brows, mouth, blink rate) — any behavior can be used as a template for either compositor layer independently.

See [docs/behaviors.md](docs/behaviors.md) for the full reference.

---

## Architecture

```
Compositor
├── attn layer   → GazeBehavior       (gazeRadius, speedMult, easeFn)
└── affect layer → ExpressionBehavior (lids, brows, mouth, blinkMult)

GazeSaccade (bezier arc engine)
├── anticipation phase (counter-move wind-up)
├── main arc phase     (quadratic bezier)
└── follow-through     (damped spring overshoot)

Drive system
├── pressure vector    — per-behavior float, decays toward driveProfile
├── rule engine        — declarative event → [pressure, look3D, micro, ...] table
├── task queue         — utility + social modes, interrupt support
└── POI world model    — familiarity, attention, 3D positions, affordances

BodyController (Three.js)
├── headGroup          — 3-phase motion profile (ant → S-curve → overshoot) + arc roll tilt
├── upperBody          — body+head pitch group; wheels always stay grounded
├── robot body         — heading driven by differential drive; arc pitch lean
└── ball               — draggable gaze target; Y-handle for height

Mobility
├── drive kinematics   — v_L = v − ω·d/2, v_R = v + ω·d/2; realistic arc turns
├── state machine      — hold → wander → approach → scan → returning → charging
├── spatial memory     — 0.5 m grid; timestamps last visit per cell; novelty-biased targeting
├── obstacle avoidance — potential-field repulsion from object POIs and floor boundary
└── battery            — drains from movement + activity; routes to Charger POI when low

Cameras
├── face cam           — 2D canvas overlay (top-left in 4-up)
├── POV cam            — mounts at robot eye, gaze-direction frustum
├── ceiling cam        — top-down, pan+zoom only
├── travel cam         — orbit-controlled, follows robot as it moves
└── perspective cam    — orbit-controlled
```

---

## Scripts

All scripts connect to `server.py` as WebSocket clients. Override the server URL with `WS_URL=ws://host:port`.

### `server.py` — relay server

Forwards every message to every other connected client. All scripts and browser tabs connect here.

```bash
python3 server.py           # default port 8765
python3 server.py 9000      # custom port
```

### `send.py` — one-shot command sender

Send a single command and disconnect. Useful for scripting and quick tests.

```bash
python3 send.py behavior attentive
python3 send.py event face_detected x=-1.2 y=1.5 z=3.0
python3 send.py event startle scale=1.5
python3 send.py look3D -1.2 1.5 3.0 cat=person
python3 send.py pressure curious 0.6
python3 send.py micro confused 0.3
python3 send.py blink
python3 send.py param gazeSpeed 2.0
```

Run `python3 send.py` with no arguments for the full command reference.

### `states.py` — scenario runner and interactive REPL

Fire named scenarios or issue commands interactively.

```bash
python3 states.py                       # interactive REPL
python3 states.py scenario dog_hungry   # run a named scenario
python3 states.py list                  # list all scenarios and POI indices
```

REPL commands: `scenario <name>`, `task <src> <tgt> <action> [mode]`, `complete`, `event <name> [k=v …]`, `speak [peak] [duration]`, `poi`, `list`.

Named scenarios: `dog_hungry`, `dog_play`, `cat_hello`, `person_utility`, `person_social`, `kid_play`, `multi_task`, `interrupt`, `startle_recovery`, `arrival_and_greet`, `low_power`, `speaking_test`.

### `simulate.py` — synthetic sensor simulator

Generates realistic fake sensor events — no webcam or microphone needed. A virtual person enters the scene, wanders on an organic path, speaks periodically, then leaves. Ambient sounds fire independently.

```bash
python3 simulate.py                 # continuous, real-time
python3 simulate.py --fast          # 3× compressed time
python3 simulate.py --once          # one visit cycle then exit
python3 simulate.py --seed 42       # reproducible sequence
python3 simulate.py --speed 2       # explicit time multiplier
```

### `recorder.py` — session recorder

Connects to the relay, filters `type: "state"` packets, and appends each to a timestamped JSONL file. Auto-reconnects with exponential backoff.

```bash
python3 recorder.py                 # writes to ./recordings/
python3 recorder.py /tmp/sessions   # custom output directory
```

Output: `<dir>/session_YYYYMMDD_HHMMSS.jsonl`

### `replay.py` — session replay

Plays back a recorded JSONL file through the relay at the original cadence. Open a browser tab with Renderer Mode enabled to display the playback.

```bash
python3 replay.py recordings/session_20250411_143022.jsonl
python3 replay.py session.jsonl --speed 2       # double speed
python3 replay.py session.jsonl --loop          # repeat until Ctrl-C
```

### `face_detect.py` — webcam face detection

Tracks faces via webcam, estimates 3D world position, and fires `face_detected` / `look3D` / `face_lost` / `person_close` events. Works with any webcam including a laptop's built-in camera.

```bash
pip install mediapipe opencv-python websockets

python3 face_detect.py                  # default webcam, display window
python3 face_detect.py --camera 1       # camera index 1
python3 face_detect.py --no-display     # headless
python3 face_detect.py --hfov 90        # set camera horizontal FOV
```

The depth estimate uses the face bounding box width. Tune `--hfov` to match your camera for accurate distances.

### `audio.py` — microphone input pipeline

Captures mic input, runs a VAD state machine, and fires `speech_start` / `speech_end` / `loud_sound` / `startle` events. Sends a continuous `amplitude` parameter at 20 Hz for real-time mouth sync.

```bash
pip install sounddevice numpy websockets

python3 audio.py                        # default mic
python3 audio.py --list-devices         # print available audio devices
python3 audio.py --device 2             # use device index 2
python3 audio.py --threshold 0.03       # override speech onset threshold
```

### `time_scheduler.py` — time-of-day drive scheduler

Shifts the robot's baseline temperament throughout the day by injecting pressure commands on a day curve. Fires every 2 minutes; effects decay naturally between injections.

| Period | Hours | Effect |
|---|---|---|
| Morning | 05–09 | curious↑, alert↑ |
| Day | 09–17 | neutral baseline |
| Evening | 17–21 | idle↑ |
| Night | 21–05 | sleepy↑, resting↑ |

```bash
python3 time_scheduler.py               # run continuously
python3 time_scheduler.py --interval 60 # inject every 60s
python3 time_scheduler.py --dry-run     # print without connecting
```

---

## Running the full stack

```bash
# Terminal 1 — relay
python3 server.py

# Terminal 2 — open sim
open index.html

# Pick any combination of inputs:
python3 simulate.py          # synthetic (no hardware)
python3 face_detect.py       # real webcam
python3 audio.py             # real microphone
python3 time_scheduler.py    # day curve (always safe to run)

# Optional: record the session
python3 recorder.py

# Later: replay it in Renderer Mode
python3 replay.py recordings/session_*.jsonl
```

---

## Parameters

All exposed in the UI panel:

| Param | Description |
|---|---|
| `arcCurvature` | How much the gaze arc bends (0 = straight line) |
| `gazeSpeed` | Base speed multiplier for all saccades |
| `saccadeJitter` | Adds slight randomness to target positions |
| `lidOpenness` | How wide the eye opens (overridden by behavior) |
| `pupilSize` | Pupil radius relative to iris |
| `blinkInterval` | Seconds between blinks (modified by behavior) |
| `transitionDur` | Default compositor blend duration |
| `headRotationMax` | Degrees — max head yaw offset from body heading |
| `headMoveSpeed` | deg/s — how fast the head sweeps to a new target |
| `headThreshold` | Degrees — minimum turn size that triggers anticipation/overshoot |
| `headAntAmt` | Anticipation wind-up as a fraction of turn distance (0 = off) |
| `headAntDur` | Duration of the anticipation phase in seconds |
| `headOvAmt` | Overshoot distance as a fraction of turn distance (0 = off) |
| `headOvDur` | Duration of the overshoot settle phase in seconds |
| `headArcFactor` | Head tilt into yaw turns (0 = off) |
| `bodyRotationMax` | Degrees — max body yaw offset (gaze layer, not drive heading) |
| `bodyArcFactor` | Body lean into turns (0 = off) |
| `ballTrackTimeout` | Seconds before reverting to idle after drag |
| `squashStretch` | Eye deformation amount during saccades (0 = off) |
| `attentionHoldMin` | Minimum seconds the robot dwells on each POI (default 10 s) |
| `attentionHoldMax` | Maximum seconds the robot dwells on each POI (default 25 s) |
| `driveHysteresis` | Pressure margin required to switch behavior states |
| `driveNoveltyDecay` | Pressure lost per second on the currently active state |

---

## 12 Principles of Animation

From Johnston & Thomas, *The Illusion of Life* (Disney, 1981) — the design checklist for the project.

See [docs/animation-principles.md](docs/animation-principles.md) for the full status table.

---

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).

---

## License

MIT
