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

|Behavior   |Gaze Range          |Speed |Blink Rate   |Feel                |
|-----------|--------------------|------|-------------|--------------------|
|`idle`     |moderate            |normal|normal       |relaxed, wandering  |
|`attentive`|tight (center focus)|fast  |slow         |alert, tracking     |
|`curious`  |wide                |medium|slightly slow|scanning, exploring |
|`sleepy`   |small               |slow  |very high    |heavy-lidded, drowsy|

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
- [x] Brows — shape and animation controls
- [x] Mouth — shape and animation controls
- [ ] Phonemes — mouth shapes mapped to phoneme groups (A/E/I/O/U, consonants)
- [ ] Lip sync — drive phonemes from audio analysis or text-to-speech timing data

### Visual Feedback
- [x] Arc trail visualization — line showing recent pupil path, with visibility toggle and memory duration control
- [x] Saccade target indicator — show where the next gaze point will land before the eye moves there
- [ ] Bezier arc preview — ghost the full arc path before a saccade executes
- [x] Anticipation & follow-through — brief wind-up before saccade fires, slight overshoot/settle on landing
- [ ] Velocity heatmap — overlay showing dwell density (where the eye spends the most time)
- [ ] Behavior transition flash — subtle color pulse when behavior switches
- [ ] Blink countdown indicator — visual cue showing time until next blink (dev tool)
- [ ] Clipping warning — highlight when pupil travel pushes near the iris edge
- [ ] FPS counter — frame rate display, useful for hardware porting
- [ ] Frame timing graph — sparkline of frame render times
- [ ] Behavior state machine visualization — debug tool to visualize state transitions
- [ ] Performance profiling mode — debug mode reporting CPU/GPU usage for embedded targeting

### Expression System
- [ ] Emotion layer (surprise, disgust, joy) — drives eyelids, brows, mouth together
- [ ] Environmental context awareness — context tags (e.g. "Meeting", "Reading") influence behavior parameters

### Animation Hierarchy
- [x] Global face translation — subtle whole-face shift toward the current gaze target, parent transform above gaze direction so the entire rig moves together

### 3D & Platform
- [ ] 3D body — three.js scene using the face as the character's face
- [ ] WebSocket API — external behavior triggers
- [ ] Raspberry Pi output layer (OLED / servo)
- [ ] Local LLM integration — inference state drives behavior controller
- [ ] Object/face tracking — gaze tracks detected faces or objects, overriding random wandering
- [ ] Head pose integration — pitch/yaw/roll inputs make gaze relative to head orientation
- [ ] Gaze-based UI interaction — dwell-time selection for UI elements
- [ ] Gaze vector export — time-stamped gaze vectors exported as CSV/JSON for external analysis

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
