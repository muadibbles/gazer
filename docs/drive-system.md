# Drive System

The drive system is the decision layer that sits above the compositor. It answers one question: *what state does the robot want to be in right now?*

The compositor executes transitions. The affect and attn layers control expression and gaze. The drive system decides what gets requested of those layers, and why.

```
Drive system          — decides what to want
    ↓
Compositor            — executes the transition
  ├── attn layer      — gaze / saccade expression
  └── affect layer    — facial expression
```

---

## Why "drive" not "emotion"

Emotions are a subset of what this system manages. `processing`, `searching`, and `waiting` are not emotional states — they're functional. But they still need pressure, decay, and rules to govern when they're active. The system drives all 15 behaviors equally; calling it an emotion engine would misrepresent its scope and create a naming collision with the affect layer, which already handles emotional expression.

Drive is the right word: it's what the robot is motivated toward, independent of whether that motivation is emotional, social, or operational.

---

## Components

### 1. Pressure / scoring

Each behavior state carries a **pressure** value — a float that represents how strongly the robot is being pulled toward that state. The state with the highest pressure wins and gets requested to the compositor.

**Pressure sources:**
- External stimulus (a face detected → `attentive` pressure spikes)
- Time-based buildup (no input for N seconds → `searching` pressure rises)
- Internal state (currently `speaking` → `listening` pressure builds after a pause)
- Novelty decay (any state loses pressure the longer it's been active, making the robot restless)

**Novelty decay** is key to liveliness. A robot that locks into a state and stays there reads as stuck. Decay ensures that even in the absence of new stimulus, the robot will eventually shift.

```
pressure[state] += stimulusContribution(state, dt)
pressure[state] -= decayRate[state] * dt
pressure[state] = clamp(pressure[state], 0, 1)
```

The winning state is `argmax(pressure)`, but transitions only fire when the winner changes and the margin exceeds a hysteresis threshold — to prevent rapid flickering when two states are close.

---

### 2. Rule engine

A simple set of if/then rules that translate external events into pressure changes. Rules don't fire transitions directly — they adjust pressure and let the scoring system resolve the winner.

Examples:

```
event: speech_start                   → pressure[speaking]      += 0.8
event: speech_end                     → pressure[speaking]      -= 0.8; pressure[listening] += 0.3
event: face_detected({ x, y, z })     → pressure[attentive]     += 0.6; look3D(x, y, z, 'person')
event: face_lost                      → pressure[searching]     += 0.4
event: motion_detected({ x, y, z })   → pressure[searching]     += 0.3; look3D(x, y, z, 'object')
event: long_silence                   → pressure[waiting]       += 0.2 * t
event: loud_sound                     → microExpress('alert', 0.15)
event: error_state                    → pressure[uncomfortable] += 0.5
```

Rules can fire micro-expressions directly for events that don't warrant a full state change — a loud sound, a brief confusion, a moment of pleasure — without disrupting the pressure state underneath.

---

### 3. Transition enforcer

Some state transitions are illegal or should be gated. The transition enforcer sits between the drive system's output and the compositor's input.

Examples:
- `resting → interrupted` must pass through `alert` first (or use the existing fast transTable override)
- `resting` requires a minimum hold time before any exit
- `waking` can only transition to `idle` or `attentive`, not directly to `engaged`

The enforcer doesn't block transitions — it reroutes them. If the drive system wants `resting → speaking`, the enforcer inserts `waking` first.

---

### 4. Drive layer (baseline)

What the robot wants when no external stimulus is present. This is the autonomous floor — the idle personality that runs when nothing is happening.

The drive layer is not random. It's shaped by:
- **Default pressure profile** — `driveProfile` maps state names to resting pressure targets. Currently only `idle` (0.40) and `curious` (0.25) have non-zero baseline pull; the other 13 states default to 0 and only become active in response to external stimulus via the rule engine or direct `addPressure()` calls. This gives the robot an autonomous idle/curious oscillation while keeping all other states purely reactive. The profile can be extended to give any state a baseline: a robot with high resting `attentive` will stay focused on center; high resting `curious` will wander and scan.
- **Time-of-session effects** — pressure profiles can shift over a session. Early: higher `attentive`. Late: higher `sleepy`.
- **Personal time** — see below.

The drive layer produces a baseline pressure vector that stimulus rules add to. In the absence of all stimulus, the baseline wins and the robot expresses its own character.

---

### 5. Personal time and memory

When the robot is not responding to an external target, it explores autonomously — and remembers where it has looked, how long, and how often. These memories are stored per-POI (Point of Interest) and shape where the drive layer directs attention during idle.

Each POI tracks two values:
- **`familiarity`** — 0→1, accumulates while dwelling, decays when not attending. Drives novelty-weighted selection: recently visited POIs are less likely to be chosen next.
- **`attention`** — cumulative dwell time in seconds, never decays. Visualized as marker size and a fill bar in the label. Answers "what has the robot been most interested in this session?"

A POI visited often becomes familiar; the robot is less likely to fixate there again. A POI rarely visited becomes interesting. Over time the robot develops spatial preferences that are unique to its session history.

This gives the robot a sense of having been somewhere before — an accumulated experience that shapes present behavior. It's the lightest possible form of memory, but it makes the robot feel continuous rather than stateless.

---

### 6. Behavior → POI affinity

Behavior state shapes which POIs receive attention. The `POI_BEHAVIOR_AFFINITY` table applies a per-category multiplier to each POI's novelty score before selection. This makes the robot's gaze semantically coherent with its state — when listening, it locks onto people; when uncomfortable, it averts to objects.

| Behavior | Person | Pet | Object |
|----------|--------|-----|--------|
| attentive | 2.5× | 1.2× | 0.5× |
| listening | 3.0× | 0.5× | 0.3× |
| searching | 2.0× | 1.5× | 1.0× |
| uncomfortable | 0.3× | 1.0× | 2.0× |
| curious | 1.0× | 1.2× | 1.2× |
| idle | 1.0× | 1.0× | 1.0× |

States not listed use equal weights across all categories.

---

## Data flow

The robot operates in a 3D world (Three.js scene). Attention is directed at world objects — POIs — not at 2D gaze coordinates. The drive system selects a POI; the full-body tracking system (head yaw/pitch, body yaw, eyes) takes over from there.

```
External events
    │
    ▼
Rule engine  ──→  pressure[state] + look3D(x,y,z) actions
    │
    ▼
Pressure scoring  ──→  winning behavior state (with hysteresis)
    │
    ├──→  selectAttentionPOI()  ──→  POI_BEHAVIOR_AFFINITY × novelty weight → POI index
    │         │
    │         ▼
    │     trackWorldPoint(poi.position)  ──→  head/body/eye spring physics
    │
    ▼
setAttn() / setAffect()  ──→  Compositor
```

`look3D(x, y, z, category)` is the bridge between the rule engine and the 3D world: when a rule fires a `look` action (e.g., a face detected event carrying a world position), it finds the nearest POI of the given category, repositions it to those coordinates, and sets it as the current attention target. The full-body tracking system then takes over.

Micro-expressions bypass pressure scoring and go directly to `microExpress()` — they're reactive punctuation, not state changes.

---

## Relationship to the compositor

The drive system owns *intent*. The compositor owns *execution*. They're decoupled: the drive system never touches transition durations, easing curves, or blend state. It only calls `setAttn()`, `setAffect()`, and `microExpress()` — the same API available to a human operator or WebSocket client.

This means the drive system can be disabled entirely (manual/WebSocket control takes over) or overridden per-layer (operator locks affect to `listening` while drive system still manages attn). The compositor doesn't know or care who's calling it.

---

## Implementation order

1. **Pressure/scoring** — pressure vector, decay, hysteresis threshold, `update()` hook
2. **Drive layer** — default pressure profiles, baseline temperament params
3. **Rule engine** — event bus, rule definitions, pressure contributions
4. **Transition enforcer** — route table for illegal transitions
5. **Personal time** — per-POI familiarity + attention tracking, novelty-shaped idle
6. **Behavior → POI affinity** — `POI_BEHAVIOR_AFFINITY` table, `selectAttentionPOI()` integration
