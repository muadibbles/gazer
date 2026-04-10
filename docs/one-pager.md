# Gazer: One-Pager

## What is Gazer?

Gazer is a browser-based robot eye animation and behavior system. It renders a single expressive eye on an HTML canvas and drives it with a pluggable behavior engine that controls gaze direction, blink timing, eyelid openness, and movement style. The project is a proof of concept designed to eventually run on embedded hardware like Raspberry Pi or Jetson boards.

## The Problem

Robot eyes that move linearly between points look mechanical and lifeless. Real eyes move in arcs, with variable speed and subtle overshoot. Building convincing eye animation typically requires heavy tooling (game engines, 3D rigs) that doesn't translate well to small embedded displays.

## The Approach

Gazer uses **quadratic bezier curves** to generate arc-shaped saccades instead of straight-line interpolation. A perpendicular control point is computed for each eye movement, creating natural-looking curved trajectories. Four built-in easing functions (inOutCubic, outBack, outQuart, inOutQuint) shape the timing of each movement to match the current behavioral state.

## Behavior System

A lightweight behavior controller governs the eye's personality. Each behavior is a simple config object that defines gaze range, movement speed, blink rate, and easing style:

- **Idle** -- relaxed wandering with moderate range and smooth easing
- **Attentive** -- tight center focus, fast snapping movements, slow blinks
- **Curious** -- wide scanning range with overshoot easing
- **Sleepy** -- small movements, slow speed, heavy blinking, half-closed lids

Behaviors are designed to be swappable at runtime and extensible. Future behaviors can be driven by external signals like speech state, face detection, or LLM inference output.

## Key Parameters

All animation parameters are exposed in a live UI panel: arc curvature, gaze speed, saccade jitter, lid openness, pupil size, and blink interval. This makes it easy to tune the eye's feel in real time without touching code.

## Architecture

The system is a single `index.html` file with no build step or dependencies. It runs entirely in the browser using the Canvas 2D API. The internal structure is modular:

- **BehaviorController** -- selects and applies behavior configs
- **GazeSaccade** -- bezier arc engine for eye movement
- **BlinkController** -- manages natural blink timing and lid animation
- **EyeRenderer** -- draws the eye (sclera, iris, pupil, catchlights, lid shadows)

## Roadmap

- Stereo eye support (two eyes moving together)
- Emotion layer (surprise, disgust, joy)
- WebSocket API for external behavior triggers
- Raspberry Pi output layer (OLED / servo)
- Integration with local LLM inference state

## Tech

- Vanilla JavaScript, HTML5 Canvas
- Zero dependencies, zero build step
- MIT licensed
