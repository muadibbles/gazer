"""
curate_papers.py
----------------
Scores each downloaded paper by relevance to the gazer project and removes
low-scoring ones. Also removes clearly off-topic papers by title pattern.

Scoring is keyword-based against titles and abstracts. Papers below the
threshold are deleted from disk and removed from the manifest.

Usage:
  python curate_papers.py             # dry run — shows what would be deleted
  python curate_papers.py --apply     # actually delete low-scoring papers
  python curate_papers.py --min 3     # change score threshold (default: 2)

Example:
  python curate_papers.py --apply --min 2
"""

import argparse
import json
import re
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

OUTPUT_DIR    = Path(__file__).parent / "pdfs"
MANIFEST_FILE = Path(__file__).parent / "papers.json"

DEFAULT_MIN_SCORE = 2   # papers scoring below this are removed

# ── Relevance keywords ────────────────────────────────────────────────────────
#
# Each entry: (score_value, [keywords])
# Title or abstract containing any keyword in a group awards that score.
# Scores are additive.
#
RELEVANCE_RULES: list[tuple[int, list[str]]] = [
    # Core gazer topics — strong signal
    (4, ["saccade", "saccadic", "oculomotor", "microsaccade", "fixational eye"]),
    (4, ["viseme", "phoneme", "lip sync", "lip synchron", "lip-sync"]),
    (4, ["social robot", "humanoid robot", "expressive robot", "robot face", "robot eye"]),
    (4, ["eye blink", "eyelid", "blink model", "blink animation"]),
    (4, ["gaze behavior", "gaze aversion", "gaze following", "robot gaze", "social gaze"]),
    (4, ["squash and stretch", "squash & stretch", "squash-and-stretch"]),
    (4, ["laban movement", "effort shape", "expressive motion robot"]),
    (4, ["uncanny valley", "anthropomorphism robot", "android appearance"]),
    (4, ["visual saliency", "saliency map", "bottom-up attention", "computational attention"]),
    (4, ["facial action coding", "facs", "micro-expression", "expression onset", "expression offset"]),
    (4, ["proxemics", "personal space robot", "social distance robot", "proxemic behavior"]),
    (4, ["turn-taking gaze", "multi-party conversation", "group gaze", "group conversation robot"]),
    (4, ["social navigation", "human-aware navigation", "person following robot", "robot crowd"]),
    (4, ["animation principles robot", "anticipation robot motion", "follow-through robot"]),
    # Relevant animation / character topics
    (3, ["facial animation", "face animation", "talking head", "talking face"]),
    (3, ["speech driven", "audio driven", "audio-driven", "speech-driven"]),
    (3, ["character animation", "virtual character", "virtual agent"]),
    (3, ["facial expression", "face expression", "emotion expression"]),
    (3, ["robot animation", "robot motion", "robot behavior", "nonverbal behavior"]),
    (3, ["gaze estimation", "gaze tracking", "eye tracking", "eye movement"]),
    (3, ["head pose", "head movement", "head motion"]),
    (3, ["coarticulation", "articulatory", "mouth animation", "mouth shape"]),
    (3, ["blink", "blinking"]),
    # Broader relevant topics
    (2, ["human-robot interaction", "HRI", "social robotics"]),
    (2, ["face detection", "face tracking", "face model"]),
    (2, ["animation", "rendering", "canvas", "real-time graphics"]),
    (2, ["emotion recognition", "affect recognition", "sentiment face"]),
    (2, ["deformation", "shape deformation", "mesh deformation"]),
    (2, ["procedural animation", "motion synthesis", "motion generation"]),
    (2, ["3D face", "3D facial", "face mesh", "blendshape"]),
    # Weak signal — only helps if combined with above
    (1, ["real-time", "real time", "interactive"]),
    (1, ["robot", "robotic"]),
    (1, ["face", "facial"]),
    (1, ["eye", "gaze", "look"]),
    (1, ["animation", "animate", "animated"]),
    (1, ["expression", "emotion", "affect"]),
]

# Hard-reject patterns — if title matches any of these, score is forced to 0
# regardless of other content. Be specific to avoid false positives.
HARD_REJECT_PATTERNS: list[str] = [
    # Physics / engineering / unrelated science
    r"cosmic ray",
    r"ultrahigh energy",
    r"nanoscale film",
    r"chemo.mechanical",
    r"fracture.*metal",
    r"labview",
    r"motor fault",
    r"vehicular edge",
    r"raw material.*handling",
    r"marginalized coupled dict",
    r"bandwidth extension network",
    r"speech separation.*dereverberat",
    r"single.channel speech",
    r"closed.loop audio signal",
    r"morse code",
    r"astro.animation.*art.*science",
    r"hand pose estimation",
    r"multi.object tracking.*scheduling",
    r"image annotation.*dictionary",
    r"pooling.*neural",
    r"service subscription.*vehicular",
    r"state monitoring.*motor",
    r"real.time data analytics.*raw material",
    r"script reading detection",
    r"seismolog",
    r"geolog",
    r"climate",
    r"protein",
    r"genomic",
    r"medical imag(?!ing.*face)",
    r"mri\b",
    r"ct scan",
    r"drug ",
    r"cancer",
    r"tumor",
    # Robotics but not face/expression/gaze animation
    r"robot programming.*cad",
    r"industrial robot",
    r"coaching assistant.*robot",
    r"variable autonomy.*robot",
    r"telepresence robot.*comfort",
    r"robot.*vulnerability.*empathy",
    # Gaze papers about ML/RL, not robot face animation
    r"gaze.*hand.object interaction",
    r"gaze.*reinforcement",
    r"gaze.*retail",
    r"personalized.*video gaze estimation",
    r"teacher gaze.*robot learning",
    # LLM/vision model named BLINK
    r"multimodal large language model.*perceive",
    # Face papers about ID/privacy, not animation
    r"identity.preserving face anonymi",
    r"identity.consistent face generat",
    # Lip papers about speech recognition not animation
    r"lip.to.speech synthesis",
    r"lip reading.*vision.*language",
]

# ── Scoring ───────────────────────────────────────────────────────────────────

def score_paper(title: str, abstract: str) -> tuple[int, list[str]]:
    """
    Score a paper by relevance. Returns (score, matched_keywords).
    Score of 0 means hard-rejected.
    """
    text = (title + " " + abstract).lower()

    # Hard reject check first
    for pattern in HARD_REJECT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 0, [f"HARD_REJECT: {pattern}"]

    total  = 0
    hits: list[str] = []
    for points, keywords in RELEVANCE_RULES:
        for kw in keywords:
            if kw.lower() in text:
                total += points
                hits.append(kw)
                break   # only award each rule once

    return total, hits


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Curate downloaded research papers")
    parser.add_argument("--apply",  action="store_true", help="Actually delete low-scoring papers")
    parser.add_argument("--min",    type=int, default=DEFAULT_MIN_SCORE, help="Minimum score to keep (default: 2)")
    parser.add_argument("--show-all", action="store_true", help="Print all papers, not just rejects")
    args = parser.parse_args()

    if not MANIFEST_FILE.exists():
        print("No manifest found. Run fetch_papers.py first.")
        return

    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))

    keep   = {}
    remove = {}

    for paper_id, entry in manifest.items():
        title    = entry.get("title", "")
        abstract = entry.get("abstract", "")
        score, hits = score_paper(title, abstract)

        if score >= args.min:
            keep[paper_id] = entry
            if args.show_all:
                print(f"  KEEP  [{score:>3}]  {title[:70]}")
                print(f"         hits: {', '.join(hits[:5])}")
        else:
            remove[paper_id] = (score, hits, entry)

    print(f"\n{'='*70}")
    print(f"Papers to KEEP:   {len(keep)}")
    print(f"Papers to REMOVE: {len(remove)}")
    print(f"Min score:        {args.min}")
    print(f"Mode:             {'APPLY (deleting)' if args.apply else 'DRY RUN'}")
    print(f"{'='*70}\n")

    print("REMOVING:")
    print("-" * 70)
    for paper_id, (score, hits, entry) in sorted(remove.items(), key=lambda x: x[1][0]):
        title = entry.get("title", "?")
        fname = entry.get("file", "?")
        reason = hits[0] if hits else "score too low"
        print(f"  [{score:>3}]  {title[:65]}")
        print(f"         {reason}")
        if args.apply:
            pdf_path = OUTPUT_DIR / fname
            if pdf_path.exists():
                pdf_path.unlink()
                print(f"         -> deleted {fname}")
            else:
                print(f"         -> file not found: {fname}")

    if args.apply:
        MANIFEST_FILE.write_text(
            json.dumps(keep, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"\nManifest updated. {len(keep)} papers remaining.")
    else:
        print(f"\nDry run complete. Run with --apply to delete.")

    # Print what we're keeping grouped by label
    print(f"\n{'='*70}")
    print("KEEPING (by topic):")
    print("-" * 70)
    by_label: dict[str, list] = {}
    for entry in keep.values():
        by_label.setdefault(entry["label"], []).append(entry["title"])
    for lbl, titles in sorted(by_label.items()):
        print(f"\n  [{lbl}]  ({len(titles)} papers)")
        for t in titles:
            print(f"    - {t[:70]}")


if __name__ == "__main__":
    main()
