# HANDOVER — gazer dev session 2026-04-11 (session 2)

## 1. Project Overview

**gazer** — browser-based animated robot eye system. Three.js robot body, 2D eye compositor, WebSocket-driven behavior engine, autonomous mobility. Single `index.html` (~5900 lines), Python scripts for relay/sensors/sim. No build step.

**Stack:** Vanilla JS + Three.js + Canvas 2D (`index.html`), Python (`server.py`, `simulate.py`, etc.)

---

## 2. What We Did This Session

### New docs
- `docs/drive-pipeline.md` — full explanation of the event→rule→pressure→compositor→motion causal chain; the definitive "how does the robot decide what to do" doc
- `docs/behavior-test-plan.md` — how to elicit all 17 behaviors, what drives each, what to look for; includes scenario shortcuts
- `gazer-architecture.excalidraw` — Excalidraw system architecture diagram (open with VS Code Excalidraw extension)

### Scene / POI toggle panel (`index.html`)
- New **Scene** accordion in the left panel (between Drive and Eye Shape)
- Checkbox per POI, grouped by category (People / Pets / Objects / Infrastructure), with colored dots matching marker colors
- **ALL ON / ALL OFF** convenience buttons
- `window.setPOIEnabled(idx, enabled)` — hides mesh, hides both labels (main + POV), resets `poiIdx` if robot was attending that POI
- Render loop guards: `poi.mesh.visible = show && poi.enabled` and `poi.el.style.display = (poi.enabled && show && !behind)` — render loop was resetting these every frame, overwriting the disable
- `selectAttentionPOI()` skips disabled POIs in weight sum
- `scorePOI()` returns 0 for disabled POIs
- `computeRepulsion()` skips disabled POIs
- Attention hold countdown immediately releases a POI that was disabled mid-hold

### recorder.py — verbose mode
Complete rewrite. New flags:
- `-v` / `--verbose` — saves ALL WebSocket message types (events, commands, state); prints real-time transition alerts for attn/affect/POI/task changes; prints pressure dashboard (sorted bar chart) every 100 state packets (~5 s)
- `-q` / `--quiet` — silent recording, no console output
- Verbose files named `session_YYYYMMDD_HHMMSS_verbose.jsonl`; normal files unchanged
- `replay.py` updated to strip `_rx` field (added by verbose recorder) so verbose files play back cleanly

### Side-eye bug — multiple-iteration fix
Robot was looking hard to the side and staying there when attending POIs. Root cause was in `trackWorldPoint()` in `index.html`. Fixed in four layers:

1. **`selectAttentionPOI` total=0 fallback** — when all enabled non-charger POIs have zero weight, call `randomSaccade()` and set `poiIdx = -1` instead of falling through to `pois.length - 1` (the Charger, which is behind the robot at z=-4)
2. **Charger excluded from gaze selection** — Charger has salience 0.2 and was being picked as a gaze target ~12% of the time even when other POIs were active. Now excluded from `selectAttentionPOI` weight sum (mobility-only target)
3. **Angle sanity check** — in `preUpdate`, before calling `trackWorldPoint`, check if POI is more than `headRotationMax + 25°` to the side. If so, release (`poiIdx = -1`) so the robot picks a reachable one
4. **Root cause fix** — `remainingYaw = relYawDeg - s.head3DYaw` → `remainingYaw = relYawDeg - headYawTarget`. The old formula used the head's CURRENT position. During anticipation wind-up (head moves backward first), `s.head3DYaw` went negative, making `remainingYaw` huge and clamping eyes at the edge of the face for the entire head motion sequence. Using `headYawTarget` means eyes go straight to their final resting position on frame 1 and stay stable while the head does its choreography.
- Also: `EYE_NORM_DEG` raised from 15 → 25 so a 25° residual maps to full eye travel rather than 15°

---

## 3. Current State

### Working
- POI toggle panel fully functional — disable/enable POIs, geometry + labels + attention scoring all respect the flag
- verbose recorder captures transition events in real-time with pressure dashboard
- Side-eye fix applied — eyes should now sit stably at their target position during head motion

### Unknown / unconfirmed
- Side-eye fix: user applied but hadn't confirmed fully resolved at end of session. The root cause (headYawTarget vs head3DYaw) was identified and fixed. If still present, check `advanceHeadMotion` — the head might not be reaching target, making headYawTarget and actual settled head position diverge in edge cases.

### Still open from previous session
- **"Trigger low battery" checkbox not responding** — wiring issue between HTML checkbox and `window.batteryForceLow` / Three.js module local `batteryForceLow`
- **Drive system widget** — left panel showing live mobilityState, battery %, driveV, driveOmega, wander target (data available via `window.driveState`)
- **Simulator POI movement** — `simulate.py` should move Person POI as virtual person walks; loud sounds should fire from nearby POI

---

## 4. Key Decisions & Rationale

- **`headYawTarget` not `s.head3DYaw` for eye residual** — eye position must be stable; using current head position during the anticipation phase (head briefly goes backward) caused eyes to oscillate wildly. Target-based calculation gives eyes a fixed, calm destination regardless of what the head is doing.
- **Charger excluded from gaze** — Charger at z=-4 is directly behind the robot's default starting position. Including it in gaze selection (even at low salience 0.2) caused the robot to occasionally try to look 180° behind itself.
- **POI toggle via `enabled` flag not array splice** — keeping POIs in the array at fixed indices avoids breaking `poiIdx` references. The `enabled` flag is checked at every selection and scoring point instead.
- **Verbose recorder saves ALL message types** — the key insight for debugging behavior is knowing what TRIGGERED the change (face_detected, startle, etc.), not just the resulting state. Saving events and commands alongside state packets makes the log self-explanatory.

---

## 5. Pitfalls & Lessons Learned

- **Render loop overwrites DOM/Three.js state every frame** — any hide/show set outside the render loop will be overwritten on the next frame. Always add `poi.enabled` guards inside the render loop itself, not just in the setter function.
- **`selectAttentionPOI` fallback picks last array element** — the original code fell through to `state.poiIdx = pois.length - 1` when the weighted pick didn't land (floating-point edge cases or all weights zero). Index `pois.length - 1` = 8 = Charger. This silently caused the robot to fixate on the Charger.
- **Anticipation wind-up reverses head direction** — `head3DYaw` briefly goes negative when a rightward turn begins. Any math that uses current head position to compute residual will invert during this phase, creating a brief but jarring spike in eye position.
- **`state.behavior` does not exist** — still relevant from last session. State uses `state.attn` and `state.affect`. Any code reading `state.behavior` gets `undefined`.

---

## 6. Next Steps (priority order)

1. **Confirm side-eye is fully resolved** — run with simulate.py for a few minutes, watch the face. If still happening, check `advanceHeadMotion` in `index.html` — verify `headYawTarget` passed in matches where the head actually settles.
2. **Fix "Trigger low battery" checkbox** — find the checkbox element ID in the battery widget HTML, trace the `onchange` handler, verify it reaches the correct variable in the Three.js module scope.
3. **Drive system widget** — left panel accordion showing live: `mobilityState`, `battery %`, `driveV`, `driveOmega`, current wander target label, last visited POI. Data available on `window.driveState`.
4. **Simulator POI movement** — `simulate.py`: as the virtual person moves along their organic path, send `look3D` commands to reposition the Person POI. Loud sounds should fire with coordinates near a random enabled POI.
5. **Saccade frequency** — logs show mostly blinks, few saccades. Investigate `behaviorTimer` interaction with `selectAttentionPOI` — check if `gazeTargetActive = true` is suppressing the saccade planner too aggressively while a POI is tracked.
