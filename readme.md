# gazer 👁️

A browser-based robot eye animation and behavior system. Smooth arc-based gaze movement built as a proof of concept, designed to eventually run on embedded hardware (Raspberry Pi, Jetson, etc).

-----

## What it does

- **Smooth arc saccades** — eye movement follows quadratic bezier curves, not linear paths, so it feels alive
- **Behavior controller** — pluggable behavior states that govern gaze range, speed, blink rate, and easing
- **Easing library** — `inOutCubic`, `outBack`, `outQuart`, `inOutQuint` built in, easy to extend
- **Blink system** — natural blink timing per behavior
- **Click to look** — click anywhere on canvas to trigger a manual saccade

-----

## Behaviors

|Behavior   |Gaze Range          |Speed |Blink Rate   |Feel                |
|-----------|--------------------|------|-------------|--------------------|
|`idle`     |moderate            |normal|normal       |relaxed, wandering  |
|`attentive`|tight (center focus)|fast  |slow         |alert, tracking     |
|`curious`  |wide                |medium|slightly slow|scanning, exploring |
|`sleepy`   |small               |slow  |very high    |heavy-lidded, drowsy|

-----

## Parameters

All exposed in the UI panel:

|Param          |Description                                           |
|---------------|------------------------------------------------------|
|`arcCurvature` |How much the gaze arc bends (0 = straight line)       |
|`gazeSpeed`    |Base speed multiplier for all saccades                |
|`saccadeJitter`|Adds slight randomness to target positions            |
|`lidOpenness`  |How wide the eye opens (overridden by sleepy behavior)|
|`pupilSize`    |Pupil radius relative to iris                         |
|`blinkInterval`|Seconds between blinks (modified by behavior)         |

-----

## Architecture

```
BehaviorController
├── behaviors/
│   ├── idle
│   ├── attentive
│   ├── curious
│   └── sleepy
├── GazeSaccade (bezier arc engine)
├── BlinkController
└── EyeRenderer (canvas)
```

The behavior controller is designed for expansion — each behavior is just a config object. Future behaviors can be driven by speech state, face detection, or inference output.

-----

## Roadmap

- [ ] Multiple eyes (stereo)
- [ ] Emotion layer (surprise, disgust, joy)
- [ ] WebSocket API for external behavior triggers
- [ ] Raspberry Pi output layer (OLED / servo)
- [ ] Integration with local LLM inference state

-----

## Running locally

Just open `index.html` in a browser. No build step needed.

```bash
open index.html
# or
python3 -m http.server 8080
```

-----

## License

MIT
