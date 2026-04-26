# Roadmap

---

## Done

### Core rendering

- [x] 2D eye renderer — compositor, attn + affect layers, 15 behaviors
- [x] 12 animation principles — arcs, squash/stretch, overshoot, anticipation, blink follow-through, motion cascade (face → head → body)
- [x] Blink system — interval, half-blink, squint, lid bow, facial reactions
- [x] WebSocket API — inbound commands: `behavior`, `attn`, `affect`, `micro`, `event`, `pressure`, `param`, `look`, `blink`, `color`

### 3D world

- [x] Three.js robot — self-balancing form, head/body spring physics
- [x] Full-body attention — head yaw/pitch + body yaw + eye gaze, all spring-driven toward a 3D world point
- [x] Manual ball override — drag to steer (XZ plane), Y-drag handle on ball; auto-releases after timeout
- [x] Camera — orbit controls, zoom extended to 60 units

### Multi-camera views

- [x] **Face cam** — 2D eye canvas overlaid in top-left quadrant of 4-up grid
- [x] **POV cam** — mounted at robot eye, looks in gaze direction (head quaternion + gazeX/Y); POI labels project through this camera in both single and 4-up mode
- [x] **Ceiling cam** — top-down perspective, pan + zoom only (no rotation), up=-Z for gimbal stability; centred over POI cluster
- [x] **Perspective cam** — existing orbit-controlled camera
- [x] **View switcher** — Face / POV / Ceiling / Persp / 4-up buttons; active button highlights; expand buttons on each 4-up quadrant
- [x] **Viewport fix** — logical-pixel viewport coordinates (fixes 2× retina displays)

### Drive system

- [x] Pressure / scoring — per-behavior float, novelty decay, hysteresis threshold
- [x] Drive layer — baseline profile (`idle` 0.40, `curious` 0.25), session temperament
- [x] Transition enforcer — illegal transition rerouting (`resting → waking → ...`)
- [x] Rule engine — declarative `ruleTable`, 19+ named events, typed actions (`pressure`, `look3D`, `setAttn`, `microExpress`, `microAuto`, `assignTask`, `completeTask`)
- [x] Task system — queued directed interactions; utility (transactional) + social (open-ended) modes; interrupt support; POI affordances schema
- [x] POI-sourced events — `dog_begging`, `dog_play_request`, `cat_greeting`, `kid_play_request`, `arrival`, `departure`

### World model

- [x] POIs — 8 named 3D markers (Person, Child, Cat, Dog, TV, Window, Food Bowl, Front Door)
- [x] POI categories + salience — person > pet > object baseline weights
- [x] Behavior → POI affinity — `POI_BEHAVIOR_AFFINITY` table shapes which POIs get attention in each state
- [x] `look3D(x, y, z, category)` — rule engine action that repositions a POI and snaps attention
- [x] Draggable POIs — hit-test before ball, positions persist via localStorage
- [x] Personal time — per-POI `familiarity` (decaying, drives novelty selection) + `attention` (cumulative, visualized)
- [x] Attention visualization — marker scale + fill bar by cumulative dwell time
- [x] POI info widget — left panel shows active POI name, category, familiarity bar, attention time, affordance tags

### Expression depth

- [x] Speaking face — amplitude-driven mouth; `params.amplitude` (0–1) opens mouth from closed curve to filled shape; `mouthOpenMax` controls height; smoothed at ~80ms for speech sync
- [x] Listening face — tighter gaze, slower blink, more open lids, raised brows; reduced saccade range while attending
- [x] POI-triggered expressions — `microAuto` picks pleased/curious by familiarity; per-event micros for dog, cat, kid, arrival, departure, face lost

### Config & persistence

- [x] localStorage — params, colors, POI positions survive refresh
- [x] Version stamping — title tag + header span for deployment verification

### Input pipeline

- [x] `face_detect.py` — webcam → MediaPipe Face Detection → 3D world position → `face_detected` + `look3D` at 5 Hz + `face_lost` (debounced); `--hfov`, `--camera`, `--no-display`
- [x] `audio.py` — mic → RMS → VAD state machine (`speech_start` / `speech_end`); `startle` on sudden spike; `loud_sound` on threshold; continuous `amplitude` param at 20 Hz; `--device`, `--threshold`, `--list-devices`
- [x] `time_scheduler.py` — day curve: morning (curious↑ alert↑), day (neutral), evening (idle↑), night (sleepy↑ resting↑); fires pressure commands every 2 min; `--interval`, `--dry-run`

### State broadcast

- [x] `wsBroadcastState()` — 20 Hz WebSocket out; `type: "state"` packet with full attn/affect/behavior/gaze/drive/task/pois
- [x] `recorder.py` — connects to relay, filters `type: "state"`, appends JSONL; auto-reconnects with backoff
- [x] Renderer Mode — toggle in WebSocket panel; engine pauses, incoming state packets hydrate; motion cascade + 3D springs smooth 20 Hz → 60 fps

### Dev tooling

- [x] `server.py` — WebSocket relay; all clients in one broadcast group; state packets throttled to 1/s in console
- [x] `send.py` — one-shot command sender; full event type list, `look3D`, data payloads
- [x] `states.py` — scenario runner + interactive REPL; 11 named scenarios; `speak`, `event`, `task`, `complete` commands
- [x] `simulate.py` — synthetic sensor simulator; virtual person lifecycle, speech bursts, ambient sounds; `--fast`, `--once`, `--seed`, `--speed`
- [x] `replay.py` — plays back a JSONL session at original cadence; `--speed`, `--loop`

---

## Up next

### Documentation

- [x] **README** — quick start, architecture, full scripts reference (`server.py`, `send.py`, `states.py`, `recorder.py`, `replay.py`, `simulate.py`, `face_detect.py`, `audio.py`, `time_scheduler.py`), full-stack runbook, params table

### Mobility + head motion overhaul

- [x] **3-phase head motion** — anticipation → S-curve move → overshoot/return; threshold-gated (only fires on turns ≥ `headThreshold` °); `headMoveSpeed`, `headAntAmt/Dur`, `headOvAmt/Dur` params exposed
- [x] **`upperBody` group** — body+head pitch separated from wheels; wheels always stay on the ground during lean
- [x] **Differential drive kinematics** — `v_L = v − ω·d/2`, `v_R = v + ω·d/2`; wheel angle += `v_wheel / WR * dt`; realistic arc turns (outer wheel faster than inner)
- [x] **Mobility state machine** — `hold → wander → approach → scan → returning → charging`; state dictates movement speed; disabled via checkbox
- [x] **State-gated wandering** — only in `curious`/`alert`/`playful`; `idle` stands and looks around; `resting`/`sleepy` stays put
- [x] **POI-biased wander targets** — scoring: category weight × familiarity novelty × spatial-memory novelty; humans > pets > objects
- [x] **Spatial memory** — 0.5 m grid over 26 × 26 m floor; timestamps last visit per cell; novelty score decays toward 1 as time passes
- [x] **Potential-field obstacle avoidance** — object POIs repel within 1.5 m; floor boundary repels at edges; forces blend into steering command
- [x] **Battery system** — drains from movement (0.02 %/s), mental activity (0.01 %/s), idle (0.005 %/s); charges at Charger (0.03 %/s); low battery (30 %) finishes current leg then routes home; critical (10 %) returns immediately; 9 pm–7 am sleeps on charger
- [x] **Charger POI** — named home-base marker; robot docks and idles while charging; can still respond to world events while charging
- [x] **Battery UI widget** — bar + percentage + state label; "Trigger low battery" checkbox for testing; "Mobility enabled" toggle
- [x] **Travel camera** — orbit-controlled, follows robot as it moves; target translated by robot delta each frame; added to view switcher as `vbtn-travel`
- [x] **Camera persistence** — orbit/ceiling/travel positions saved to localStorage via `getCameras()` / `restoreCameras()` in `window.three`
- [x] **Camera-to-world transform** — `cameraLocal: true` rule flag; `face_detected` converts detector-relative XZ to world coords via `getRobotPose()` (robot position + heading yaw)
- [x] **POI drag in ceiling cam** — `getActiveCamera()` helper; `startDrag`/`moveDrag` raycast through whichever camera is active; `endDrag` restores correct OrbitControls

### Engine extraction

Split `index.html` into deployable modules. Prerequisite for hardware targets.

- [ ] `engine.js` — compositor, drive, behaviors, saccade planner, state machine; no DOM dependency
- [ ] `renderer.canvas.js` — 2D eye drawing
- [ ] `renderer.three.js` — Three.js body scene
- [ ] `main.browser.js` — browser entry: engine + renderers + WebSocket state receiver
- [ ] `main.robot.js` — robot entry: engine + hardware renderers + state broadcaster

### Testing

- [ ] Unit tests — compositor, drive, transition enforcer (Node.js, no browser)
- [ ] Browser tests — Playwright: compositor blending, micro-expression return, principles toggle
- [ ] CI — GitHub Actions on push

### Hardware output

- [ ] `renderer.oled.js` — 1-bit pixel buffer for SSD1306/SH1106 via i2c
- [ ] `renderer.servo.js` — maps gaze/lid/head values to servo positions via pigpio

## Misc

- [ ] collapse all right panel bellows by default

- [ ] only one poi on by default

- [ ] fix travel cam to stay locked to the head and shoulders of hte bot

- [ ] overhead cam should be orhtographic

- [ ] shadow from bot only seems to be cast in the center of the floor

- [ ] if a POI moves the both should adjust it's course to meet it

### Bugs

- [ ] Trigger low battery checkbox not responding — wiring between HTML checkbox and module-scoped `batteryForceLow`
- [ ] Saccade frequency — logs show almost entirely blinks, nearly no saccades; investigate `behaviorTimer` / `gazeTargetActive` suppressing saccade planner while a POI is tracked
- [ ] Live State shows blinks almost entirely, never saccades and no other behaviors
- [ ] add one visible tick to each wheel so we can see the wheels rotating

### Drive system UI

- [ ] Drive widget — battery widget already shows `mobilityState`; extend it to also display `driveV`, `driveOmega`, and current wander target label (all in `window.driveState`)

### Navigation behavior

- [ ] Robot doesn't look forward when approaching POIs
- [ ] Robot should stop ~3 feet (0.9 m) from a POI instead of walking into it

### World model

- [ ] POIs at realistic heights — Person: ~1.8 m, Dog: ~0.4 m, Cat: ~0.3 m, Child: ~1.0 m, Charger: floor level

### Simulator

- [ ] Move Person POI as the virtual person walks their organic path — send `look3D` to reposition the marker each step
- [ ] Loud sounds should fire with coordinates near a random enabled POI rather than a fixed position
- [ ] recorder.py needs to poll robot posture way more often

---

## Later / deployment context

- [ ] LLM integration — speaking/listening cycle driven by speech pipeline
- [ ] Calendar / schedule context — shifts drive profile for meetings, focus time, end of day
- [ ] Multiple named persons — expand POI set dynamically as faces are recognized
- [ ] Pi 4 / Jetson deployment — full stack with kiosk sim view on HDMI
- [ ] Pi Zero 2W deployment — headless, sim view on separate machine over network
