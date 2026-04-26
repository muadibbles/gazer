# Codebase Topics

Full topic map of what the gazer codebase and docs cover.

---

## Behavior System
- 15 named behaviors across 4 categories: Classic (idle, attentive, curious, sleepy), Attention (alert, searching), Conversational (listening, processing, speaking, waiting), Affective (pleased, uncomfortable, playful, resting, interrupted)
- Two-layer compositor — `attn` layer (gaze/saccade parameters) and `affect` layer (expression parameters) run independently and can be mixed freely
- Micro-expressions — brief 200–500ms affect flashes that sit on top of the current state without replacing it (startle, wince, brighten, doubt, drift)

## Drive System
- Pressure/scoring — each behavior carries a float pressure; highest pressure wins
- Novelty decay — pressure decays over time, preventing lock-in
- Hysteresis — threshold prevents rapid state flip-flopping
- Rule engine — declarative table of 19+ named events → typed actions (pressure injection, look3D, microExpress, assignTask)
- Task system — queued directed interactions in two modes: utility (transactional) and social (open-ended)
- Session temperament — baseline profile shapes default behavior mix

## Gaze & Eye Movement
- Saccade planner — quadratic bezier arcs, anticipation counter-move wind-up, overshoot spring
- Microsaccades — small random jumps during fixation (no drift component yet)
- Gaze targeting — eyes → face → head → body cascade at different rates; spring physics throughout
- Eye canvas renderer — 2D Canvas with lid, iris, pupil, brow, mouth; squash/stretch deformation during saccades

## World Model & POIs
- 8 named POIs — Person, Child, Cat, Dog, TV, Window, Food Bowl, Front Door + Charger home base
- Per-POI fields — position, category, salience, familiarity (decays), attention (cumulative dwell)
- POI behavior affinity — table maps behavior states to which POIs get attention
- look3D action — repositions a POI to a detected world coordinate and snaps attention
- Draggable POIs in ceiling cam; positions persist in localStorage

## Mobility & Navigation
- State machine — hold → wander → approach → scan → returning → charging
- Differential drive kinematics — v_L / v_R arc turns, realistic wheel physics
- Wander target scoring — category weight × familiarity novelty × spatial memory novelty
- Spatial memory — 0.5m grid, timestamps last visit per cell, novelty decays over time
- Potential-field obstacle avoidance — object POIs and floor boundary repel within radius
- State-gated wandering — only curious/alert/playful wander; idle/sleepy/resting stay put
- Battery system — drain from movement/activity, charge at home base, sleep schedule (9pm–7am)

## Expression & Expressiveness
- Affect layer — lids, brows, mouth curvature, blink rate per behavior state
- Speaking face — amplitude-driven mouth opening synced to audio (smoothed ~80ms)
- Blink system — interval, half-blink, squint, lid bow, brow/mouth reactions
- 12 Disney animation principles — arcs, squash/stretch, anticipation, follow-through, overlap, slow-in/slow-out, secondary action, timing, appeal; all applied and documented

## 3D Scene (Three.js)
- Robot body — self-balancing form, head/body spring physics, upperBody group (pitch separate from wheels)
- 5 cameras — Face, POV (eye-mounted), Ceiling (top-down), Travel (follows robot), Perspective
- Head controller — 3-phase motion profile: anticipation → S-curve → overshoot/return
- Full-body tracking — trackWorldPoint() drives head yaw/pitch + body yaw + eye gaze toward a 3D point

## Sensor Inputs (Python)
- face_detect.py — webcam → MediaPipe → 3D world position → face_detected events at 5 Hz
- audio.py — mic → RMS → VAD state machine; speech_start/end, startle, amplitude at 20 Hz
- time_scheduler.py — day-curve pressure: morning (curious/alert), evening (idle), night (sleepy/resting)
- simulate.py — synthetic sensor simulator for dev/testing

## Infrastructure
- server.py — WebSocket relay; all clients in one broadcast group
- State broadcast — wsBroadcastState() at 20 Hz; full attn/affect/gaze/drive/task/poi packet
- Renderer Mode — engine pauses, incoming state packets drive the UI (separates execution from observation)
- recorder.py / replay.py — JSONL timestamped session capture and playback
- send.py / states.py — one-shot command sender and scenario REPL

## Architecture Planning (not yet built)
- Engine extraction — split index.html into engine.js, renderer.canvas.js, renderer.three.js, main.browser.js, main.robot.js
- Unit test layer — compositor, drive, transition enforcer (Node.js, no browser required)

## Environmental Triggers
- Pressure sources: motion/proximity detection, audio events, face detection, time-of-day curves
- All route through emitDriveEvent() or addPressure() — no special architecture needed per source
