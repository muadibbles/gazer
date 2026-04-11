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
- [x] Manual ball override — drag to steer, auto-releases after timeout
- [x] Camera — orbit controls, zoom extended to 60 units

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

### Config & persistence
- [x] localStorage — params, colors, POI positions survive refresh
- [x] Version stamping — title tag + header span for deployment verification

---

## Up next

### Multi-camera views
Four named cameras rendered as a switchable single view or a 2×2 grid.

- [ ] **Face cam** — camera attached to the robot's head, pointing at the face from slightly in front; shows the live 2D eye render on the 3D face mesh at all times regardless of orbit position
- [ ] **POV cam** — camera mounted at the robot's eye position, pointing in the direction of current gaze; shows what the robot is actually looking at in the 3D world
- [ ] **Ceiling cam** — fixed overhead orthographic view; surveys the full scene, all POIs, and the robot's body orientation at a glance
- [ ] **Perspective cam** — existing orbit-controlled camera, preserved as the fourth view
- [ ] **Layout toggle** — single-view selector (cycle through the four) and 2×2 four-up grid mode; each quadrant labeled

### Input pipeline
Connect the rule engine to real sensors. The rule engine is ready — it just needs events.

- [x] `send.py` upgrades — native `attn`, `affect`, `micro`, `event`, `pressure` commands; event data payloads (`x=`, `y=`, `z=`, `scale=`); `look3D` command
- [ ] Face detection process — camera → 3D position → `face_detected {x,y,z}` → person POI tracks a real face
- [ ] Audio process — microphone amplitude → `loud_sound` / `startle`; voice activity → `speech_start` / `speech_end`
- [ ] Time-of-day — scheduler that shifts drive profile weights on a day curve (morning alert, evening sleepy)

### State broadcast
The robot currently only receives commands. It needs to push state out.

- [ ] WebSocket out channel — engine serializes full state each tick, broadcasts to all subscribers
- [ ] Recorder — subscriber that appends state packets to JSONL for session replay
- [ ] Browser as pure renderer — receives state packets instead of computing them (prerequisite for deployment)

### Engine extraction
Split `index.html` into deployable modules.

- [ ] `engine.js` — compositor, drive, behaviors, saccade planner, state machine; no DOM dependency
- [ ] `renderer.canvas.js` — 2D eye drawing
- [ ] `renderer.three.js` — Three.js body scene
- [ ] `main.browser.js` — browser entry: engine + renderers + state receiver
- [ ] `main.robot.js` — robot entry: engine + hardware renderers + broadcaster

### Hardware output
- [ ] `renderer.oled.js` — 1-bit pixel buffer for SSD1306/SH1106 via i2c
- [ ] `renderer.servo.js` — maps gaze/lid/head values to servo positions via pigpio

### Expression depth
- [ ] Speaking face — mouth animation, phoneme-driven or amplitude-driven
- [x] Listening face — tighter gaze, slower blink, more open lids, raised brows; reduced saccade range while attending
- [x] POI-triggered expressions — `microAuto` picks pleased/curious by familiarity; per-event micros for dog, cat, kid, arrival, departure, face lost

### Testing
- [ ] Update `send.py` with all event types
- [ ] Unit tests — compositor, drive, transition enforcer (Node.js, no browser)
- [ ] Browser tests — Playwright, compositor blending, micro-expression return, principles toggle
- [ ] CI — GitHub Actions on push

---

## Later / deployment context

- [ ] LLM integration — speaking/listening cycle driven by speech pipeline
- [ ] Calendar / schedule context — shifts drive profile for meetings, focus time, end of day
- [ ] Multiple named persons — expand POI set dynamically as faces are recognized
- [ ] Pi 4 / Jetson deployment — full stack with kiosk sim view on HDMI
- [ ] Pi Zero 2W deployment — headless, sim view on separate machine over network
