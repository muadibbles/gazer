"""
fetch_papers.py
---------------
Downloads research papers relevant to the gazer project using free public APIs:
  - arXiv API        : searches arxiv.org (CS / robotics / neuroscience)
  - Semantic Scholar : broader academic search with open-access PDF filter

Papers are saved to ./pdfs/
A manifest (papers.json) tracks downloads so re-runs skip duplicates.

Usage:
  python fetch_papers.py

Optional: set env var S2_API_KEY for higher Semantic Scholar rate limits.
  (Free key at: https://www.semanticscholar.org/product/api)

Example:
  S2_API_KEY=your_key python fetch_papers.py
"""

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

# Fix Windows console Unicode issues (cp1252 → utf-8)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── Config ───────────────────────────────────────────────────────────────────

OUTPUT_DIR    = Path(__file__).parent / "pdfs"
MANIFEST_FILE = Path(__file__).parent / "papers.json"

# Optional: Semantic Scholar free API key (higher rate limits)
S2_API_KEY = os.environ.get("S2_API_KEY", "")

# Delay between requests (seconds). arXiv recommends >= 3s, S2 >= 1s w/ key.
ARXIV_DELAY = 4.0
S2_DELAY    = 3.0

# Retry settings
MAX_RETRIES = 4
BACKOFF_BASE = 8   # seconds; doubles each retry

# ── Search topics ─────────────────────────────────────────────────────────────
#
# arXiv: (label, query, max_results)
# Use ti: prefix for title search (more precise than all:)
#
ARXIV_SEARCHES = [
    # Eye movement & saccades
    ("saccade",        'ti:saccade eye movement animation',                    6),
    ("saccade",        'ti:saccade oculomotor model',                          6),
    ("microsaccade",   'ti:microsaccade fixational eye movement',               5),
    # Blink
    ("blink",          'ti:eye blink animation model',                         5),
    ("blink",          'ti:eyelid animation mechanics',                        4),
    # Gaze & HRI
    ("gaze_hri",       'ti:social robot gaze behavior',                        6),
    ("gaze_hri",       'ti:robot eye contact interaction',                     5),
    # Lip sync & phonemes
    ("lip_sync",       'ti:viseme lip synchronization animation',              6),
    ("lip_sync",       'ti:phoneme viseme mouth shape animation',              5),
    # Audio/speech-driven face
    ("audio_face",     'ti:audio driven facial animation',                     6),
    ("audio_face",     'ti:speech driven 3D facial animation',                 6),
    # Emotion & expression
    ("emotion_robot",  'ti:robot facial expression emotion',                   5),
    ("emotion_robot",  'ti:facial action coding system animation',             4),
    # Robot face design
    ("robot_face",     'ti:social robot face design',                          6),
    ("robot_face",     'ti:humanoid robot face expressive',                    6),
    ("robot_face",     'ti:robot appearance anthropomorphism design',          5),
    # Robot character animation
    ("robot_anim",     'ti:robot character animation behavior',                6),
    ("robot_anim",     'ti:expressive robot motion animation',                 6),
    ("robot_anim",     'ti:robot nonverbal behavior animation',                5),
    # Other
    ("face_tracking",  'ti:gaze estimation real-time face',                    5),
    ("head_pose",      'ti:head pose estimation real-time',                    5),
    ("squash_stretch", 'ti:squash stretch animation deformation',              4),
    ("idle_gaze",      'ti:idle gaze wandering virtual agent',                 4),
    # Visual saliency / computational attention (gap: POI selection tuning)
    ("visual_saliency", 'ti:visual saliency model eye movement',                6),
    ("visual_saliency", 'ti:computational attention saliency map gaze',         5),
    ("visual_saliency", 'ti:bottom-up top-down attention visual scene',         5),
    # FACS / expression timing (gap: affect layer timing)
    ("facs_timing",    'ti:facial action coding system expression timing',       5),
    ("facs_timing",    'ti:micro-expression spontaneous facial movement',        5),
    ("facs_timing",    'ti:facial expression onset offset duration',             4),
    # Proxemics in HRI (gap: social distance and gaze)
    ("proxemics",      'ti:proxemics personal space robot interaction',          5),
    ("proxemics",      'ti:social distance robot human comfort',                 5),
    ("proxemics",      'ti:proxemic behavior social robot',                      4),
    # Multi-person / group gaze (gap: attention allocation)
    ("group_gaze",     'ti:multi-party conversation robot gaze',                 5),
    ("group_gaze",     'ti:turn-taking gaze robot interaction',                  5),
    ("group_gaze",     'ti:group attention social robot',                        4),
    # Robot navigation (new topic)
    ("navigation",     'ti:social robot navigation human-aware',                 6),
    ("navigation",     'ti:robot path planning social awareness',                5),
    ("navigation",     'ti:person following robot navigation',                   5),
    ("navigation",     'ti:robot crowd navigation pedestrian',                   5),
    # Animation principles in robot design (new topic)
    ("robot_principles", 'ti:Disney animation principles robot expressive',      5),
    ("robot_principles", 'ti:Laban movement notation robot motion',              5),
    ("robot_principles", 'ti:expressive motion principles robot design',         5),
    ("robot_principles", 'ti:anticipation follow-through robot animation',       4),
]

# Semantic Scholar: (label, query, max_results)
# Bulk endpoint supports boolean syntax: "phrase" for exact, + to require term
S2_SEARCHES = [
    # Eye movement & saccades
    ("saccade",        '"saccade" +eye +animation',                            6),
    ("saccade",        '"saccadic eye movement" model',                        6),
    ("saccade",        '"robot eye" +saccade',                                 5),
    ("microsaccade",   '"microsaccade" OR "fixational eye movement"',          6),
    # Blink
    ("blink",          '"eye blink" +animation +model',                        5),
    ("blink",          '"eyelid" +animation +character',                       4),
    # Gaze & HRI
    ("gaze_hri",       '"social robot" +gaze +interaction',                    6),
    ("gaze_hri",       '"robot gaze" +behavior +human',                        5),
    ("gaze_hri",       '"gaze aversion" +robot',                               4),
    ("idle_gaze",      '"idle gaze" OR "gaze behavior" +virtual +agent',       5),
    ("idle_gaze",      '"head movement" +gaze +animation +virtual',            4),
    # Lip sync & phonemes
    ("lip_sync",       '"viseme" +lip +animation',                             6),
    ("lip_sync",       '"phoneme" +mouth +animation +"real-time"',             5),
    ("lip_sync",       '"coarticulation" +viseme +animation',                  4),
    # Audio/speech-driven face
    ("audio_face",     '"audio-driven" +facial +animation',                    6),
    ("audio_face",     '"speech-driven" +face +animation',                     6),
    # Emotion & expression
    ("emotion_robot",  '"social robot" +emotion +expression +face',            6),
    ("emotion_robot",  '"facial action" +robot +animation',                    5),
    # Robot face design
    ("robot_face",     '"social robot" +face +design',                         6),
    ("robot_face",     '"robot face" +expressive +design',                     6),
    ("robot_face",     '"uncanny valley" +robot',                              5),
    ("robot_face",     '"anthropomorphism" +robot +appearance',                5),
    # Robot character animation
    ("robot_anim",     '"expressive robot" +motion +animation',                6),
    ("robot_anim",     '"robot" +nonverbal +behavior +animation',              5),
    ("robot_anim",     '"Laban" +robot +motion',                               4),
    ("robot_anim",     '"character animation" +robot +behavior',               5),
    # Other
    ("face_tracking",  '"gaze estimation" +"real-time" +face',                 5),
    ("squash_stretch", '"squash" +"stretch" +animation +character',            4),
    # Visual saliency / computational attention
    ("visual_saliency", '"visual saliency" +eye +movement',                     6),
    ("visual_saliency", '"computational attention" +gaze +model',               5),
    ("visual_saliency", '"saliency map" +eye +movement +prediction',            5),
    ("visual_saliency", '"bottom-up attention" +visual +saliency',              5),
    # FACS / expression timing
    ("facs_timing",    '"facial action" +FACS +expression +timing',             5),
    ("facs_timing",    '"micro-expression" +spontaneous +face',                 5),
    ("facs_timing",    '"expression duration" +facial +onset +offset',          4),
    # Proxemics in HRI
    ("proxemics",      '"proxemics" +robot +interaction',                       5),
    ("proxemics",      '"personal space" +robot +human',                        5),
    ("proxemics",      '"social distance" +robot +proxemic',                    4),
    # Multi-person / group gaze
    ("group_gaze",     '"multi-party" +robot +gaze',                            5),
    ("group_gaze",     '"turn-taking" +gaze +robot',                            5),
    ("group_gaze",     '"group conversation" +robot +attention',                4),
    # Robot navigation
    ("navigation",     '"social navigation" +robot +human',                     6),
    ("navigation",     '"human-aware" +robot +navigation',                      5),
    ("navigation",     '"person following" +robot',                             5),
    ("navigation",     '"robot navigation" +social +space',                     5),
    # Animation principles in robot design
    ("robot_principles", '"Laban" +robot +motion +expressive',                  5),
    ("robot_principles", '"animation principles" +robot +expressive',           5),
    ("robot_principles", '"anticipation" +robot +motion +expressive',           4),
    ("robot_principles", '"follow-through" +robot +animation',                  4),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def safe_filename(title: str, max_len: int = 80) -> str:
    """Convert a paper title to a safe filename slug."""
    s = re.sub(r'[^\w\s-]', '', title.lower())
    s = re.sub(r'[\s_-]+', '_', s).strip('_')
    return s[:max_len]


def load_manifest() -> dict:
    if MANIFEST_FILE.exists():
        return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest: dict) -> None:
    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def api_get(url: str, params: dict = None, headers: dict = None, delay: float = 1.0) -> requests.Response | None:
    """
    GET with retry/backoff for 429 and timeouts.
    Returns Response or None on permanent failure.
    """
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=25)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                wait = BACKOFF_BASE * (2 ** attempt)
                print(f"    [rate limit] waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code in (403, 404):
                print(f"    [http {resp.status_code}] {url[:60]}")
                return None
            print(f"    [http {resp.status_code}] retrying...")
            time.sleep(BACKOFF_BASE)
        except requests.exceptions.Timeout:
            wait = BACKOFF_BASE * (2 ** attempt)
            print(f"    [timeout] waiting {wait}s...")
            time.sleep(wait)
        except Exception as e:
            print(f"    [error] {e}")
            return None
    print(f"    [failed] gave up after {MAX_RETRIES} attempts")
    return None


def download_pdf(url: str, dest: Path) -> bool:
    """Download a PDF to dest. Returns True on success."""
    try:
        resp = requests.get(url, timeout=40, headers={
            "User-Agent": "gazer-research-fetcher/1.0 (academic; fillat@gmail.com)"
        }, allow_redirects=True)
        content = resp.content
        # Validate it's actually a PDF
        if resp.status_code == 200 and (
            resp.headers.get("content-type", "").startswith("application/pdf")
            or content[:4] == b'%PDF'
        ):
            dest.write_bytes(content)
            return True
        print(f"    [not a pdf] status={resp.status_code} type={resp.headers.get('content-type','?')[:40]}")
        return False
    except Exception as e:
        print(f"    [download error] {e}")
        return False


# ── arXiv API ─────────────────────────────────────────────────────────────────

ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_NS  = "http://www.w3.org/2005/Atom"

def search_arxiv(query: str, max_results: int) -> list[dict]:
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
    }
    resp = api_get(ARXIV_API, params=params, delay=ARXIV_DELAY)
    if not resp:
        return []
    root = ET.fromstring(resp.text)
    papers = []
    for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
        arxiv_id = entry.find(f"{{{ARXIV_NS}}}id").text.strip()
        title    = entry.find(f"{{{ARXIV_NS}}}title").text.strip().replace("\n", " ")
        abstract = entry.find(f"{{{ARXIV_NS}}}summary").text.strip().replace("\n", " ")
        authors  = [a.find(f"{{{ARXIV_NS}}}name").text for a in entry.findall(f"{{{ARXIV_NS}}}author")]
        raw_id   = arxiv_id.split("/abs/")[-1]
        pdf_url  = f"https://arxiv.org/pdf/{raw_id}"
        papers.append({
            "source":   "arxiv",
            "id":       arxiv_id,
            "title":    title,
            "authors":  authors,
            "abstract": abstract[:400],
            "pdf_url":  pdf_url,
        })
    return papers


# ── Semantic Scholar API ──────────────────────────────────────────────────────
# Using /paper/search/bulk which supports boolean logic (AND, OR, NOT, +, -)
# and is designed for batch retrieval. Same rate limits as /paper/search but
# returns more results per call and supports token-based pagination.

S2_BULK   = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
S2_FIELDS = "paperId,title,authors,abstract,year,openAccessPdf"

def search_semantic_scholar(query: str, max_results: int) -> list[dict]:
    # bulk endpoint supports boolean: quotes for phrases, + to require terms
    params  = {"query": query, "fields": S2_FIELDS, "limit": min(max_results * 3, 100)}
    headers = {"x-api-key": S2_API_KEY} if S2_API_KEY else {}
    resp = api_get(S2_BULK, params=params, headers=headers, delay=S2_DELAY)
    if not resp:
        return []
    papers = []
    for p in resp.json().get("data", []):
        oa = p.get("openAccessPdf")
        if not oa or not oa.get("url"):
            continue
        papers.append({
            "source":   "semantic_scholar",
            "id":       p.get("paperId", ""),
            "title":    p.get("title", "Untitled"),
            "authors":  [a["name"] for a in p.get("authors", [])],
            "abstract": (p.get("abstract") or "")[:400],
            "pdf_url":  oa["url"],
            "year":     p.get("year"),
        })
        if len(papers) >= max_results:
            break
    return papers


# ── Process a single paper ────────────────────────────────────────────────────

def process_paper(paper: dict, label: str, manifest: dict) -> bool:
    """Download paper if not already in manifest. Returns True if downloaded."""
    paper_id = paper["id"]
    title    = paper["title"]
    pdf_url  = paper["pdf_url"]

    if paper_id in manifest:
        return False   # already have it

    fname = safe_filename(title) + ".pdf"
    dest  = OUTPUT_DIR / fname

    # Skip if file already exists under a different ID
    if dest.exists():
        manifest[paper_id] = {
            "title": title, "file": fname, "source": paper["source"],
            "label": label, "authors": paper.get("authors", []),
            "abstract": paper.get("abstract", ""), "pdf_url": pdf_url,
        }
        save_manifest(manifest)
        return False

    tag = f"[{paper['source']}]"
    print(f"  {tag:<22} {title[:65]}")

    ok = download_pdf(pdf_url, dest)
    if ok:
        manifest[paper_id] = {
            "title": title, "file": fname, "source": paper["source"],
            "label": label, "authors": paper.get("authors", []),
            "abstract": paper.get("abstract", ""), "pdf_url": pdf_url,
        }
        save_manifest(manifest)
        print(f"    -> {fname}")
        return True
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    manifest   = load_manifest()
    downloaded = 0
    skipped    = 0

    if S2_API_KEY:
        print(f"Semantic Scholar: using API key (higher rate limits)")
    else:
        print(f"Semantic Scholar: no API key — using conservative delays")
        print(f"  (get a free key at https://www.semanticscholar.org/product/api)")

    # ── arXiv ──
    print(f"\n{'='*60}")
    print(f"arXiv searches ({len(ARXIV_SEARCHES)} queries)")
    print(f"{'='*60}")
    for label, query, n in ARXIV_SEARCHES:
        print(f"\n[{label}] {query}")
        results = search_arxiv(query, n)
        print(f"  {len(results)} results")
        for p in results:
            ok = process_paper(p, label, manifest)
            downloaded += ok
            skipped    += not ok
        time.sleep(ARXIV_DELAY)

    # ── Semantic Scholar ──
    print(f"\n{'='*60}")
    print(f"Semantic Scholar searches ({len(S2_SEARCHES)} queries)")
    print(f"{'='*60}")
    for label, query, n in S2_SEARCHES:
        print(f"\n[{label}] {query}")
        results = search_semantic_scholar(query, n)
        open_access = len(results)
        print(f"  {open_access} open-access results")
        for p in results:
            ok = process_paper(p, label, manifest)
            downloaded += ok
            skipped    += not ok
        time.sleep(S2_DELAY)

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"Downloaded: {downloaded}  |  Skipped (already had): {skipped}")
    print(f"PDFs:     {OUTPUT_DIR}")
    print(f"Manifest: {MANIFEST_FILE}")

    by_label: dict[str, list] = {}
    for entry in manifest.values():
        by_label.setdefault(entry["label"], []).append(entry["title"])

    print(f"\n{'LABEL':<22} COUNT  TITLES")
    print("-" * 80)
    for lbl, titles in sorted(by_label.items()):
        print(f"  {lbl:<20} {len(titles):>3}")
        for t in titles:
            print(f"    - {t[:70]}")


if __name__ == "__main__":
    main()
