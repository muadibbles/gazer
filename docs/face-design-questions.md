# Face Design & Animation — Open Questions

Ten questions to answer when designing and tuning gazer's face, ordered from foundational to behavioral. Grounded in oculomotor science, HRI trust research, Disney animation principles, and the competitive analysis.

---

**Q1. Eye proportions**
What is the right eye size relative to the face, and what proportions make a stylized eye read as expressive rather than dead? Research confirms eyes are the dominant trust signal — but what ratio of iris to sclera, lid opening to face height maximizes expressiveness without triggering uncanny mismatch?

**Q2. Main-sequence saccade velocity**
Should saccade velocity scale with amplitude (the main-sequence relationship), and how much does uniform velocity break perceived naturalness? Oculomotor science is clear that real eyes follow a velocity/amplitude curve — short saccades are fast, long ones peak higher but take longer. How noticeable is the current uniform speed, and what does it cost to fix?

**Q3. Fixational drift + microsaccade coupling**
What is the right fixational drift + microsaccade model during holds, and how much does the missing drift component degrade the sense of aliveness? We have microsaccades but no slow drift. The Bayesian and self-avoiding walk papers give us the model. What amplitude, timescale, and coupling to microsaccade onset creates the minimum viable "alive gaze"?

**Q4. Blink speed and lid asymmetry per state**
How should blink speed and lid asymmetry vary per behavior state, and what is the expressive range from a fast confident snap to a slow heavy-lidded close? The Disney blink paper argues speed and asymmetry are where expressiveness lives. We have blink rate per state but uniform mechanics. What are the target parameters for each of the 15 behavior states?

**Q5. Brow expressiveness range**
How much do brows independently carry the emotional signal, and is the current brow range sufficient or does it need to be pushed further? The face design literature says brows disambiguate emotional states (happy vs. surprised both use wide eyes; brows differentiate). Are our brows doing enough work, or are we underusing one of the two highest-signal features?

**Q6. Gaze aversion protocol**
What is the correct gaze aversion pattern during conversation — frequency, duration, and direction — and how do we implement it without the robot looking evasive? The ~70% eye contact norm, the gaze aversion HRI study, and our trust doc all point here as the biggest behavioral gap. What does a natural aversion look like in terms of timing and direction (up = thinking, down = recall)?

**Q7. Eye-to-head cascade latency**
How should the eye cascade timing be parameterized — specifically the latency between eye lead and head follow — to match the biological 100–200ms gap? The virtual agents review cites specific latency values. We have a cascade but the gap isn't explicitly parameterized. Does tightening or loosening this change how the motion reads?

**Q8. Independent settle timing for lid, brow, and mouth**
What is the right overlap timing for lid, brow, and mouth settling independently after a behavior transition? Animation principle #5 (overlap) says each part should settle at a different rate — currently they settle together. What mass/tension model gives each element a distinct settle time, and does it meaningfully change how transitions read?

**Q9. Variation budget vs. habituation threshold**
At what point does expressiveness produce habituation vs. sustained engagement, and what is the minimum variation needed to stay above that threshold? Leite et al.'s 5-week study and the habituation literature suggest deterministic loops wear out. What is the actual variation budget — how many distinct expressions, at what repetition frequency, before the robot starts to feel mechanical?

**Q10. Next feature on the abstraction spectrum**
What is gazer's design position on the abstraction spectrum — and are there specific feature additions (pupil dilation, mouth curve, specular highlight) that would increase trust without approaching the uncanny cliff? Every addition is a tradeoff: more features add expressiveness but narrow the safe stylization zone. What is the next highest-ROI feature to add, and what is the feature that would most risk crossing into uncanny territory?
