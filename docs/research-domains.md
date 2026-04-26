# Research Domains

The 10 academic fields that gazer's features draw from. Use these to guide paper searches and identify coverage gaps.

---

## 1. Oculomotor Science
Everything about how eyes physically move: saccade dynamics, microsaccades, fixational drift, smooth pursuit, the main-sequence velocity/amplitude relationship, inhibition of return.

**Gazer features:** saccade planner, microsaccades, gaze cascade, spring physics on eye/head/body

---

## 2. Attention & Salience
What drives where eyes go next: computational saliency models, top-down vs bottom-up attention, scene search strategies, inhibition of return, novelty bias.

**Gazer features:** POI salience weights, familiarity decay, selectAttentionPOI, wander target scoring, spatial memory novelty

---

## 3. Facial Expression Science
How expressions work and when: FACS action units, micro-expression timing, onset/offset durations, emotional valence/arousal models, what the face does during speech.

**Gazer features:** affect layer, micro-expressions, blink system, lid/brow/mouth params per behavior state

---

## 4. Social Gaze in HRI
The social meaning of eye contact: mutual gaze, gaze aversion, deictic gaze, turn-taking signals, proxemics, group attention allocation, how robot gaze affects perceived naturalness.

**Gazer features:** listening/speaking behaviors, look3D, face_detected events, POI attention, conversational behavior set

---

## 5. Character Animation Principles
The craft of making motion feel alive: Disney's 12 principles, Laban movement notation, squash/stretch, anticipation, follow-through, timing and weight.

**Gazer features:** anticipation wind-up, bezier arcs, overshoot springs, cascade timing, per-state enter duration and easing

---

## 6. Expressive Robot Design
Robot-specific design decisions: uncanny valley, anthropomorphism tradeoffs, minimal vs realistic faces, which features (brows/lids/mouth) carry the most expressive signal, robot appearance and perceived personality.

**Gazer features:** eye canvas design, brow/lid/mouth expressiveness, stylized vs realistic choices

---

## 7. Social Robot Navigation
How robots move around people: human-aware path planning, proxemic zones, person-following, crowd navigation, gaze-during-locomotion coordination.

**Gazer features:** mobility state machine, wander scoring, potential-field avoidance, state-gated wandering, battery/charging routing

---

## 8. Motivation & Behavior Architecture
How autonomous agents decide what to do: drive theory, subsumption architectures, behavior trees, utility-based selection, curiosity/novelty models, goal persistence.

**Gazer features:** drive system, pressure scoring, rule engine, task system, novelty decay, session temperament

---

## 9. Affective Computing & Emotion Modeling
Computational models of emotional state: arousal/valence space, emotion contagion, state transition timing, how internal state maps to observable behavior, circumplex models.

**Gazer features:** affect layer, behavior state set, micro-expressions, drive pressure curves, time-of-day scheduling

---

## 10. Audio-Driven Expression
Speech as an animation input: VAD, amplitude-to-mouth mapping, prosody as expression cue, speech rhythm and head/eye behavior.

**Gazer features:** audio.py VAD pipeline, amplitude param → mouth open, speech_start/end events, listening/speaking/processing behavior transitions

---

## Coverage Assessment

| Domain | Current paper coverage | Gap level |
|--------|----------------------|-----------|
| Oculomotor science | Good — saccade, microsaccade, fixational papers | Low |
| Character animation principles | Good — Disney blink paper, squash/stretch | Low |
| Social gaze in HRI | Partial — review papers, gaze aversion study | Medium |
| Expressive robot design | Partial — humanoid robot paper, HRI reviews | Medium |
| Facial expression science | Thin — FER papers but no FACS/timing research | High |
| Attention & salience | Thin — scene search paper but no saliency models | High |
| Social robot navigation | None | High |
| Motivation & behavior architecture | None | High |
| Affective computing & emotion modeling | None | High |
| Audio-driven expression | Partial — audio face papers but not VAD/prosody focus | Medium |
