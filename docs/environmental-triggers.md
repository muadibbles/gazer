# Environmental Triggers

Environmental conditions are pressure sources for the drive system. They feed `emitDriveEvent()` or `addPressure()` directly, using the same rule engine as conversational events — no special architecture needed. The distinction is that environmental inputs are continuous and ambient rather than discrete and event-driven: they reflect the state of the world around the robot, not a specific interaction happening right now.

This document describes the categories, their drive mappings, and implementation notes for each.

---

## How they integrate

Every environmental source produces either:
- A **pressure contribution** — `addPressure('attentive', 0.4)` — a continuous push toward a state that decays naturally via novelty decay
- A **drive event** — `emitDriveEvent('person_entered', { distance: 1.2 })` — a named event the rule engine can respond to with pressure + optional micro-expression

Environmental inputs run as external processes (Python or Node.js) that observe sensors or system state and send WebSocket commands to the behavior engine. The engine doesn't need to know where the signal came from.

```
Sensor / source         →  input process     →  WebSocket command
Time of day             →  scheduler.py       →  { type: 'event', value: 'late_evening' }
PIR motion              →  presence.py        →  { type: 'event', value: 'motion_detected' }
Microphone amplitude    →  audio.py           →  { type: 'pressure', state: 'alert', amount: 0.3 }
```

---

## Presence & proximity

Who is in the room, how many, and how close.

| Condition | Drive event / pressure | Behavior |
|-----------|----------------------|----------|
| Person enters room | `person_entered` | `attentive` spike → look toward entry |
| Person leaves room | `person_left` | `searching` → eventually `idle` |
| Person very close (<0.5m) | `person_close` | `uncomfortable` pressure; slight gaze aversion |
| Person at comfortable distance (0.5–2m) | `person_present` | `attentive`/`engaged` |
| Person far away (>3m) | — | mild `curious`, wandering gaze |
| Multiple people | `crowd_detected` | `searching` or `confused`; gaze shifts between people |
| Room empty for extended time | `room_empty` | `sleepy` or `resting` pressure builds over time |
| Room empty → person returns | `person_entered` | `waking` → `attentive` (via transition enforcer) |

**Implementation:** PIR sensor for binary presence. Camera + depth (or stereo, or structured light) for count and distance. `emitDriveEvent('person_entered')` on rising edge; `emitDriveEvent('person_left')` on falling edge with debounce (~2s).

---

## Time & rhythm

The robot's internal clock shapes its baseline drive profile throughout the day.

| Time window | Drive profile adjustment | Feel |
|-------------|-------------------------|------|
| Early morning (6–9am) | `waking` baseline pressure, low speed | groggy, coming online |
| Morning (9am–12pm) | `attentive` / `curious` baseline | alert, engaged |
| Afternoon (12–5pm) | default profile | balanced |
| Late afternoon (5–7pm) | mild `sleepy` creep | slightly lower energy |
| Evening (7–10pm) | `idle` dominates | winding down |
| Late night (10pm–6am) | `resting` baseline pressure | nearly shut down |

Time-based changes should apply gradually — not a sudden shift at 10pm but a slow drift over 30–60 minutes as the time window changes. Implement as a scheduled process that adjusts `driveProfile` weights via `param` WebSocket messages, or as a continuous pressure contribution that varies with a sinusoidal day curve.

**Time since last interaction** also matters:
- < 5 minutes: `attentive` still elevated
- 5–30 minutes: gradual decay back to idle
- > 30 minutes: `curious` pressure builds (restless, looking for something to do)
- > 2 hours: `sleepy` pressure builds

**Implementation:** `scheduler.py` — reads system clock, computes current time window, sends `param` or `pressure` messages on a slow interval (every 60s). No sensor needed.

---

## Ambient environment

The physical quality of the space.

| Condition | Drive event / pressure | Behavior |
|-----------|----------------------|----------|
| Loud ambient noise | `loud_environment` | `uncomfortable` or `alert` pressure |
| Sudden loud sound | `startle` | `alert` micro-expression; `attentive` spike |
| Quiet room | — | lower blink rate, more `processing`/`resting` baseline |
| Bright lighting | — | `attentive` baseline slightly elevated |
| Dim lighting | — | `sleepy` pressure gradually builds |
| Motion detected (PIR, no face) | `motion_detected` | `searching` spike; look toward motion |
| No motion for extended period | `room_still` | `resting`/`sleepy` pressure builds |

**Ambient sound** is the richest input. A microphone running continuously can distinguish:
- Amplitude envelope → arousal level (loud = alert/uncomfortable, quiet = processing/resting)
- Sudden transients → startle events
- Sustained speech with no face detected → `curious` (someone talking nearby but not to the robot)

**Implementation:** `audio.py` with PyAudio — sliding window RMS for amplitude, threshold detection for transients. Light level from a simple photoresistor or camera exposure value. PIR for motion.

---

## System state

The robot's own internal condition as an environmental signal.

| Condition | Drive event / pressure | Behavior |
|-----------|----------------------|----------|
| CPU load high | `processing_heavy` | `processing` affect; slower saccades |
| Network connected | `online` | mild `attentive` boost |
| Network lost | `offline` | `confused` micro-expression; `uncomfortable` pressure |
| Low battery | `low_power` | `sleepy` / `resting` pressure builds gradually |
| Critical battery | `critical_power` | `resting` override |
| Boot / startup | `startup` | `waking` state, then normal drive |
| Error / exception | `error` | `uncomfortable` pressure; `confused` micro-expression |
| Successful task | `success` | `pleased` micro-expression |

**Implementation:** system metrics available from `/proc/stat`, `psutil`, or `subprocess`. Battery from `/sys/class/power_supply/`. Network from socket connectivity check. These run as a slow polling loop (every 5–30s) — system state changes slowly.

---

## Calendar & schedule

Higher-level context that frames what the robot is doing.

| Context | Effect |
|---------|--------|
| Meeting in progress | `listening`/`waiting` affect baseline; reduced saccade range |
| Focus / do-not-disturb | `processing` affect; near-zero environmental response |
| Presentation mode | `attentive` + `speaking` loop; heightened engagement |
| Idle / unstructured time | full drive system autonomy; personal time active |
| End of day | gradual `sleepy` → `resting` transition |

Calendar context is coarse-grained and changes infrequently. It's best modeled as a **context modifier** that adjusts `driveProfile` weights rather than injecting events — a meeting doesn't make the robot suddenly switch states, it shifts the baseline so the robot naturally settles into meeting-appropriate behavior.

**Implementation:** calendar webhook, iCal polling, or a simple manual context setter in the operator console. Sends `param` messages to shift drive profile weights.

---

## Implementation order

1. **Time of day** — no sensor needed; highest value for low effort; immediately gives the robot a day/night rhythm
2. **Presence (PIR)** — single sensor; binary presence is enough to trigger waking/sleeping cycles
3. **Ambient audio** — microphone is likely already needed for speech pipeline; amplitude envelope is cheap to compute alongside speech detection
4. **System state** — zero hardware cost; makes the robot feel self-aware
5. **Camera presence/proximity** — depends on face tracking being implemented; builds on that work
6. **Calendar / schedule** — highest integration cost; lowest autonomy value; most useful when the robot is deployed in a specific context

---

## Relationship to drive system

Environmental triggers don't replace the drive system's internal dynamics — they add to them. The robot still has novelty decay, baseline temperament, and the idle/curious oscillation running underneath. Environmental inputs push pressure values up or down, which shifts what state the drive system settles into. Remove all external inputs and the robot falls back to its own drive profile, wandering on its own schedule.

This is the right layering: environment shapes drive, drive shapes compositor, compositor shapes expression. At no layer does environment reach directly into expression — the robot's personality mediates everything.
