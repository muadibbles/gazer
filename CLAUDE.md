# CLAUDE.md — gazer

Project-specific instructions for Claude Code. Read this at the start of every session.

---

## What this project is

**gazer** — browser-based animated robot eye system. Single `index.html` (~6100 lines), no build step. Python scripts for relay, sensors, and simulation.

**Stack:** Vanilla JS + Three.js + Canvas 2D (`index.html`), Python (`server.py`, `simulate.py`, `recorder.py`, `replay.py`, `send.py`, `states.py`, `face_detect.py`, `audio.py`, `time_scheduler.py`)

---

## Always do this when making changes

**Bump the version number.** It appears in two places in `index.html` — keep them in sync:
- Line 7: `<title>GAZER v0.XX</title>`
- Line 848: `<span>v0.XX — robot eye behavior system</span>`

Increment the minor version (e.g. v0.26 → v0.27) for any substantive change. This is how we verify the right build is loaded in the browser.

---

## Architecture

The codebase is one file split into two logical halves:

**Top half — 2D engine (lines ~1–5100):**
- `params` object — all tunable values (line ~1308)
- `state` object — live runtime state: `attn`, `affect`, `gazeX/Y`, `head3DYaw/Pitch`, `poiIdx`, etc. (line ~1610)
- Behavior compositor — 17 named behaviors, attn + affect layers
- Drive system — pressure/scoring, rule engine, task system
- `update()` — main 60 Hz loop

**Bottom half — Three.js world (lines ~5100–6124):**
- POIs, robot body, mobility/drive, cameras
- `preUpdate(dt)` — runs before each `update()` call; handles gaze targeting and drive integration
- `trackWorldPoint(targetPos, dt, s, p)` — shared math that drives head/body/eyes toward a 3D world point
- `window.three` — public API exposed to the top half

**Cross-half communication:**
- `window.state`, `window.params`, `window.pois` — shared objects
- `window.driveState` — live drive telemetry `{ mobilityState, battery, driveV, driveOmega, drivePos, driveYaw }`
- `window.batteryLevel` — exposed for UI widgets
- `window.setPOIEnabled(idx, bool)` — toggle POI visibility and attention scoring
- `window.advanceHeadMotion(s, dt, yawTarget, pitchTarget, p)` — 3-phase head motion

---

## Key invariants — do not break these

**Render loop overwrites everything every frame.** Any DOM or Three.js state set outside the render loop is overwritten on the next frame. Always add guards inside the render loop itself, not just in setter functions.

**`driveYaw` accumulates without normalization.** It grows forever as the robot turns — after a few minutes it can be `-2856°` or worse. Any code that does raw subtraction with `driveYaw` will produce huge angles that pin head and eyes to maximum. Always normalize: `((driveYaw * 180 / Math.PI) % 360 + 540) % 360 - 180`. The `relYawDeg` in `trackWorldPoint` must also be normalized after subtraction for the same reason. When debugging gaze issues, check `body3DYaw` in the state broadcast first — if it's not in `-180..180`, this is the problem.

**`trackWorldPoint` must use `drivePos` for yaw calculation.** The target yaw must be computed relative to the robot's position, not the world origin:
```js
// CORRECT
Math.atan2(targetPos.x - drivePos.x, targetPos.z - drivePos.z)
// WRONG — only works when robot is at origin
Math.atan2(targetPos.x, targetPos.z)
```

**Eye residual uses `headYawTarget`, not `s.head3DYaw`.** During anticipation wind-up the head moves backward (negative yaw), inflating the residual and pinning eyes at the edge of the face. Always use the target, not the current position.

**`state.behavior` does not exist.** State tracks `state.attn` and `state.affect`. Any code reading `state.behavior` gets `undefined`.

**`selectAttentionPOI` must handle `total === 0`.** If all enabled non-charger POIs have zero weight, call `randomSaccade()` and set `poiIdx = -1`. The old fallback was `poiIdx = pois.length - 1` = Charger (behind robot at z=-4).

**Charger is mobility-only, not a gaze target.** Exclude it from `selectAttentionPOI` weight sum. It sits at z=-4, directly behind the robot's default start position.

**POI `enabled` flag must be checked in 4 places:** selection weight sum, wander scoring (`scorePOI`), obstacle repulsion (`computeRepulsion`), and the render loop (mesh visibility + both label elements).

---

## Running the system

```bash
# Full stack
python server.py          # WebSocket relay on ws://localhost:8765
open index.html           # Browser — connect to relay automatically
python simulate.py        # Synthetic sensors (virtual person, sounds, speech)

# Hardware sensors (optional, instead of simulate.py)
python face_detect.py     # Webcam → MediaPipe → face_detected events
python audio.py           # Mic → VAD → speech_start/end/startle events
python time_scheduler.py  # Time-of-day pressure curves

# Dev tools
python send.py event startle         # One-shot command
python states.py                     # Interactive REPL + scenario runner
python recorder.py -v                # Verbose session recording
python replay.py session.jsonl       # Replay a recording
```

---

## Handover files

Session handovers are saved to `handovers/HANDOVER_YYYYMMDD_HHMMSS.md`. Read the most recent one at the start of a session for prior context. Run `/handover` at the end of each session to write a new one.
