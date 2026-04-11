# World Model

The robot lives in a 3D scene (Three.js). The world model is the layer that bridges the abstract drive system (pressure, behavior states) and the physical world — where things actually are in space.

The drive system decides what the robot wants to pay attention to. The world model answers: *where is that thing, and what does the robot's body need to do to look at it?*

---

## POIs (Points of Interest)

The scene is pre-seeded with a named set of 3D markers. Each POI represents something the robot might want to look at.

**Current set:** Person, Child, Cat, Dog, TV, Window, Food Bowl, Front Door

**Per-POI fields:**

| Field | Type | Description |
|-------|------|-------------|
| `position` | `{ x, y, z }` | 3D world coordinates |
| `category` | string | `person`, `pet`, or `object` |
| `salience` | float | base weight in POI selection |
| `familiarity` | 0→1 | decays when not attended; drives novelty selection |
| `attention` | seconds | cumulative dwell time; never decays |

**Categories and colors:**
- `person` — orange, highest base salience
- `pet` — green
- `object` — blue/purple

**Persistence:** POI positions can be dragged in the scene to match the real room layout. Positions persist via `localStorage` so the layout survives page reloads.

---

## Full-body attention

When the drive system selects a POI, `trackWorldPoint(poi.position)` engages the full-body tracking system. Attention is distributed across head, body, and eyes via spring physics — the same system that handles manual ball drag.

| Actuator | Contribution | Notes |
|----------|-------------|-------|
| Head yaw | covers ~75% of horizontal angle | springs toward target |
| Head pitch | covers ~75% of vertical angle | springs toward target |
| Eyes | cover the residual ~25% | faster response, smaller range |
| Body yaw | kicks in when head exceeds ~60% of its range | slow spring, large range |

The result: the robot turns its whole body toward what it's interested in, not just its eyes. A POI directly ahead requires only eyes; a POI far to the side involves head and body.

All springs share the same damping/stiffness parameters as the rest of the animation system, so full-body tracking feels continuous with manual and drive-initiated motion.

---

## Personal time in 3D

Personal time is tracked per POI, not as a 2D gaze grid.

**`familiarity`** accumulates while the robot dwells on a POI and decays when it doesn't. High familiarity suppresses that POI in novelty-weighted selection — the robot is less likely to look at something it just looked at. Low familiarity (a POI long unvisited or newly repositioned) increases selection weight.

**`attention`** is cumulative dwell time in seconds and never decays. It answers "what has this robot been most interested in during this session?" Visualized in the scene as marker size (larger = more cumulative attention) and a fill bar in the POI label.

Together they give the robot a lightweight spatial memory: a sense of having been somewhere before, and curiosity about what it hasn't seen recently.

---

## Behavior → POI affinity

Different behavior states prefer different POI categories. `selectAttentionPOI()` applies the `POI_BEHAVIOR_AFFINITY` table as a multiplier on each POI's novelty score before selection. This makes gaze semantically coherent with state.

| Behavior | Person | Pet | Object |
|----------|--------|-----|--------|
| attentive | 2.5× | 1.2× | 0.5× |
| listening | 3.0× | 0.5× | 0.3× |
| searching | 2.0× | 1.5× | 1.0× |
| uncomfortable | 0.3× | 1.0× | 2.0× |
| curious | 1.0× | 1.2× | 1.2× |
| idle | 1.0× | 1.0× | 1.0× |

States not listed use equal weights. A robot in `listening` state will almost always look at people; a robot in `uncomfortable` will avert to objects and furniture.

---

## The `look3D(x, y, z, category)` action

Called by the rule engine when an event includes a world position. Steps:

1. Find the nearest POI of the given `category` to `(x, y, z)`.
2. Reposition it to `(x, y, z)`.
3. Set it as the current attention target — `trackWorldPoint` takes over immediately.

This means external events (face detected, motion detected) directly update the world model. The person POI moves to where the face actually is; the robot looks there.

**Fallback:** when no 3D scene is active, `look3D` calls `triggerSaccade` using projected 2D coordinates. The drive system still works in 2D environments.

---

## Manual override

The yellow ball is a highest-priority manual override. While the ball is being dragged — and for `ballTrackTimeout` seconds after drag ends — the full-body tracking system follows the ball instead of any POI. Autonomous POI attention is suspended.

Once the timeout expires, POI selection resumes normally. The ball's final position does not update any POI.

---

## Relationship to drive system

```
Drive system (pressure / behavior state)
    └──→ selectAttentionPOI() applies POI_BEHAVIOR_AFFINITY × novelty weight
         └──→ picks a POI index
              └──→ preUpdate() calls trackWorldPoint(poi.position)
                   └──→ head / body / eye spring physics
```

The drive system never writes directly to joint angles or eye targets. It selects a POI; the world model resolves the geometry; the spring physics produce the motion. Each layer owns exactly one concern.
