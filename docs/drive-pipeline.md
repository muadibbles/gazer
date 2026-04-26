# How the Robot Decides What to Do

This document explains the causal chain — what actually drives the robot's behavior from external event to physical response.

---

## The pipeline at a glance

```
World event
    ↓
Rule engine  →  pressure injection
    ↓
Pressure competition  →  behavior selected
    ↓
Compositor  →  attn layer + affect layer
    ↓
GazeSaccade · Head Controller · Mobility
    ↓
Eyes move · face changes · body moves
```

---

## Step 1 — Events come in

Something happens in the world. These arrive as named events over WebSocket from the input scripts:

| Event | Source |
|---|---|
| `face_detected` | `face_detect.py` — webcam sees a face |
| `face_lost` | `face_detect.py` — face leaves frame |
| `speech_start` | `audio.py` — VAD detects someone talking |
| `speech_end` | `audio.py` — speech stops |
| `startle` | `audio.py` — sudden loud sound spike |
| `loud_sound` | `audio.py` — sustained loud audio |
| `dog_begging`, `cat_greeting`, `kid_play_request` | POI-sourced events from the world model |
| `arrival`, `departure` | POI-sourced when a person POI becomes active |

Events can also be injected manually via `send.py` or `states.py` for testing.

---

## Step 2 — The rule engine reacts

A declarative rule table maps every event to a set of immediate actions. Rules don't change behavior directly — they adjust **pressure** and trigger transient effects.

Example rules:

| Event | Actions |
|---|---|
| `face_detected` | spike `curious` pressure · reposition Person POI · trigger micro-expression |
| `startle` | spike `alert` pressure · snap to `interrupted` · micro: startle |
| `speech_start` | raise `listening` pressure · set attn to `listening` |
| `speech_end` | lower `listening` pressure · restore previous attn |
| `dog_begging` | raise `curious` pressure · assign task · look at Dog POI |
| `arrival` | spike `alert` · micro: brighten · look at Front Door |

Rule actions include: `pressure`, `look3D`, `setAttn`, `setAffect`, `microExpress`, `microAuto`, `assignTask`, `completeTask`.

---

## Step 3 — Pressure decides who wins

Every behavior has a floating pressure value between 0 and 1. Every frame, the system:

1. **Pulls** all pressures toward a baseline driveProfile (`idle: 0.40`, `curious: 0.25` at rest)
2. **Decays** the currently active behavior's pressure (novelty decay — it gets boring over time)
3. **Switches** if any other behavior's pressure exceeds active + a hysteresis margin

This means the robot drifts naturally between states even without any external input, and events push it toward specific states temporarily. When the event's pressure injection fades, the robot drifts back toward the baseline.

Key parameters:
- `driveNoveltyDecay` — how fast the active state loses pressure (higher = more restless)
- `driveHysteresis` — margin required to trigger a switch (higher = more sticky)

Illegal transitions are enforced: e.g. `resting` cannot jump directly to `speaking` — it must pass through `waking` → `idle` first.

---

## Step 4 — The compositor outputs two independent layers

The winning behavior simultaneously drives two output layers:

| Layer | Controls | Examples |
|---|---|---|
| **Attn** (gaze layer) | Where the eyes look, saccade radius and speed | `curious` = wide wandering gaze · `listening` = tight focused gaze |
| **Affect** (expression layer) | Lids, brows, mouth shape, blink rate | `pleased` = soft lids, raised brows · `alert` = wide eyes, fast blinks |

The two layers are independent — you can pin one and let the drive system move only the other. This allows expressions like "curious gaze + uncomfortable expression" simultaneously.

**Micro-expressions** are short-duration affect overrides (0.2–0.5 s) that snap to a state and auto-return. They don't affect the attn layer and don't interrupt the drive system.

---

## Step 5 — Motion and mobility follow

The compositor output feeds three downstream systems:

**GazeSaccade** reads the attn layer:
- Plans the next eye movement target within the gaze radius
- Executes as a bézier arc with anticipation wind-up and overshoot follow-through
- Speed and radius are behavior-specific

**Head and body controller** follows gaze:
- 3-phase head motion: anticipation wind-up → S-curve move → overshoot settle
- Head tilts into yaw turns (arc roll); body leans during rotation
- Only fires for turns above the `headThreshold` parameter

**Mobility state machine** reads the attn behavior:
- `curious` / `alert` / `playful` → wander; approach POIs
- `idle` → stand still; look around at nearby POIs
- `resting` / `sleepy` → stay put
- `low battery` → finish current leg, route to Charger POI

---

## The full picture

There is no single "decision point." The robot's behavior is the result of a continuous pressure competition with natural decay. Key properties of this design:

- **Events are temporary** — pressure injections fade; the robot always drifts back to baseline
- **Behavior has inertia** — hysteresis prevents jittery switching on noisy sensor input
- **Expression and gaze are independent** — richer combinations than a single-state machine
- **Personality is the baseline** — the `driveProfile` defaults define the robot's resting temperament; adjusting them changes its character without touching any event logic

---

## Related docs

- [Drive system deep-dive](drive-system.md)
- [World model & POIs](world-model.md)
- [Behaviors reference](behaviors.md)
- [Testing the drive system](testing.md)
