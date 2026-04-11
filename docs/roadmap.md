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
- [x] `states.py` — interactive scenario tester; 11 named scenarios covering pets, tasks, social, multi-task queue, interrupt

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

### Dev tooling
- [x] `send.py` — full event type list, data payloads (`x=`, `y=`, `z=`, `scale=`), `look3D` command
- [x] `states.py` — scenario runner + interactive REPL with `speak`, `event`, `task`, `complete` commands

---

## Up next

### Input pipeline
- [x] **Face detection** — `face_detect.py`; webcam → MediaPipe Face Detection → 3D world position estimate → `face_detected` + `look3D` track at 5 Hz + `face_lost` (debounced); `--hfov`, `--camera`, `--no-display`
- [x] **Audio process** — `audio.py`; mic → RMS → `speech_start` / `speech_end` VAD state machine; `startle` on sudden spike; `loud_sound` on threshold; continuous `amplitude` param at 20 Hz for mouth sync; `--device`, `--threshold`, `--list-devices`
- [x] **Time-of-day scheduler** — `time_scheduler.py`; day curve: morning (curious↑ alert↑), day (neutral), evening (idle↑), night (sleepy↑ resting↑); fires pressure commands every 2 min; `--interval`, `--dry-run`

### State broadcast
- [x] **WebSocket out channel** — `wsBroadcastState()` at 20 Hz; `type: "state"` packet with full attn/affect/behavior/gaze/drive/task/pois
- [x] **Recorder** — `recorder.py`; connects to relay, filters `type: "state"`, appends JSONL with auto-reconnect
- [x] **Browser as pure renderer** — Renderer Mode toggle in WebSocket panel; engine pauses, incoming state packets hydrate; motion cascade + 3D springs smooth 20 Hz → 60 fps

### Engine extraction
Split `index.html` into deployable modules. Prerequisite for hardware targets.

- [ ] `engine.js` — compositor, drive, behaviors, saccade planner, state machine; no DOM dependency
- [ ] `renderer.canvas.js` — 2D eye drawing
- [ ] `renderer.three.js` — Three.js body scene
- [ ] `main.browser.js` — browser entry: engine + renderers + WebSocket state receiver
- [ ] `main.robot.js` — robot entry: engine + hardware renderers + state broadcaster

### Hardware output
- [ ] `renderer.oled.js` — 1-bit pixel buffer for SSD1306/SH1106 via i2c
- [ ] `renderer.servo.js` — maps gaze/lid/head values to servo positions via pigpio

### Testing
- [ ] Unit tests — compositor, drive, transition enforcer (Node.js, no browser)
- [ ] Browser tests — Playwright: compositor blending, micro-expression return, principles toggle
- [ ] CI — GitHub Actions on push

---

## Later / deployment context

- [ ] LLM integration — speaking/listening cycle driven by speech pipeline
- [ ] Calendar / schedule context — shifts drive profile for meetings, focus time, end of day
- [ ] Multiple named persons — expand POI set dynamically as faces are recognized
- [ ] Pi 4 / Jetson deployment — full stack with kiosk sim view on HDMI
- [ ] Pi Zero 2W deployment — headless, sim view on separate machine over network
