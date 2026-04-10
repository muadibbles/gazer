# Intro to Animating for Robots

## Why Robot Animation is Different

Animating for robots is not the same as animating for film or games. In film, you control the camera, the lighting, the edit. In games, you have a full rendering pipeline and can lean on physics engines. On a robot, you're animating for a physical object that exists in someone's space, reacting in real time, with no cuts and no retakes.

This changes everything about how you think about movement.

## The Uncanny Valley of Motion

Most people know the uncanny valley as a visual phenomenon -- a face that's almost human but not quite. Motion has its own uncanny valley. A robot eye that snaps instantly from point A to point B reads as mechanical. One that moves in a perfectly smooth line reads as robotic in a different way -- too precise, too clean. Real eyes don't work like either of those.

Human eyes move in **saccades**: fast, ballistic arcs between fixation points. They overshoot slightly, settle, then hold. The path curves. The speed varies. Blinks cluster around transitions. All of this happens below conscious awareness, but people absolutely notice when it's wrong.

## Arcs, Not Lines

The single most important principle borrowed from traditional animation is **arcs**. Almost nothing in organic motion travels in a straight line. Joints rotate, muscles pull at angles, momentum carries things along curves.

In Gazer, every eye movement follows a quadratic bezier curve. A control point is generated perpendicular to the straight-line path between the current gaze position and the target. This creates a subtle arc that makes the movement feel alive. The amount of curvature is tunable -- too little and it looks linear, too much and it looks drunk.

```
Start ----*---- End       <- linear (mechanical)

Start ---,     ,--- End   <- arc (organic)
          '---'
           ctrl
```

## Easing and Timing

The second key principle is **easing**. Constant-speed movement (linear interpolation) looks robotic. Real motion accelerates and decelerates. Different emotional states have different timing signatures:

- **Alert/attentive**: fast snap with quick settle (inOutQuint). The eye arrives almost instantly and locks on.
- **Relaxed/idle**: smooth acceleration and deceleration (inOutCubic). The eye drifts naturally between points.
- **Curious/searching**: overshoot easing (outBack). The eye goes slightly past the target then pulls back, like it's scanning.
- **Sleepy/drowsy**: slow deceleration (outQuart). Movement tapers off gradually, like the eye is heavy.

Choosing the right easing function for each behavioral state is what gives the eye its personality.

## Blinks Are Not Optional

Blinking is one of the strongest signals that something is alive. A robot eye that doesn't blink will always feel off, even if the gaze movement is perfect.

But blink timing matters just as much as the blinks themselves:

- Relaxed states blink at a natural rate (every 3-4 seconds)
- Attentive states suppress blinking (you blink less when concentrating)
- Sleepy states blink frequently, with slower lid movement
- Blinks should cluster around gaze transitions, not fire on a rigid timer

The blink itself has asymmetric timing: closing is faster than opening. In Gazer, the close phase takes about 70ms and the open phase about 120ms. This matches real human blink dynamics.

## Behavioral States vs. Keyframe Animation

Traditional animation uses keyframes: an animator poses the character at specific moments, and the software interpolates between them. This works for linear, scripted content but breaks down for a robot that needs to react to unpredictable input in real time.

Gazer uses a **behavioral state model** instead. Rather than scripting specific movements, you define a set of parameters that govern *how* the eye moves:

- How far does it look? (gaze radius)
- How fast does it move? (speed multiplier)
- How often does it blink? (blink multiplier)
- What does the movement feel like? (easing function)
- How open are the lids? (lid openness)

The actual movements are generated procedurally within these constraints. The result is animation that feels hand-crafted but is entirely reactive and never repeats.

## Designing for Peripheral Perception

One thing that separates robot animation from screen animation: people often perceive robots in their peripheral vision. A robot sitting on a desk or shelf is mostly seen out of the corner of someone's eye. This means:

- **Broad movements read better than subtle ones.** A small pupil twitch that looks great on a monitor may be invisible on a robot across the room.
- **Timing matters more than detail.** People pick up on rhythm and tempo peripherally even when they can't see detail.
- **Stillness is a state, not a failure.** A robot that's always moving is exhausting. Periods of quiet stillness, punctuated by the occasional blink, make the moments of movement more meaningful.

## From Screen to Hardware

Gazer currently runs in a browser as a proof of concept. Moving to hardware introduces new constraints:

- **Display limitations**: small OLEDs and LED matrices have low resolution, so eye designs need to be bold and simple
- **Frame rate**: embedded hardware may not hit 60fps, so animations need to degrade gracefully
- **Input latency**: sensor data (face tracking, audio levels) arrives with delay, so the behavior system needs to smooth over gaps
- **Power**: continuous animation drains batteries, so idle states should be genuinely low-cost

The behavioral state model maps well to these constraints. The same behavior configs that drive the browser prototype can drive a Pi with an OLED, just with a different renderer swapped in.

## Summary

The core ideas for making robot animation feel alive:

1. **Arcs over lines** -- use curved paths for all movement
2. **Ease everything** -- never use linear interpolation for organic motion
3. **Blink naturally** -- vary timing by behavioral state
4. **Think in behaviors, not keyframes** -- define how the system moves, not what it does
5. **Design for peripheral vision** -- bold timing, comfortable stillness
6. **Separate behavior from rendering** -- the same animation logic should work across display hardware
