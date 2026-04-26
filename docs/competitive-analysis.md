# Competitive Analysis — Open Source Projects

Maps open source projects covering similar ground to gazer across five categories. Knowledge cutoff August 2025.

---

## Category 1: Robot Eye Animation Systems

### 1. M5Stack-Avatar
**GitHub:** https://github.com/meganetaaan/m5stack-avatar

Animated cartoon eyes and mouth on M5Stack microcontroller displays. Eyes blink, dilate pupils, shift gaze. Supports discrete expression states (neutral, happy, sleepy, sad, doubt, angry).

**Tech stack:** C++ / Arduino, ESP32 + TFT display.

**Overlap:** Both animate expressive eyes with discrete affect states, blink cycles, and gaze direction. Both run a real-time render loop driven by state.

**What it does that gazer doesn't:**
- Runs on embedded hardware — no browser or PC required
- Mouth animation synchronized with expression
- Very low resource footprint (~$10 hardware)

**What gazer does that it doesn't:**
- 3D world model with POIs and spatial awareness
- Drive system / behavior compositor — it has states but no autonomous decision-making
- Sensor integration (face detection, VAD)
- Disney animation principles (bezier arcs, anticipation, spring overshoot)
- Differential drive and mobility

---

### 2. Nilheim Mechatronic Eye Mechanism
**GitHub:** https://github.com/Nilheim/Mechatronic-Eye-Mechanism

Arduino-driven servo control for physical animatronic eye mechanisms. Controls pan/tilt servos for eyeball movement and eyelid servos for blink/squint, per-eye independently.

**Tech stack:** C++ / Arduino, servo PWM, physical hardware.

**Overlap:** Both model gaze direction, eyelid states, and blink as independent axes.

**What it does that gazer doesn't:**
- Actual physical servo output
- Per-eye independent divergence (strabismus) for expressiveness
- Squint as a distinct state from full blink

**What gazer does that it doesn't:**
- Everything software-side: behavior engine, sensor fusion, world model, browser deployment

---

### 3. Adafruit AnimatedEyes
**GitHub:** https://github.com/adafruit/AnimatedEyes

High-quality animated eye firmware for SAMD51/nRF52 boards with round TFT displays. Procedural iris texture, corneal specular highlights, eyelids, autonomous idle saccades, blink, pupil dilation on startle.

**Tech stack:** C++ / CircuitPython, custom 60 fps rasterizer on microcontrollers.

**Overlap:** Saccades, blink, pupil dilation, idle wander, startle response — all present in both.

**What it does that gazer doesn't:**
- Photorealistic iris with procedural texture and corneal reflection
- Dual synchronized eye displays (two separate screens)
- Runs entirely on $10 hardware

**What gazer does that it doesn't:**
- Behavior decision layer — Adafruit eyes have autonomous saccades but no attention model, POIs, or behavioral states
- Sensor-driven inputs (face detection, VAD)
- 3D world and spatial model

---

## Category 2: Social Robot Behavior Engines

### 4. py_trees
**GitHub:** https://github.com/splintered-reality/py_trees

Python behavior tree framework used extensively in social robotics (ROS ecosystem). Composites (sequence, selector, parallel), decorators, blackboard shared state, visual debugger. Used in PAL Robotics TIAGo stacks.

**Tech stack:** Pure Python, optional ROS 2 integration.

**Overlap:** Both provide a decision-making layer selecting among named behaviors based on runtime conditions, with a shared state object.

**What it does that gazer doesn't:**
- Formal tree structure with provable semantics (ticks, success/failure/running)
- Visual tree debugger (py_trees_ros_viewer)
- Full ROS 2 integration

**What gazer does that it doesn't:**
- Drive-pressure scoring — more fluid emergent blending vs strict tree evaluation
- Rendering, animation timing, affect expression — py_trees is pure logic

---

### 5. OpenDR
**GitHub:** https://github.com/opendr-eu/opendr

EU Horizon 2020 robotics perception toolkit. Social robot perception modules: face detection, skeleton estimation, emotion recognition, action recognition, gaze estimation of humans — all ROS-interfaced.

**Tech stack:** Python, PyTorch, ROS 2.

**Overlap:** Both do face detection as a sensor input and treat human attention as a trigger.

**What it does that gazer doesn't:**
- Full perception pipeline: emotion recognition from face, skeletal pose, gaze estimation of the *human*
- ROS-native, works with real robot hardware
- Academic-grade documented algorithms

**What gazer does that it doesn't:**
- The animated output side — OpenDR perceives humans but doesn't display robot affect
- Autonomous behavior/animation from those percepts

---

### 6. Hanson Robotics HEAD (Sophia's behavior system)
**GitHub:** https://github.com/hansonrobotics/HEAD
Also: https://github.com/opencog/ros-behavior-scripting

The actual open-sourced behavior engine behind Sophia robot. Attention allocation, emotion state machine, behavior trees, blended animation on a Blender-driven face rig, TTS sync, gaze targeting at detected faces.

**Tech stack:** Python, ROS, Blender (for face mesh), OpenCog (optional).

**Overlap:** Large. Both have: attention targeting at humans, affect/emotion state, behavior compositor driving animation, face detection → gaze targeting, gaze cascade (eyes → head → body), speech integration.

**What it does that gazer doesn't:**
- Full animatronic hardware integration (servos for a physical humanoid face)
- Blender-based facial mesh with 50+ FACS action unit blend shapes
- OpenCog cognitive architecture for memory and reasoning
- Dialogue management and conversational AI hooks
- Lip sync from audio

**What gazer does that it doesn't:**
- Actually deployable — Hanson HEAD requires a full ROS environment, Blender, and the physical robot
- Differential drive mobility and world navigation
- Drive-pressure scoring (vs rigid emotion state machine)
- Zero-dependency browser deployment

---

### 7. MiRo BRain — Consequential Robotics
**GitHub:** https://github.com/MiRo-projects/miro_ros_interface
Also: https://github.com/consequential/miro

MiRo is a commercial social robot with a fully open-source brain explicitly modeled on mammalian neuroscience: subcortical (reflex), limbic (emotion/drive), hippocampal (spatial mapping), cortical (higher behavior). Drive system with homeostatic pressures (energy, social, curiosity) directly maps to behavior selection.

**Tech stack:** Python, ROS, C++ core.

**Overlap:** Closest architectural match to gazer. Both have: drive-based behavior selection with named pressures (curiosity, social engagement), attention/gaze at detected stimuli, novelty/familiarity decay on environmental objects, differential drive robot, spatial world model with POIs.

**What it does that gazer doesn't:**
- Full neuroscience-grounded architecture (subcortical reflexes, hippocampal map)
- Actual hardware robot with ears, camera, cliff sensors, IMU
- Multi-modal perception: vision + audio + touch
- Social reinforcement learning (learns human preferences)
- Sophisticated spatial navigation (SLAM-adjacent)

**What gazer does that it doesn't:**
- Browser-native, zero ROS dependency
- Expressive animated eye rendering with Disney animation quality
- Real-time affect visualization
- Dramatically simpler to deploy and extend

---

## Category 3: Expressive Robot Face / Head Systems

### 8. Furhat SDK
**GitHub:** https://github.com/FurhatRobotics/furhat-sdk

Social robot head with back-projected animated face on a physical mask. SDK controls facial expressions, gaze, speech, and listening behaviors. Has explicit concepts of "attention" (who the robot is looking at) and "attending" behavior.

**Tech stack:** Kotlin (JVM), proprietary renderer on robot, open SDK.

**Overlap:** Gaze management (attend, look-at, glance), expression states, speech/listening behavioral modes.

**What it does that gazer doesn't:**
- Full dialogue management — conversations with built-in turn-taking logic
- Multi-person attention (can track and switch between multiple people)
- Lip sync from synthesized speech
- Commercial-grade production system

**What gazer does that it doesn't:**
- 3D world model with spatial POIs and drive-based attention selection
- Autonomous wandering/exploration (Furhat is stationary)
- Open source rendering engine (Furhat's face renderer is proprietary)
- Disney-quality animation timing

---

### 9. Anki Vector — full engine open-sourced (victor)
**GitHub:** https://github.com/anki/victor

Vector's complete embedded behavior engine, open-sourced after company closure. Includes: mood system (valence/arousal), behavior tree, face tracking and attention, animated OLED face with many expression states, acoustic startle, social engagement behaviors, dock-to-charger.

**Tech stack:** C++, custom CLAD messaging, embedded Linux.

**Overlap:** Very close match. Both have: mood/affect state, eye animations with many expression states, attention/gaze at detected faces, startle response, dock-to-charger behavior, drive/pressure behavior selection.

**What it does that gazer doesn't:**
- Full embedded C++ production implementation on real hardware
- Procedural animation system with named "anim clips" (authored + procedural blend)
- Path planning with obstacle avoidance (proper costmap)
- Voice recognition and interaction
- Lift/head hardware animation

**What gazer does that it doesn't:**
- Browser-deployable, no hardware required
- 3D world model with named POIs
- Drive system visible and tunable in real-time
- Richer wander behavior and world simulation

---

## Category 4: HRI Frameworks / Social Robotics Middleware

### 10. DIARC — Drexel Interactive Architecture
**GitHub:** https://github.com/mscheutz/diarc

Full cognitive architecture for HRI research. Natural language understanding, task reasoning, knowledge base, perception, social behavior. Explicit attention and gaze management modules. Used with physical robots in HRI research.

**Tech stack:** Java (core), Python bindings, ROS integration.

**Overlap:** Attention management, behavior selection, sensor-driven social responses.

**What it does that gazer doesn't:**
- Natural language grounding and task understanding
- Formal knowledge representation (OWL ontologies)
- Multi-robot coordination

**What gazer does that it doesn't:**
- Eye rendering and animation — DIARC has no display component
- Web-native, no Java runtime required
- Real-time animated affect visualization

---

### 11. iCub gaze controller (iKinGaze)
**GitHub:** https://github.com/robotology/icub-main
Gaze controller: https://github.com/robotology/icub-tutorials

iCub humanoid research robot's gaze controller. Full published system: smooth pursuit, saccades, vergence, vestibulo-ocular reflex (VOR), neck/torso coordination. Moves eyes + head + torso in a coordinated cascade to fixate a 3D point.

**Tech stack:** C++, YARP middleware.

**Overlap:** The gaze cascade (eyes first, then head, then body) is architecturally identical to gazer's `trackWorldPoint` cascade. Both compute residual after head movement and pass remainder to eyes.

**What it does that gazer doesn't:**
- Biomechanically accurate eye/neck/torso dynamics (Jacobian-based)
- VOR — stabilizes gaze against head motion during locomotion
- Vergence (stereo cameras tracking depth)
- Published peer-reviewed kinematic model

**What gazer does that it doesn't:**
- Affect/expression layer
- Behavior compositor selecting what to look at and why
- Runs in a browser

---

## Category 5: Virtual Agent / NPC Behavior Systems

### 12. behavior3js
**GitHub:** https://github.com/behavior3/behavior3js

JavaScript behavior tree library for game/NPC AI. Composites, decorators, action nodes, blackboard. Runs in browser.

**Tech stack:** JavaScript, browser or Node.

**Overlap:** Both run in browser, both provide decision-making logic for an autonomous character with shared state.

**What it does that gazer doesn't:**
- Formal tree structure with visual editor (Behavior3Editor)
- General purpose — works for any NPC/agent type

**What gazer does that it doesn't:**
- Drive/pressure-based blending (softer, more organic than strict tree evaluation)
- Eye rendering, animation, affect
- Sensor integration and real-world I/O
- 3D world model

---

### 13. Beehave (Godot)
**GitHub:** https://github.com/bitbrain/beehave

GDScript behavior tree addon for Godot Engine. Used for NPC AI in Godot games. Clean API, visual debugging in Godot editor.

**Tech stack:** GDScript / Godot 4.

**Overlap:** NPC decision-making, idle/attention/engage-style behaviors common in game AI.

**What it does that gazer doesn't:**
- Full game engine integration (physics, audio, networking)
- Visual tree debugger baked into Godot editor
- Large community, active examples

**What gazer does that it doesn't:**
- Real-world sensor integration
- Robotics-specific concepts (drive pressure, spatial POIs, docking)
- Deployable in plain browser with no engine

---

## Summary Comparison Table

| Project | Eye Animation | Behavior Engine | Drive/Pressure | 3D World Model | Sensor Integration | Browser Deploy |
|---------|--------------|----------------|----------------|----------------|-------------------|----------------|
| **gazer** | High quality | Yes (17 behaviors) | Yes | Yes (POIs, wander) | Yes (face, VAD) | Yes |
| M5Stack-Avatar | Basic | No | No | No | No | No |
| Adafruit AnimatedEyes | Photorealistic | Minimal | No | No | No | No |
| Hanson HEAD | Mesh/blendshape | Yes | Partial | No | Yes | No |
| Vector (victor) | OLED/expressive | Yes | Yes | Minimal | Yes | No |
| MiRo BRain | None | Yes | Yes (bio) | Yes | Yes | No |
| Furhat SDK | Projected face | Partial | No | No | Yes | No |
| py_trees | None | Yes | No | No | No | No |
| iCub gaze | None | No | No | No | Yes | No |
| behavior3js | None | Yes | No | No | No | Yes |
| Beehave (Godot) | None | Yes | No | No | No | No |

---

## Key Gaps Gazer Could Learn From

**1. Lip sync / mouth animation** — Hanson HEAD, Furhat, and Vector all have this. If gazer ever speaks, a synchronized mouth would significantly increase social presence.

**2. Multi-person attention** — Furhat handles crowds; gazer's POI system only supports one "Person" POI at a time. A list of detected-person POIs with attention competition would be more realistic.

**3. Formal behavior tree debugger** — py_trees and Beehave both have visual tree inspection at runtime. Gazer's drive-based system is harder to visualize, but the live state panel is a step in this direction.

**4. VOR / gaze stabilization** — iCub's vestibulo-ocular reflex keeps gaze stable during body motion. Gazer currently has no compensation for drive yaw during saccades — fast turns may cause gaze drift artifacts.

**5. Procedural + authored animation clip blend** — Vector blends keyframed anim clips with procedural overrides. Gazer's behaviors are entirely procedural; a hybrid clip/procedural system would enable richer one-shot reactions.

**6. Emotion recognition in the loop** — OpenDR classifies human facial expressions, which could feed directly into gazer's affect state (robot mirrors the human's mood). Currently gazer only knows presence/absence, not the emotional valence of the detected human.

---

## Gazer's Strongest Differentiators

**1. Zero-dependency browser deployment** — every other system above requires ROS, a specific robot, an embedded toolchain, or a game engine. Gazer runs in a browser tab.

**2. Drive-pressure behavior selection with real-time tuning** — most competitors use rigid state machines or behavior trees. Gazer's scoring compositor is closer to MiRo's BRain but far more accessible and inspectable.

**3. Disney animation principles explicitly implemented** — bezier saccade arcs, anticipation wind-up, overshoot springs, cascade timing — none of the above implement these with this level of intentionality.

**4. Integrated 3D world with mobility in the same render loop** — the Three.js world + behavior compositor + drive system co-simulating in one file is architecturally unique.

**5. Sensor fusion via WebSocket relay** — the Python relay pattern (server.py + face_detect.py + audio.py) is lightweight and composable in a way ROS-based systems are not.
