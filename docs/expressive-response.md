# Expressive Response

The robot expresses its internal state through two mechanisms: a sustained **affect layer** that shapes ongoing expression, and brief **micro-expressions** that react to events without committing to a full state change.

---

## Affect layer

The affect layer is one half of the compositor. It controls expression parameters — lid openness, brow height and shape, mouth curvature, blink rate — and runs independently from the gaze layer. Any of the 15 behaviors can be used as the affect template, regardless of what the gaze layer is doing.

This independence is what makes the compositor interesting. The same behavior set that controls where and how the robot looks also controls how it appears to feel. `attentive` as an affect template produces wide-open eyes and a slow blink rate — focused, present. `processing` as an affect template produces a heavier lid, elevated blink rate, and slightly defocused expression — the face of someone thinking. Neither of those depends on the gaze pattern running simultaneously.

Some combinations are emotive (`gaze:idle` + `affect:pleased` = contentedly wandering). Some are functional (`gaze:listening` + `affect:processing` = absorbing something complicated). The layers don't need to agree, and the tension between them can itself be expressive.

Transitions between affect states follow the same blend system as the full compositor: each state defines its own enter duration and easing curve. `pleased` blooms in over 0.5s with an `outBack` overshoot. `uncomfortable` drags in over 0.7s with a slow `inOutCubic`. The character of the change is part of the expression.

---

## Micro-expressions

Micro-expressions are brief flashes of affect — 200–500ms — that surface, read, and return to the previous state without committing. They sit on top of the affect layer rather than replacing it.

A startled wince. A flicker of confusion. A brief pleasure response before settling back to neutral. The underlying affect state doesn't change; the micro-expression borrows the face for a moment.

Mechanically this uses the existing `maxHold` system: the affect layer snaps or blends quickly to the micro-expression state, holds for the specified duration, then returns automatically to whatever affect was active before. Because `interrupted` already demonstrates this pattern (snap in, hold 0.5s, return), micro-expressions are a natural extension — shorter holds, faster transitions, and a wider vocabulary of triggering states.

The value of micro-expressions is legibility. A robot whose face only changes when its full behavioral state changes looks slow and deliberate. One whose face briefly reacts to events — then settles — reads as present and responsive, even when its underlying state is stable.
