# Robot Face Design & Trust

Research synthesis on robot face design as a lever for increasing human trust, engagement, and long-term usage.

---

## 1. The Uncanny Valley

Masahiro Mori's 1970 hypothesis describes a dip in perceived affinity as robot humanlikeness increases, followed by a recovery at full human realism. MacDorman & Ishiguro (2006) and Seyama & Nagayama (2007) confirm the dip is real but clarify its shape: it behaves more like a **cliff than a symmetric valley**. Once you enter the uncanny zone, increasing realism rarely recovers affinity to cartoon levels — the perceptual system keeps finding new violations (skin texture, micro-expressions, sclera color).

Zlotowski et al. (2015, *Frontiers in Psychology*) meta-analysis found the valley is triggered primarily by **mismatches between modalities** — realistic skin + wrong eye movement, or humanlike voice + robotic face. The safest design space is either clearly stylized (well below the valley) or fully photorealistic with motion-capture fidelity (above it). For practical robotics, the former is nearly always the right choice.

---

## 2. Minimal vs. Realistic Faces

Breazeal's Kismet (2003) and later Jibo demonstrated that **expressive stylized faces consistently outperform realistic ones** on likeability and trust in user studies. Heerink et al.'s (2010) UTAUT-robot model found perceived sociability — driven by face design — is a stronger predictor of long-term adoption than task performance.

Roomba's facelessness works because it is a floor appliance with no social contract; users anthropomorphize it anyway (Sung et al., 2007) but report lower social engagement. Vector (Anki, 2018) with its OLED stylized eyes scored higher on emotional engagement than Pepper's more humanoid face in comparative studies (Niemelä et al., 2019).

The **sweet spot is cartoonish abstraction with high expressiveness** — enough features to read emotional state, few enough to avoid uncanny mismatch.

---

## 3. Features That Drive Trust

Eyes are the dominant channel. Mutlu et al. (2009, *HRI*) showed gaze alone accounts for more variance in perceived attentiveness and trustworthiness than any other facial feature. Eyebrows are the second-highest signal for emotional disambiguation (happy vs. surprised both use wide eyes; brows differentiate). Mouth contributes to valence (positive/negative) but is largely redundant when eyes are expressive.

**For an eyes-only system like gazer, the literature supports sufficiency**: Gockley et al. (2005) found faces reduced to eyes + brows generated trust ratings comparable to full faces in task-oriented interactions. The key requirement is that eyes must be **dynamically responsive** — static stylized eyes score worse than animated minimal eyes.

---

## 4. Expressiveness and Long-Term Trust

Short-term studies (single session) almost universally favor more expressive robots. Long-term data is thinner but instructive.

Leite et al. (2013, *IJSR*) ran a 5-week chess-playing robot study: empathic expressiveness maintained engagement over time while the control (minimal expression) saw habituation and declining interaction quality. Mutlu & Forlizzi (2008) found that in workplace deployments, robots perceived as socially aware (tracked by gaze behavior, not face complexity) sustained user engagement longer.

**Habituation risk is real but is driven by repetition of the same expressions**, not expressiveness per se — varied, context-driven responses maintain novelty. The implication: a behavior system with multiple affect states and probabilistic variation (as gazer implements) is better than a robot with a fixed happy face.

---

## 5. Gaze as a Trust Signal

This is the best-supported finding in the literature. Mutlu et al. (2009) showed that **mutual gaze increases information retention and compliance** in HRI. Andrist et al. (2012, *HRI*) demonstrated that referential gaze (robot looks at an object it's discussing) increases perceived competence. Gaze aversion at socially appropriate moments (before answering, during "thinking") increases naturalness ratings.

Staring continuously without aversion triggers discomfort — the same threshold (~70% eye contact) as human-human norms (Argyle & Cook, 1976). **Gaze that tracks humans** — following people as they move, returning to face after distraction — is the single highest-ROI behavior for perceived social presence in stylized systems.

---

## 6. Design Recommendations (Consensus from Literature)

- **Stay clearly stylized.** Abstract eyes on a non-humanoid body avoid uncanny triggers entirely.
- **Prioritize dynamics over detail.** A blinking, tracking, saccading simple eye beats a detailed static one every time.
- **Gaze behavior > face complexity.** Invest in gaze logic (attention, aversion, referential gaze) before adding face features.
- **Vary expressions stochastically.** Deterministic loops habituate quickly; probabilistic variation maintains perceived aliveness.
- **Eyes + brows is sufficient for trust.** Mouth adds valence but is not required for social presence in task contexts.
- **Match modalities.** If voice is present, ensure prosody and face expression align — mismatch is the primary uncanny trigger.

---

## Implications for Gazer

| Finding | Gazer status |
|---------|-------------|
| Stylized face avoids uncanny valley | ✅ Clearly abstract, non-humanoid |
| Dynamic eyes beat static detail | ✅ Saccades, blink, anticipation, spring overshoot |
| Eyes + brows sufficient for trust | ✅ Current design has no mouth (adds later) |
| Gaze behavior > face complexity | ✅ Drive system + POI attention is the primary investment |
| Stochastic variation prevents habituation | ✅ Probabilistic behavior selection, novelty decay |
| Gaze aversion needed during conversation | ⚠️ Not yet implemented — biggest gap per the research |
| Referential gaze increases competence | ⚠️ Robot looks at objects but doesn't signal "I'm looking at X" |
| Mutual gaze during listening increases trust | ⚠️ Listening behavior is tight but no explicit mutual-gaze phase |

---

## Key Researchers

- **Mori** — uncanny valley original hypothesis
- **MacDorman** — perceptual mechanisms of the uncanny, modality mismatch
- **Breazeal** — social robotics design (Kismet, Jibo)
- **Mutlu** — gaze behavior in HRI, compliance and trust
- **Fogg** — persuasion and trust in technology
- **Leite** — long-term HRI, habituation and empathy
- **Andrist** — referential gaze, gaze as communication signal
