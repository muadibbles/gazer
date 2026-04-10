# gazer 👁️

An exploration of the 12 principles of animation applied to robotics — using a 3D robot with expressive eyes as the test subject. The goal is to understand what makes a robot feel alive rather than mechanical: how motion, timing, and expression create the impression of weight, intention, and personality. A secondary thread is robot personality implementation: how independent behavioral layers, state machines, and an emotion engine can give a robot a coherent inner life that shapes how it moves and responds over time. Browser-based, designed to eventually run on embedded hardware (Raspberry Pi, Jetson, etc).

-----

## What it does

- **Smooth arc saccades** — eye movement follows quadratic bezier curves, not linear paths, so it feels alive
- **Compositor** — two independent layers: *gaze* (controls saccade pattern) and *expression* (controls lids, brows, mouth); any behavior can be used as either template, mixed freely
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

All 15 behaviors are available to both compositor layers independently.

### Classic
|Behavior   |Gaze Range          |Speed |Blink Rate   |Feel                |Enter  |
|-----------|--------------------|------|-------------|--------------------| ------|
|`idle`     |moderate            |normal|normal       |relaxed, wandering  |0.40s  |
|`attentive`|tight (center focus)|fast  |slow         |alert, tracking     |0.20s  |
|`curious`  |wide                |medium|slightly slow|scanning, exploring |0.32s  |
|`sleepy`   |small               |slow  |very high    |heavy-lidded, drowsy|0.90s  |

### Attention
|Behavior    |Gaze Range|Speed|Blink Rate|Feel                          |Enter  |
|------------|----------|-----|----------|------------------------------|-------|
|`alert`     |very tight|very fast|very slow|snapped to source, wide-eyed |0.06s  |
|`searching` |very wide |medium-fast|moderate|scanning, seeking            |0.28s  |

### Conversational
|Behavior     |Gaze Range|Speed|Blink Rate|Feel                         |Enter  |
|-------------|----------|-----|----------|-----------------------------|-------|
|`listening`  |tight     |slow |slow      |receptive, focused on speaker|0.40s  |
|`processing` |medium    |slow |high      |inward, defocused, thinking  |0.55s  |
|`speaking`   |medium    |normal|normal   |natural, expressive          |0.28s  |
|`waiting`    |medium    |slow |slightly high|patient, expectant        |0.45s  |

### Affective
|Behavior       |Gaze Range|Speed|Blink Rate|Feel                       |Enter  |
|---------------|----------|-----|----------|---------------------------|-------|
|`engaged`      |tight     |fast |very slow |bright, leaning in         |0.25s  |
|`confused`     |medium    |medium|moderate |erratic, furrowed          |0.35s  |
|`pleased`      |medium    |normal|high     |squinting smile, happy     |0.50s  |
|`uncomfortable`|wide      |medium|high     |averted gaze, nervous      |0.70s  |

### Operational
|Behavior      |Gaze Range|Speed   |Blink Rate|Feel                      |Enter  |
|--------------|----------|--------|----------|--------------------------|-------|
|`waking`      |very tight|sluggish|very high |groggy, coming online     |1.20s  |
|`resting`     |tiny      |very slow|very high|nearly shut down          |1.50s  |
|`interrupted` |snap      |very fast|very low |startle, instant redirect |0.00s ⚡|

`interrupted` also auto-returns to the previous state after 0.5s (`maxHold`).

### Pair-specific transition overrides
| Pair | Duration | Feel |
|------|----------|------|
| `pleased → uncomfortable` | 0.90s | reluctant, slow shift |
| `uncomfortable → pleased` | 0.55s | cautious brightening |
| `resting → interrupted` | 0.08s | groggy startle |
| `resting → alert` | 0.25s | slow state takes a breath first |

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

From Johnston & Thomas, *The Illusion of Life* (Disney, 1981). Gazer uses these as a design checklist.

| # | Principle | Description | Status |
|---|-----------|-------------|--------|
| 1 | **Squash & stretch** | Deformation conveys weight and flexibility | ✅ eye deforms during saccades; easing on entry/exit of each state |
| 2 | **Anticipation** | Wind-up before action signals what's coming | ✅ brief counter-move before saccade fires |
| 3 | **Staging** | Clear composition, one idea at a time | n/a — single subject |
| 4 | **Straight ahead vs pose-to-pose** | Two approaches to planning movement | n/a |
| 5 | **Follow-through & overlapping action** | Parts settle independently after movement stops | ✅ overshoot spring on saccades; head/body spring overshoot; pupils → face → head → body cascade at different rates |
| 6 | **Slow in and slow out** | Ease in/out — most motion happens in the middle | ✅ easing library on saccades; head/body spring physics eases in *and* out; per-state `enterEase` shapes every compositor transition |
| 7 | **Arcs** | Natural motion follows curved paths, not straight lines | ✅ quadratic bezier saccades; head tilts into yaw turns + body leans into rotation — 3D motion traces curves, not flat angles |
| 8 | **Secondary action** | Supporting motions that reinforce the primary one | ✅ face/head/body cascade; brow and mouth react to blink |
| 9 | **Timing** | Number of frames determines weight and mood | ✅ per-behavior speed, pause, and blink timing; per-state `enterDur` |
| 10 | **Exaggeration** | Push beyond realism to read as more real | 🔨 behavior states push values — room to go further |
| 11 | **Solid drawing** | Volume, weight, balance (the 3D-thinking principle) | ✅ three.js robot body with physical presence |
| 12 | **Appeal** | Charisma — the thing that makes you want to watch | the whole project |

Areas with room to grow: **exaggeration** (states could push harder at extremes; `interrupted`/`alert` could squash harder, velocities could spike further) and **overlap** (lids, brows, mouth each settling at different rates after a behavior change).

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
- [ ] Micro-expressions — brief flashes of affect (200ms) that don't fully commit, then return to base state

### Emotion Engine
- [ ] Pressure/scoring system — each state has a "pressure" that builds over time or from stimulus; highest pressure wins; novelty decay makes gazer restless
- [ ] Rule engine — simple if/then rules mapping external events to state changes (`speaking=true → attn:speaking, affect:engaged`)
- [ ] Transition enforcer — prevents illegal jumps (e.g. `resting → interrupted` must go through `alert`), enforces hold times
- [ ] External state driver — WebSocket / LLM / audio pipeline pushes `{ attn, affect }` pairs to the compositor
- [ ] Drive layer — what gazer wants when no external input is present; bridges into personal time

### Agency & Memory
- [ ] Gazer personal time — when not attending to an operator target or external stimulus, gazer explores the space autonomously and builds its own spatial memories: locations it has looked at, how long, how often. Over time these memories shape where it chooses to look during idle, giving it a sense of accumulated experience and preference.

### Expression System
- [ ] Emotion layer (surprise, disgust, joy) — drives eyelids, brows, mouth together as named presets
- [ ] Environmental context awareness — context tags (e.g. "Meeting", "Reading") influence behavior parameters

### Animation Hierarchy
- [x] Global face translation — subtle whole-face shift toward gaze target, parent transform above gaze
- [x] Motion cascade — layered delays: pupils → face shift → head turn → body shift, each with independent speed and amount
- [x] Squash & stretch — eye shape deforms slightly during fast saccades
- [x] Spring physics — head/body rotation uses underdamped spring dynamics; natural ease-in/out and slight overshoot on every movement
- [x] Arc motion — head tilts into yaw turns, body leans during rotation; 3D motion traces curves through space

### API & Integration
- [x] WebSocket API — relay server + browser client; external processes send `behavior`, `attn`, `affect`, `param`, `look`, `blink`, `color` commands
- [ ] Raspberry Pi output layer (OLED / servo)
- [ ] Local LLM integration — inference state drives behavior controller
- [x] Object tracking — draggable ball in 3D scene; robot tracks with 75/25 head/eye split; configurable timeout reverts to idle wander
- [ ] Face tracking — gaze tracks detected faces, overriding random wandering
- [ ] Head pose integration — pitch/yaw/roll inputs make gaze relative to head orientation
- [ ] Gaze vector export — time-stamped gaze vectors exported as CSV/JSON for external analysis

### 3D & Platform
- [x] 3D body — Three.js robot scene; face canvas mapped as texture; head-leads-body cascade with spring physics; hub caps, color controls
- [ ] Gaze-based UI interaction — dwell-time selection for UI elements

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
