# Research Paper Summary

Maps the paper library against gazer's current doc topics. Papers in `research/` (root) were manually curated; papers in `research/pdfs/` were fetched by `fetch_papers.py` and labeled automatically.

---

## Highly Relevant Papers

### Saccade mechanics

**`saccade_optimal_control_oculomotor.pdf`** (root, manually curated)
Optimal control model of saccade generation — explains *why* saccades have the velocity/duration profile they do (main sequence). Directly applies to `update()` saccade timing and the anticipation wind-up before a jump. The model predicts that saccade peak velocity scales with amplitude — we don't currently match this; all saccades use the same speed curve regardless of distance.
> **Dig in:** Use the main-sequence relationship to scale saccade speed with amplitude. Short saccades are quick; long ones peak higher but take longer. Currently we treat them uniformly.

**`advanced_statistical_methods_for_eye_movement_analysis_and_modeling_a_gentle_int.pdf`** (pdfs/, label: saccade)
Statistical framework for modeling gaze sequences as stochastic processes — random walks, hidden Markov models, Lévy flights. Relevant to the POI attention weighting and how `selectAttentionPOI` decides where to look next. The Lévy flight model (many short fixations, occasional long jumps) matches how people scan a scene and is a strong candidate for the idle wandering behavior.
> **Dig in:** Replace uniform random saccade in `idle` with a Lévy flight distribution — shorter jumps most of the time, occasional long ones. More naturalistic than pure random.

**`how_do_eyes_and_brain_search_a_randomly_structured_uninformative_scene_exploitin.pdf`** (pdfs/, label: saccade)
Scene search study: attention and memory interact to guide where we look next. Confirmed inhibition-of-return (already visited locations are suppressed). Directly maps to our `familiarity` field — the current linear decay is a simplification; the real suppression is stronger right after a visit and dissipates exponentially.
> **Dig in:** Refine `familiarity` decay curve to be exponential (fast drop, then plateau) rather than linear. Also: add explicit inhibition-of-return for saccade targets — don't return to a just-visited POI for at least ~1.5 seconds.

---

### Microsaccades and fixational movement

**`fixational_eye_movements_microsaccade.pdf`** (root, manually curated)
Core reference on the three components of fixational eye movement: tremor (~100 Hz, tiny), drift (slow random walk), and microsaccades (fast, involuntary corrective jumps). All three occur during what appears to be a still gaze. The behavioral significance: microsaccades reset drift and prevent neural adaptation.

**`bayesian_dynamical_modeling_of_fixational_eye_movements.pdf`** (pdfs/, label: microsaccade)
Bayesian model of drift + microsaccade dynamics. Shows that drift is a self-avoiding random walk — it tends to wander away from fixation center, then a microsaccade corrects it. The coupling between drift and microsaccade onset is the key mechanism.

**`a_self_avoiding_walk_with_neural_delays_as_a_model_of_fixational_eye_movements.pdf`** (pdfs/, label: microsaccade)
Statistical analysis showing the drift component shapes the persistence→antipersistence transition. The slow drift matters more than was previously thought — microsaccades are not the whole story.
> **Dig in (high value):** Gazer currently implements microsaccades as small random saccades during `idle`. We're missing the drift component entirely. Adding a slow 2D drift (self-avoiding random walk, amplitude ~0.3° eye rotation, timescale ~500ms) between microsaccades would make resting gaze look alive in a way that's currently absent. This is a low-complexity, high-realism gain.

---

### Blink modeling

**`blink_modeling_disney.pdf`** (root, manually curated)
Disney research on expressive blink timing — blink speed varies by emotional state, leading/trailing lid asymmetry, blink clusters during transitions. Directly applies to the per-behavior blink rate params and the blink animation easing.
> **Dig in:** We have blink rate per behavior but uniform blink speed. This paper argues the *speed* and *asymmetry* of the blink are where expressiveness lives — a slow, heavy blink reads as tired/sad; a fast snap reads as alert/confident. Worth parameterizing `blinkDownDur` and `blinkUpDur` per behavior state.

---

### Gaze in HRI (social robot gaze)

**`social_eye_gaze_hri_review.pdf`** (root, manually curated)
Comprehensive review of eye gaze in human-robot interaction. Covers: mutual gaze, gaze aversion, deictic gaze (pointing with eyes), and the social signaling function of each. Key finding: robots that use gaze aversion during speech pauses are rated as more natural than those that maintain constant contact.

**`robotic_gaze_aversion_hri.pdf`** (root, manually curated)
Focused study on gaze aversion specifically — timing, frequency, and direction of look-aways during conversation. Humans avert gaze ~40% of the time during face-to-face interaction; robots that don't avert feel uncanny. Aversion direction matters (up-right = thinking; down-left = recall).
> **Dig in (high value):** Gazer's `listening` and `speaking` behaviors maintain a tight gaze with slow saccades but don't implement structured gaze aversion. This paper gives exact timing guidelines: avert 0.5–2 seconds every 5–8 seconds during sustained conversation, bias upward during `processing`, restore quickly on `speech_end`. This is the single biggest gap between current behavior and natural-feeling conversation.

**`eye_gaze_virtual_agents_review.pdf`** (root, manually curated)
Review covering gaze in virtual agents specifically — includes head-eye coordination models, how fast eyes lead head on a redirect, and the effect of gaze direction on perceived intelligence/engagement.
> **Dig in:** Head-eye coordination section is directly applicable. Our current cascade (eyes first, head follows) matches the biological model but the timing gap isn't parameterized. This review cites specific latency values (eye leads head by ~100–200ms on a large redirect) we could use to tune the cascade delay.

**`gaze_behavior_during_a_long_term_in_home_social_robot_intervention_for_children_with_asd.pdf`** (pdfs/, label: gaze_hri)
Long-term deployment study of a social robot. Most relevant as a source of real-world gaze metrics under naturalistic conditions — what a robot actually does over weeks, not just in a lab. Useful validation that the behaviors we're designing are in the right range.

**`human_gaze_and_head_rotation_during_navigation_exploration_and_object_manipulation.pdf`** (pdfs/, label: gaze_hri)
Study of how humans coordinate gaze and head rotation during shared-space navigation. Relevant to the mobility + gaze integration in gazer's world model — when the robot is driving, how should gaze and head decouple from the body heading?
> **Dig in:** During mobility, humans tend to look ahead of their travel direction (predictive gaze). Gazer's current drive integration tracks the target POI while driving; this paper suggests we should bias gaze slightly forward of the current heading during navigation, returning to POI only at approach.

---

### Facial expressiveness (humanoid robot)

**`facially_expressive_humanoid_robot.pdf`** (root, manually curated)
Design and implementation of a physically expressive robot face. Relevant for the affect layer — specifically how many independent expression DOFs are needed to be readable, and which expressions are most salient to human observers. Finding: brow position and lid aperture carry most of the signal; mouth is secondary.
> **Dig in:** Validates our affect layer architecture (lids + brows + blink rate as primary). The paper ranks expression salience — worth checking if our behavior state definitions weight these in the right order.

---

## Less Relevant (but worth knowing about)

### Lip sync papers (not currently applicable)

The library has ~10 papers on audio-driven lip sync and 3D talking face animation. Gazer doesn't have a mouth/lips system yet. If that changes, these are the right starting point — particularly:

- **`jali_viseme_lip_sync.pdf`** and **`lipsync_realtime_framework.pdf`** (root) — practical real-time lip sync implementations
- **`audio_driven_realtime_facial_animation.pdf`** (root) — full pipeline for audio→face

File away for a future audio/speech expression phase.

### Emotion recognition papers (input, not output)

Several papers cover recognizing facial expressions from video (SAFER, geometric feature FER, continual learning FER). These would be useful if gazer were *reading* human emotion as a sensor input. Not currently in scope — the drive system responds to presence/motion/audio events, not recognized emotion.

> **Possible future use:** A face_detect.py extension that reads emotional state from the webcam and maps it to a drive event (e.g., detected distress → robot shifts to `concerned` affect). The FER papers would be the research basis.

### Squash/stretch and character animation

- **`space_time_sketching_of_character_animation.pdf`** — space-time constraints for character motion; too high-level for gazer's direct-physics approach
- **`pose_representations_for_deep_skeletal_animation.pdf`** — ML-based skeletal animation; not directly applicable

The animation-principles.md doc already captures the relevant Disney squash/stretch principles without needing these.

---

## Research Gaps — What's Missing

These topics come up in our docs but aren't covered by any paper in the library:

### 1. Attention salience and POI selection
The world-model doc describes `salience`, `familiarity`, and novelty-based selection, but there's no paper on computational attention models that would let us tune these values empirically. Specifically: how should salience decay after a visit? How does category (person vs. object) affect baseline weight?
> **Recommend fetching:** Papers on visual saliency maps and computational models of attention (Itti & Koch saliency model is the classic reference; newer work on learned saliency models).

### 2. Affect layer timing — when do expressions change?
The expressive-response.md doc describes micro-expressions and sustained affect, but there's no research backing on *how fast* real emotional expressions arise and decay. Disney's 12 principles give animation guidelines but not cognitive/behavioral timing data.
> **Recommend fetching:** FACS (Facial Action Coding System) papers on expression onset/offset timing. Ekman's work on micro-expressions specifically.

### 3. Idle behavior — what do eyes do when there's nothing to attend to?
The drive system describes `idle` as "relaxed, wandering" but the library only has eye movement papers from the fixation/task context (fixational movements, scene search). True idle eye behavior — slow ambient scanning, no task — is not covered.
> **Recommend fetching:** Studies on spontaneous gaze behavior, eye movement during mind-wandering, or "resting state" oculomotor behavior.

### 4. Social distance and gaze — proxemics
The HRI papers cover gaze direction but not how gaze behavior should adapt to physical distance. A person at 0.5m gets different gaze treatment than someone at 3m. No paper in the library covers this.
> **Recommend fetching:** Proxemics studies in HRI — Hall's proxemic zones applied to robot social behavior.

### 5. Multi-person gaze allocation
The world model has Person and Child as separate POIs but there's no research on how the robot should allocate attention when multiple people are present. Social gaze research covers dyadic interaction (one-on-one) almost exclusively.
> **Recommend fetching:** Group gaze dynamics, floor-holding and floor-taking signals in multi-party conversation, robot attention in group settings.

---

## Priority Order for Implementation

Based on coverage + impact:

| Priority | Research area | Paper | Impl effort |
|----------|--------------|-------|-------------|
| 1 | Gaze aversion in conversation | `robotic_gaze_aversion_hri.pdf` | Low — add to `listening`/`speaking` rules |
| 2 | Fixational drift + microsaccade coupling | `fixational_eye_movements_microsaccade.pdf` + Bayesian paper | Medium — new drift component in `idle` |
| 3 | Inhibition of return in POI selection | scene search paper | Low — tweak `familiarity` decay |
| 4 | Blink speed/asymmetry per state | `blink_modeling_disney.pdf` | Low — add params to behavior table |
| 5 | Head-eye latency calibration | `eye_gaze_virtual_agents_review.pdf` | Low — tune cascade timing |
| 6 | Saccade amplitude → velocity scaling | `saccade_optimal_control_oculomotor.pdf` | Medium — touch saccade planner |
| 7 | Predictive gaze during mobility | gaze+head rotation paper | Medium — touch drive integration |
