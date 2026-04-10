# Behaviors

All 15 behaviors are available to both compositor layers independently. The `attn` layer uses a behavior's gaze parameters (range, speed, easing). The `affect` layer uses its expression parameters (lids, brows, mouth, blink rate). Any combination is valid.

---

## Classic

| Behavior    | Gaze Range           | Speed  | Blink Rate    | Feel                 | Enter  |
|-------------|----------------------|--------|---------------|----------------------|--------|
| `idle`      | moderate             | normal | normal        | relaxed, wandering   | 0.40s  |
| `attentive` | tight (center focus) | fast   | slow          | alert, tracking      | 0.20s  |
| `curious`   | wide                 | medium | slightly slow | scanning, exploring  | 0.32s  |
| `sleepy`    | small                | slow   | very high     | heavy-lidded, drowsy | 0.90s  |

## Attention

| Behavior    | Gaze Range | Speed       | Blink Rate | Feel                          | Enter  |
|-------------|------------|-------------|------------|-------------------------------|--------|
| `alert`     | very tight | very fast   | very slow  | snapped to source, wide-eyed  | 0.06s  |
| `searching` | very wide  | medium-fast | moderate   | scanning, seeking             | 0.28s  |

## Conversational

| Behavior     | Gaze Range | Speed  | Blink Rate    | Feel                          | Enter  |
|--------------|------------|--------|---------------|-------------------------------|--------|
| `listening`  | tight      | slow   | slow          | receptive, focused on speaker | 0.40s  |
| `processing` | medium     | slow   | high          | inward, defocused, thinking   | 0.55s  |
| `speaking`   | medium     | normal | normal        | natural, expressive           | 0.28s  |
| `waiting`    | medium     | slow   | slightly high | patient, expectant            | 0.45s  |

## Affective

| Behavior        | Gaze Range | Speed  | Blink Rate | Feel                      | Enter  |
|-----------------|------------|--------|------------|---------------------------|--------|
| `engaged`       | tight      | fast   | very slow  | bright, leaning in        | 0.25s  |
| `confused`      | medium     | medium | moderate   | erratic, furrowed         | 0.35s  |
| `pleased`       | medium     | normal | high       | squinting smile, happy    | 0.50s  |
| `uncomfortable` | wide       | medium | high       | averted gaze, nervous     | 0.70s  |

## Operational

| Behavior      | Gaze Range | Speed      | Blink Rate | Feel                       | Enter   |
|---------------|------------|------------|------------|----------------------------|---------|
| `waking`      | very tight | sluggish   | very high  | groggy, coming online      | 1.20s   |
| `resting`     | tiny       | very slow  | very high  | nearly shut down           | 1.50s   |
| `interrupted` | snap       | very fast  | very low   | startle, instant redirect  | 0.00s ⚡ |

`interrupted` auto-returns to the previous state after 0.5s (`maxHold`).

---

## Pair-specific transition overrides

Some state pairs have a custom blend duration that overrides both the destination state's `enterDur` and the global `transitionDur` default. These are designed to give specific transitions a distinct character.

| Pair | Duration | Feel |
|------|----------|------|
| `pleased → uncomfortable` | 0.90s | reluctant, slow shift |
| `uncomfortable → pleased` | 0.55s | cautious brightening |
| `resting → interrupted` | 0.08s | groggy startle |
| `waking → interrupted` | 0.08s | still-groggy startle |
| `resting → alert` | 0.25s | slow state takes a breath first |
| `resting → attentive` | 0.35s | slow rise to attention |

---

## Using behaviors as compositor templates

Each behavior defines two groups of parameters:

**Gaze parameters** (used by the `attn` layer):
- `gazeRadius` — how far from center the saccade targets land
- `speedMult` — multiplier on base saccade speed
- `easeFn` — easing curve for the arc motion

**Expression parameters** (used by the `affect` layer):
- `lidOpenness` — how open the eye is
- `browHeight`, `browAngle` — brow position and tilt
- `mouthCurve` — smile/frown amount
- `blinkMult` — multiplier on base blink interval

When you set `attn:alert` + `affect:processing`, the robot looks alert (tight fast gaze, wide eyes from `alert`'s gaze params) while appearing to think (heavy lid, elevated blink from `processing`'s expression params). The layers blend independently and transition independently.
