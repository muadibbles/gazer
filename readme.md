# gazer 👁️

An exploration of the 12 principles of animation applied to robotics — using a 3D robot with expressive eyes as the test subject. The goal is to understand what makes a robot feel alive rather than mechanical: how motion, timing, and expression create the impression of weight, intention, and personality. A secondary thread is robot personality implementation: how independent behavioral layers, state machines, and a drive system can give a robot a coherent inner life that shapes how it moves and responds over time. Browser-based, designed to eventually run on embedded hardware (Raspberry Pi, Jetson, etc).

-----

## What it does

- **Smooth arc saccades** — eye movement follows quadratic bezier curves, not linear paths, so it feels alive
- **Compositor** — two independent layers: *gaze* (controls saccade pattern) and *expression* (controls lids, brows, mouth); any behavior can be used as either template, mixed freely — see [Expressive Response](docs/expressive-response.md)
- **Transition blending** — each state defines its own blend-in duration and easing curve; pair-specific overrides for dramatic shifts; `interrupted` snaps in and auto-returns after 0.5s
- **Easing library** — `inOutCubic`, `outBack`, `outQuart`, `inOutQuint` built in, easy to extend
- **Blink system** — natural blink timing per behavior, with anticipation and follow-through spring
- **3D robot body** — Three.js scene with physical robot; face canvas mapped as texture
- **Spring physics** — head and body rotation use underdamped spring dynamics: natural ease-in, ease-out, and slight overshoot on every movement
- **Arc motion in 3D** — head tilts into yaw turns, body leans during rotation; motion traces curves through space, not flat angular sweeps
- **Draggable gaze target** — yellow ball in the 3D scene; drag it and the robot tracks it with a 75/25 head/eye split; reverts to idle wander after configurable timeout
- **Click to look** — click anywhere on canvas to trigger a manual saccade

-----

## Behaviors

17 behaviors across five groups: Classic, Attention, Conversational, Affective, and Operational. Each defines gaze parameters (range, speed, easing) and expression parameters (lids, brows, mouth, blink rate) — any behavior can be used as a template for either compositor layer independently.

See [docs/behaviors.md](docs/behaviors.md) for the full reference, pair-specific transition overrides, and notes on combining layers.

-----

## Parameters

All exposed in the UI panel:

|Param              |Description                                                  |
|-------------------|-------------------------------------------------------------|
|`arcCurvature`     |How much the gaze arc bends (0 = straight line)              |
|`gazeSpeed`        |Base speed multiplier for all saccades                       |
|`saccadeJitter`    |Adds slight randomness to target positions                   |
|`lidOpenness`      |How wide the eye opens (overridden by behavior)              |
|`pupilSize`        |Pupil radius relative to iris                                |
|`blinkInterval`    |Seconds between blinks (modified by behavior)                |
|`transitionDur`    |Default compositor blend duration (overridden per state)     |
|`headRotationMax`  |Degrees — max 3D head yaw                                    |
|`head3DSpeed`      |Head spring stiffness scale (higher = snappier)              |
|`headSpringDamp`   |Head spring damping (lower = more overshoot)                 |
|`headArcFactor`    |Head tilt into yaw turns (arc motion, 0 = off)               |
|`bodyRotationMax`  |Degrees — max 3D body yaw                                    |
|`body3DSpeed`      |Body spring stiffness scale                                  |
|`bodySpringDamp`   |Body spring damping                                          |
|`bodyArcFactor`    |Body lean into rotation (arc motion, 0 = off)                |
|`ballTrackTimeout` |Seconds before reverting to idle wander after drag ends      |
|`squashStretch`    |Eye deformation amount during saccades (0 = off)             |

-----

## Architecture

```
Compositor
├── attn layer  → GazeBehavior   (gazeRadius, speedMult, easeFn)
└── affect layer → ExpressionBehavior  (lids, brows, mouth, blinkMult)
    └── per-state: enterDur, enterEase, maxHold
    └── per-pair: transTable overrides

GazeSaccade (bezier arc engine)
├── anticipation phase (counter-move wind-up)
├── main arc phase (quadratic bezier)
└── follow-through (damped spring overshoot)

BlinkController
├── anticipation
└── follow-through (spring)

BodyController (Three.js)
├── headGroup — underdamped spring yaw/pitch + arc roll tilt
├── robot body — spring yaw + arc pitch lean
└── ball — draggable gaze target, triggers 75/25 head/eye tracking

EyeRenderer (canvas → THREE.CanvasTexture)
├── squash & stretch during saccades
└── behavior expression: lids, brows, mouth, nose
```

The compositor is designed for external driving — each layer can be set independently via WebSocket (`attn`, `affect` message types) to combine gaze patterns with emotional expressions freely.

-----

## 12 Principles of Animation

From Johnston & Thomas, *The Illusion of Life* (Disney, 1981) — the design checklist for the project. Most principles are implemented; exaggeration and overlap have the most room to grow.

See [docs/animation-principles.md](docs/animation-principles.md) for the full status table and notes on where to push further.

-----

## Roadmap

### UI & Layout
- [x] Multiple eyes (stereo)
- [x] Move event log to opposite side of page
- [x] 3-column layout — canvas centered between left event log panel and right controls panel
- [x] Visibility toggles — checkboxes to show/hide pupils, eyelids, brows, mouth
- [x] Config persistence — save/load/export via localStorage
- [x] Color controls — floor, robot body, wheels

### Eye Shape & Controls
- [x] Eye rotation mirroring — left/right eyes tilt opposite directions
- [x] Pupil spacing — independent horizontal offset per eye, child of eye spacing
- [x] Brow spacing — independent horizontal position, child of eye spacing
- [x] Lid rotation — tilt lids independently of eye rotation

### Face Anatomy
- [x] Eyelids — oval matching eye shape with curved crop; controls for rotation, curvature, translation, color
- [x] Brows — shape, taper (inner/outer ends, round caps), and animation controls
- [x] Mouth — shape, taper, and animation controls
- [x] Nose — bridge and nostril shape controls
- [ ] Better blink mechanics — multi-stage lid travel, asymmetric open/close timing, hold at closed
- [ ] Phonemes — mouth shapes mapped to phoneme groups (A/E/I/O/U, consonants)
- [ ] Lip sync — drive phonemes from audio analysis or text-to-speech timing data

### Visual Feedback
- [x] Arc trail visualization — line showing recent pupil path, with visibility toggle and memory duration control
- [x] Saccade target indicator — show where the next gaze point will land before the eye moves there
- [x] Planning grid overlay — center crosshair, grid, and no-go border zone for layout reference
- [x] Anticipation & follow-through — brief wind-up before saccade fires, slight overshoot/settle on landing
- [ ] Bezier arc preview — ghost the full arc path before a saccade executes
- [ ] Spring force vectors — arrows on head/body showing current spring acceleration
- [ ] Velocity heatmap — overlay showing dwell density (where the eye spends the most time)
- [ ] Behavior transition flash — subtle color pulse when behavior switches
- [ ] Blink countdown indicator — visual cue showing time until next blink (dev tool)
- [ ] Clipping warning — highlight when pupil travel pushes near the iris edge
- [ ] FPS counter — frame rate display, useful for hardware porting
- [ ] Frame timing graph — sparkline of frame render times

### Conversational Robot States
- [x] Attention states — idle, alert, searching
- [x] Conversational states — listening, processing, speaking, waiting
- [x] Affective states — engaged, confused, pleased, uncomfortable
- [x] Operational states — waking, resting, interrupted
- [x] State compositor — two independent layers (gaze + expression); any behavior usable as either template; mixed freely; live status display
- [x] State machine — per-state blend duration + easing (`interrupted` = instant snap, `resting` = 1.5s melt); pair-specific overrides (e.g. `pleased→uncomfortable` = 0.9s reluctant shift); `maxHold` auto-return; live progress bar
- [x] Micro-expressions — brief flashes of affect (200ms) that don't fully commit, then return to base state; 5 named presets (startle, wince, brighten, doubt, drift); independent hold timer; WebSocket `micro` command

### Drive System

See [docs/drive-system.md](docs/drive-system.md) for the full design.

- [x] Pressure/scoring — per-state pressure vector, novelty decay on active state, hysteresis threshold, `updateDrive()` each frame
- [x] Drive layer — `driveProfile` defines resting pressure per state (baseline temperament); idle/curious oscillation from novelty decay
- [x] Rule engine — `emitDriveEvent()` with built-in events (face_detected, speech_start, startle, etc.); `addPressure()` for direct injection; WebSocket `event` and `pressure` commands
- [x] Transition enforcer — `transEnforcer` table reroutes illegal drive-originated jumps through intermediate states (e.g. `resting→anything` goes via `waking`); blend-guard prevents drive from interrupting in-progress transitions
- [ ] Personal time — spatial memory of dwell history shapes idle gaze over a session

### Environmental Triggers

See [docs/environmental-triggers.md](docs/environmental-triggers.md) for the full design and implementation notes.

- [ ] Time of day — scheduler adjusts drive profile weights through a day/night curve; time-since-last-interaction builds restlessness
- [ ] Presence detection — PIR or camera; person enters/leaves room triggers `attentive`/`searching`/`resting` pressure cycles
- [ ] Ambient audio — microphone amplitude envelope drives arousal level; transients fire `startle` events
- [ ] System state — CPU load, battery, network status, errors feed drive events with no extra hardware
- [ ] Proximity — distance to nearest person shapes `comfortable`/`uncomfortable` pressure and gaze aversion
- [ ] Calendar / schedule context — meeting, focus, idle modes shift drive profile baseline

### Animation Hierarchy
- [x] Global face translation — subtle whole-face shift toward gaze target, parent transform above gaze
- [x] Motion cascade — layered delays: pupils → face shift → head turn → body shift, each with independent speed and amount
- [x] Squash & stretch — eye shape deforms slightly during fast saccades
- [x] Spring physics — head/body rotation uses underdamped spring dynamics; natural ease-in/out and slight overshoot on every movement
- [x] Arc motion — head tilts into yaw turns, body leans during rotation; 3D motion traces curves through space
- [x] Principles off switch — button zeros arc curvature, squash/stretch, anticipation, follow-through, arc tilt/lean, cascade, blink anticipation/overshoot, and forces linear easing + critically-damped springs; snapshot restores originals on toggle-back

### API & Integration
- [x] WebSocket API — relay server + browser client; external processes send `behavior`, `attn`, `affect`, `param`, `look`, `blink`, `color`, `event`, `pressure`, `micro` commands
- [x] Object tracking — draggable ball in 3D scene; robot tracks with 75/25 head/eye split; configurable timeout reverts to idle wander
- [ ] Gaze vector export — time-stamped gaze vectors exported as CSV/JSON for external analysis
- [ ] Gaze-based UI interaction — dwell-time selection for UI elements

### Robot Deployment

See [docs/robot-architecture.md](docs/robot-architecture.md) for the full design: state broadcast architecture, telemetry sim view, recorder/playback, hardware adapters, and input pipeline.

**Engine & architecture**
- [ ] Engine extraction — split `index.html` into `engine.js` + renderer modules; prerequisite for all deployment work
- [ ] State broadcast — engine publishes full state packet to WebSocket each tick; all subscribers receive identical stream
- [ ] Browser telemetry mode — browser receives state rather than computing it; cannot drift from robot reality

**Observability**
- [ ] Recorder — WebSocket subscriber writes JSONL state log; no logic, just timestamps and packets
- [ ] Playback — feed recorded JSONL back into browser renderer; scrub-able, speed-adjustable

**Hardware output**
- [ ] OLED adapter — re-implement `EyeRenderer` as 1-bit pixel buffer writer for SSD1306/SH1106 via i2c
- [ ] Servo adapter — map `gazeX/Y`, `lidOpenness`, `head3DYaw/Pitch` to servo positions via pigpio or serial
- [ ] Raspberry Pi deployment — Pi 4/Jetson full stack (Node.js engine + Chromium kiosk); Pi Zero headless

**Input pipeline**
- [ ] Audio pipeline — mic amplitude → blink rate/processing affect; wake word → alert+listening; silence → waiting
- [ ] Face tracking — camera → face position events → drive system (`face_detected`, `face_lost`)
- [ ] Head pose integration — external pitch/yaw/roll inputs offset gaze target
- [ ] LLM integration — inference state → drive events (`speech_start`, `speech_end`, `uncertain`)

-----

## Running locally

Just open `index.html` in a browser. No build step needed.

```bash
open index.html
# or
python3 -m http.server 8080
```

-----

## License

MIT
