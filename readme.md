# gazer 👁️

A browser-based robot eye animation and behavior system. Smooth arc-based gaze movement built as a proof of concept, designed to eventually run on embedded hardware (Raspberry Pi, Jetson, etc).

-----

## What it does

- **Smooth arc saccades** — eye movement follows quadratic bezier curves, not linear paths, so it feels alive
- **Behavior controller** — pluggable behavior states that govern gaze range, speed, blink rate, and easing
- **Easing library** — `inOutCubic`, `outBack`, `outQuart`, `inOutQuint` built in, easy to extend
- **Blink system** — natural blink timing per behavior
- **Click to look** — click anywhere on canvas to trigger a manual saccade

-----

## Behaviors

### Classic
|Behavior   |Gaze Range          |Speed |Blink Rate   |Feel                |
|-----------|--------------------|------|-------------|--------------------|
|`idle`     |moderate            |normal|normal       |relaxed, wandering  |
|`attentive`|tight (center focus)|fast  |slow         |alert, tracking     |
|`curious`  |wide                |medium|slightly slow|scanning, exploring |
|`sleepy`   |small               |slow  |very high    |heavy-lidded, drowsy|

### Attention
|Behavior    |Gaze Range|Speed|Blink Rate|Feel                          |
|------------|----------|-----|----------|------------------------------|
|`alert`     |very tight|very fast|very slow|snapped to source, wide-eyed |
|`searching` |very wide |medium-fast|moderate|scanning, seeking            |

### Conversational
|Behavior     |Gaze Range|Speed|Blink Rate|Feel                         |
|-------------|----------|-----|----------|-----------------------------|
|`listening`  |tight     |slow |slow      |receptive, focused on speaker|
|`processing` |medium    |slow |high      |inward, defocused, thinking  |
|`speaking`   |medium    |normal|normal   |natural, expressive          |
|`waiting`    |medium    |slow |slightly high|patient, expectant        |

### Affective
|Behavior       |Gaze Range|Speed|Blink Rate|Feel                       |
|---------------|----------|-----|----------|---------------------------|
|`engaged`      |tight     |fast |very slow |bright, leaning in         |
|`confused`     |medium    |medium|moderate |erratic, furrowed          |
|`pleased`      |medium    |normal|high     |squinting smile, happy     |
|`uncomfortable`|wide      |medium|high     |averted gaze, nervous      |

### Operational
|Behavior      |Gaze Range|Speed   |Blink Rate|Feel                      |
|--------------|----------|--------|----------|--------------------------|
|`waking`      |very tight|sluggish|very high |groggy, coming online     |
|`resting`     |tiny      |very slow|very high|nearly shut down          |
|`interrupted` |snap      |very fast|very low |startle, instant redirect |

-----

## Parameters

All exposed in the UI panel:

|Param          |Description                                           |
|---------------|------------------------------------------------------|
|`arcCurvature` |How much the gaze arc bends (0 = straight line)       |
|`gazeSpeed`    |Base speed multiplier for all saccades                |
|`saccadeJitter`|Adds slight randomness to target positions            |
|`lidOpenness`  |How wide the eye opens (overridden by sleepy behavior)|
|`pupilSize`    |Pupil radius relative to iris                         |
|`blinkInterval`|Seconds between blinks (modified by behavior)         |

-----

## Architecture

```
BehaviorController
├── behaviors/
│   ├── idle
│   ├── attentive
│   ├── curious
│   └── sleepy
├── GazeSaccade (bezier arc engine)
├── BlinkController
└── EyeRenderer (canvas)
```

The behavior controller is designed for expansion — each behavior is just a config object. Future behaviors can be driven by speech state, face detection, or inference output.

-----

## Roadmap

### UI & Layout
- [x] Multiple eyes (stereo)
- [x] Move event log to opposite side of page
- [x] 3-column layout — canvas centered between left event log panel and right controls panel
- [x] Visibility toggles — checkboxes to show/hide pupils, eyelids, brows, mouth
- [x] Config persistence — save/load/export via localStorage

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
- [ ] State compositor — combine attention + conversational + affective layers so e.g. `listening` + `engaged` looks different from `listening` + `confused`
- [ ] State machine transitions — define legal transitions and blend durations between states
- [ ] External state driver — WebSocket / LLM inference pushes state changes

### Agency & Memory
- [ ] Gazer personal time — when not attending to an operator target or external stimulus, gazer explores the space autonomously and builds its own spatial memories: locations it has looked at, how long, how often. Over time these memories shape where it chooses to look during idle, giving it a sense of accumulated experience and preference.

### Expression System
- [ ] Emotion layer (surprise, disgust, joy) — drives eyelids, brows, mouth together as named presets
- [ ] Environmental context awareness — context tags (e.g. "Meeting", "Reading") influence behavior parameters

### Animation Hierarchy
- [x] Global face translation — subtle whole-face shift toward gaze target, parent transform above gaze
- [x] Motion cascade — layered delays: pupils → face shift → head turn → body shift, each with independent speed and amount
- [x] Squash & stretch — eye shape deforms slightly during fast saccades

### API & Integration
- [x] WebSocket API — relay server + browser client; external processes send behavior/param/look/blink/color commands
- [ ] Raspberry Pi output layer (OLED / servo)
- [ ] Local LLM integration — inference state drives behavior controller
- [ ] Object/face tracking — gaze tracks detected faces or objects, overriding random wandering
- [ ] Head pose integration — pitch/yaw/roll inputs make gaze relative to head orientation
- [ ] Gaze vector export — time-stamped gaze vectors exported as CSV/JSON for external analysis

### 3D & Platform
- [ ] 3D body — three.js scene using the face as the character's face
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
