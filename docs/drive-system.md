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
event: speech_start         → pressure[speaking]   += 0.8
event: speech_end           → pressure[speaking]   -= 0.8; pressure[listening] += 0.3
event: face_detected(x, y)  → pressure[attentive]  += 0.6; look(x, y)
event: face_lost            → pressure[searching]  += 0.4
event: long_silence         → pressure[waiting]    += 0.2 * t
event: loud_sound           → microExpress('alert', 0.15)
event: error_state          → pressure[uncomfortable] += 0.5
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
- **Default pressure profile** — each state has a resting pressure that defines the robot's baseline temperament. A robot with high resting `curious` pressure will wander and scan. One with high resting `attentive` pressure will stay focused on center.
- **Time-of-session effects** — pressure profiles can shift over a session. Early: higher `attentive`. Late: higher `sleepy`.
- **Personal time** — see below.

The drive layer produces a baseline pressure vector that stimulus rules add to. In the absence of all stimulus, the baseline wins and the robot expresses its own character.

---

### 5. Personal time and memory

When the robot is not responding to an external target, it explores autonomously — and remembers where it has looked, how long, and how often. These memories accumulate over a session and shape where the drive layer directs attention during idle.

A location looked at often becomes familiar; the robot is less likely to fixate there again (novelty decay in spatial form). A location rarely visited becomes interesting. Over time the robot develops spatial preferences that are unique to its session history.

This gives the robot a sense of having been somewhere before — an accumulated experience that shapes present behavior. It's the lightest possible form of memory, but it makes the robot feel continuous rather than stateless.

---

## Data flow

```
External events
    │
    ▼
Rule engine  ──→  pressure[state] for each behavior
    │
    ▼
Pressure scoring  ──→  winning state (with hysteresis)
    │
    ▼
Transition enforcer  ──→  legal transition sequence
    │
    ▼
setAttn() / setAffect()  ──→  Compositor
```

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
5. **Personal time** — spatial memory, dwell accumulation, novelty-shaped idle
