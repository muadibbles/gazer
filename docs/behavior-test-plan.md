# Behavior Test Plan

How to elicit each of the 17 behaviors. For each one: what drives it, how to trigger it, and what to look for.

Use `python3 server.py` + `open index.html` + `python3 simulate.py` as the baseline setup. All `send.py` commands assume the relay is running.

---

## Quick reference — all 17 behaviors

| # | Behavior | Group | Best trigger |
|---|---|---|---|
| 1 | `idle` | Classic | Drive baseline; stop all events |
| 2 | `attentive` | Attention | Manual set or task assigned |
| 3 | `curious` | Attention | face_detected, novel POI |
| 4 | `sleepy` | Classic | time_scheduler night; manual |
| 5 | `alert` | Attention | startle, arrival |
| 6 | `searching` | Attention | face_lost after face_detected |
| 7 | `listening` | Conversational | speech_start |
| 8 | `processing` | Conversational | After speech_end |
| 9 | `speaking` | Conversational | Manual or task with speech |
| 10 | `waiting` | Conversational | Task assigned, awaiting response |
| 11 | `engaged` | Conversational | During social task |
| 12 | `confused` | Affective | Manual micro / rule |
| 13 | `pleased` | Affective | Familiar POI interaction |
| 14 | `uncomfortable` | Affective | Manual or startle follow-up |
| 15 | `waking` | Operational | After resting; transition enforcer |
| 16 | `resting` | Operational | Sleepy pressure + time |
| 17 | `interrupted` | Operational | Any startle while active |

---

## Per-behavior detail

---

### 1. `idle`
**What it is:** The default resting gaze. Slow, wide saccades. Moderate blink rate. Robot stands and looks around nearby POIs.

**How to trigger:**
- Just wait — `idle` has the highest baseline pressure (0.40) and the robot returns here naturally
- Disable the simulator: `Ctrl-C` on simulate.py, wait 30–60 s
- Manual: `python3 send.py behavior idle`

**What to watch:**
- Slow, casual eye movements covering a wide arc
- Relaxed lids, neutral brows
- Robot stands still or turns its head slowly between nearby POIs

---

### 2. `attentive`
**What it is:** Focused gaze locked onto a specific target. Tight saccade radius. Slightly raised brows, open lids.

**How to trigger:**
- `python3 send.py behavior attentive`
- Assign a task: `python3 states.py` → `task person person greeting`
- Via drive: spike curious, then it sometimes steps up to attentive when a task is active

**What to watch:**
- Eyes barely move — very small saccade radius
- Head and body track a specific POI tightly
- Lids slightly wider than idle

---

### 3. `curious`
**What it is:** Active searching gaze, medium-wide radius. Robot wanders toward novel POIs.

**How to trigger:**
- `python3 simulate.py` — face_detected events push curious pressure
- `python3 send.py event face_detected x=-1.2 y=1.5 z=3.0`
- `python3 send.py pressure curious 0.8`
- Enable only Person and Child POIs in the Scene panel — robot will wander between them

**What to watch:**
- Eyes move with moderate speed and range
- Robot starts wandering toward the Person POI
- Micro-expression of `pleased` or `curious` fires on face arrival

---

### 4. `sleepy`
**What it is:** Very slow, heavy-lidded. Eyes droop. Minimal saccades. Robot stays put.

**How to trigger:**
- Run `time_scheduler.py` after 9 pm (or adjust system clock)
- `python3 send.py pressure sleepy 0.9`
- `python3 send.py behavior sleepy`

**What to watch:**
- Heavy lid openness (lids drop)
- Very slow, long pauses between saccades
- Robot does not wander
- Slow blink rate; occasional half-blink

---

### 5. `alert`
**What it is:** Wide eyes, fast small saccades. Robot freezes movement and scans rapidly.

**How to trigger:**
- `python3 send.py event startle scale=1.5`
- `python3 send.py event arrival`
- `python3 send.py pressure alert 0.9`
- Clap loudly near microphone if `audio.py` is running

**What to watch:**
- Eyes snap open wide immediately
- Rapid small eye movements — scanning
- Head snaps toward the event source
- Micro: startle expression (brows up, wince)

---

### 6. `searching`
**What it is:** Active scanning with large saccade range. Robot sweeps head back and forth looking for something.

**How to trigger:**
- `python3 send.py event face_lost` (after face_detected was fired)
- `python3 send.py behavior searching`
- Disable all person POIs in the Scene panel while curious — robot enters searching

**What to watch:**
- Wide, sweeping eye movements
- Head turns noticeably
- More head motion than curious — actively looking

---

### 7. `listening`
**What it is:** Tight gaze locked on speaker. Slow blink rate. Raised brows, open lids.

**How to trigger:**
- `python3 send.py event speech_start`
- `python3 audio.py` — speak near microphone
- `python3 states.py` → `speak` command

**What to watch:**
- Saccade radius shrinks — eyes stay near center
- Blink rate slows noticeably
- Slightly raised brows ("I'm paying attention")
- Head angles toward Person POI

---

### 8. `processing`
**What it is:** Eyes drift inward and defocus slightly. Robot "thinking" after speech ends.

**How to trigger:**
- `python3 send.py event speech_end` (after speech_start)
- `python3 states.py` → `speak 0.5 3` then wait

**What to watch:**
- Eyes drift to a neutral position rather than tracking a POI
- Slightly slower movement
- Brows lower slightly — internal focus
- Lasts only a few seconds before drive moves on

---

### 9. `speaking`
**What it is:** Mouth opens and closes driven by amplitude. Open lids, engaged expression.

**How to trigger:**
- `python3 states.py` → `speak 0.7 4` (70% amplitude for 4 seconds)
- `python3 send.py param amplitude 0.8` then `python3 send.py param amplitude 0`
- Run `audio.py` and play audio near the mic

**What to watch:**
- Mouth visibly opens with speech amplitude
- Open, engaged expression
- Mouth shape changes with amplitude — louder = wider

---

### 10. `waiting`
**What it is:** Patient gaze. Slower saccades, soft expression. Robot holds position waiting for response.

**How to trigger:**
- `python3 send.py behavior waiting`
- Assign a social task and let it reach the wait phase: `python3 states.py` → `scenario person_social`

**What to watch:**
- Eyes scan slowly at medium range
- Relaxed but open expression
- Robot is still — not wandering

---

### 11. `engaged`
**What it is:** Close, warm attention on a specific POI. Tight gaze, slightly pleased expression.

**How to trigger:**
- `python3 send.py behavior engaged`
- `python3 send.py event face_detected x=-1.2 y=1.5 z=3.0` then `python3 send.py event speech_start`
- Run `scenario arrival_and_greet` in states.py

**What to watch:**
- Eyes locked on Person POI
- Slightly softer expression than attentive
- Less head movement — settled and attending

---

### 12. `confused`
**What it is:** Brows furrow, eyes narrow slightly. Hesitant saccades.

**How to trigger:**
- `python3 send.py micro confused 0.5`
- `python3 send.py behavior confused`
- `python3 states.py` → `scenario person_social` — confused fires mid-conversation

**What to watch:**
- One or both brows tilt inward/down
- Slightly narrowed lids
- Short micro version: snaps in and returns to base after ~0.5 s
- Full behavior version: sustained for the duration

---

### 13. `pleased`
**What it is:** Soft lids, raised cheeks/brows, warm expression. Robot looks content.

**How to trigger:**
- `python3 send.py micro pleased 0.4`
- `python3 send.py behavior pleased`
- Fires automatically via `microAuto` when the robot visits a familiar POI (familiarity > 0.5)
- Run `simulate.py` for a few minutes — robot learns the Person POI and shows pleased on each visit

**What to watch:**
- Lids soften (not drooping, just relaxed)
- Brows raise slightly
- Mouth curves upward if mouth is enabled
- Warm, inviting look

---

### 14. `uncomfortable`
**What it is:** Slight wince. Lids tighten, brows furrow. Avoidant gaze.

**How to trigger:**
- `python3 send.py micro uncomfortable 0.4`
- `python3 send.py behavior uncomfortable`
- Chain after startle: `python3 send.py event startle` then `python3 send.py behavior uncomfortable`

**What to watch:**
- Tighter lids (squint-like)
- Brows pulled inward
- Gaze radius shrinks — avoidant
- Distinct from confused: more aversive, less puzzled

---

### 15. `waking`
**What it is:** Transition state. Eyes flutter open from resting. Brief, then moves to idle.

**How to trigger:**
- Set to resting first, then inject any pressure: `python3 send.py behavior resting` → wait → `python3 send.py pressure curious 0.6`
- The transition enforcer forces `resting → waking → idle` — you cannot skip it

**What to watch:**
- Eyes open gradually from heavy-lidded resting state
- Brief state — transitions to idle within a second or two
- Head starts to lift

---

### 16. `resting`
**What it is:** Eyes mostly closed. Very slow breathing-like blink rhythm. Robot stays still.

**How to trigger:**
- `python3 send.py behavior resting`
- `python3 send.py pressure sleepy 0.9` then wait — drive will push into resting
- Enable only the Charger POI, let battery drain — robot docks and rests

**What to watch:**
- Lids nearly closed
- Very slow, deliberate blinks
- No saccades — eyes stay centered
- Robot does not wander

---

### 17. `interrupted`
**What it is:** Snaps to a brief wide-eyed alert then auto-returns after 0.5 s.

**How to trigger:**
- `python3 send.py event startle`
- `python3 send.py behavior interrupted` (manual)
- Clap near microphone with `audio.py` running

**What to watch:**
- Instantaneous snap — no blend-in
- Wide eyes, raised brows for exactly 0.5 s
- Returns automatically to whatever state was active before
- Progress bar appears gold and drains in 0.5 s

---

## Scenario shortcuts (states.py)

```bash
python3 states.py scenario dog_hungry        # dog_begging → curious → task
python3 states.py scenario dog_play          # dog_play_request → playful task
python3 states.py scenario cat_hello         # cat_greeting → pleased micro
python3 states.py scenario person_utility    # utility task: attentive → engaged → waiting
python3 states.py scenario person_social     # social task: engaged → listening → confused → pleased
python3 states.py scenario kid_play          # play task: curious → playful
python3 states.py scenario startle_recovery  # startle → alert → searching → idle
python3 states.py scenario arrival_and_greet # arrival → alert → attentive → engaged
python3 states.py scenario low_power         # battery drops → returning → resting
python3 states.py scenario speaking_test     # amplitude sweep for mouth testing
```

---

## Tips

- **Pin a layer** to isolate gaze from expression: use "GAZE PINNED" or "EXPR PINNED" buttons in the Drive accordion so you can test one layer without the other moving.
- **Use the Scene panel** to disable most POIs so the robot focuses on a specific one — makes it much easier to observe one behavior cleanly.
- **Slow down the drive**: raise the Hysteresis slider and lower Novelty Decay so behaviors hold longer and you have time to observe them.
- **Watch the Live State widget**: it shows current `attn` and `affect` so you know which layer is active.
