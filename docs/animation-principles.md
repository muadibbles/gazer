# 12 Principles of Animation

From Johnston & Thomas, *The Illusion of Life* (Disney, 1981). Gazer uses these as a design checklist — the goal is to apply as many as possible to a robot that has no narrative, no character arc, and no animator: just physics, timing, and behavioral state.

| # | Principle | Description | Status |
|---|-----------|-------------|--------|
| 1 | **Squash & stretch** | Deformation conveys weight and flexibility | ✅ eye deforms during saccades; easing on entry/exit of each state |
| 2 | **Anticipation** | Wind-up before action signals what's coming | ✅ brief counter-move before saccade fires |
| 3 | **Staging** | Clear composition, one idea at a time | n/a — single subject |
| 4 | **Straight ahead vs pose-to-pose** | Two approaches to planning movement | n/a |
| 5 | **Follow-through & overlapping action** | Parts settle independently after movement stops | ✅ overshoot spring on saccades; head/body spring overshoot; pupils → face → head → body cascade at different rates |
| 6 | **Slow in and slow out** | Ease in/out — most motion happens in the middle | ✅ easing library on saccades; head/body spring physics eases in *and* out; per-state `enterEase` shapes every compositor transition |
| 7 | **Arcs** | Natural motion follows curved paths, not straight lines | ✅ quadratic bezier saccades; head tilts into yaw turns + body leans into rotation — 3D motion traces curves, not flat angles |
| 8 | **Secondary action** | Supporting motions that reinforce the primary one | ✅ face/head/body cascade; brow and mouth react to blink |
| 9 | **Timing** | Number of frames determines weight and mood | ✅ per-behavior speed, pause, and blink timing; per-state `enterDur` |
| 10 | **Exaggeration** | Push beyond realism to read as more real | 🔨 behavior states push values — room to go further |
| 11 | **Solid drawing** | Volume, weight, balance (the 3D-thinking principle) | ✅ three.js robot body with physical presence |
| 12 | **Appeal** | Charisma — the thing that makes you want to watch | the whole project |

---

## Areas with room to grow

**Exaggeration (#10)** — states could push harder at extremes. `interrupted` and `alert` could squash the eye harder and spike velocity further on entry. The current implementation is tasteful; the principle calls for going further than feels comfortable, then pulling back slightly.

**Overlap (#5)** — lids, brows, and mouth currently settle together after a behavior change. Each should settle at a different rate, the way a physical face has parts with different mass and tension. A brow should still be moving when the lid has already landed.

**Anticipation (#2)** — currently only applied to saccades (counter-move before the eye jumps). Head and body turns don't have anticipation. A large head rotation could wind up slightly in the opposite direction before committing — especially for dramatic turns from `alert` or `interrupted`.
