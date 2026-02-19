"""
Generate vidhimur_tags.json from kanoon_raw.json using the auto-tagger.

Usage:
    py generate_tags.py                  # Preview only (no write)
    py generate_tags.py --write          # Write to vidhimur_tags.json
    py generate_tags.py --compare        # Compare auto vs hand-written tags
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import KANOON_RAW_FILE, VIDHIMUR_TAGS_FILE
from app.services.auto_tagger import generate_tags


def load_raw_cases() -> list[dict]:
    """Load cases from kanoon_raw.json."""
    with open(KANOON_RAW_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_existing_tags() -> dict:
    """Load existing vidhimur_tags.json if it exists."""
    if VIDHIMUR_TAGS_FILE.exists():
        with open(VIDHIMUR_TAGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def generate_all_tags(cases: list[dict]) -> dict:
    """Generate tags for all cases."""
    all_tags = {}
    for case in cases:
        tid = str(case["tid"])
        cite_titles = [c.get("title", "") for c in case.get("citeList", [])]

        tags = generate_tags(
            title=case["title"],
            headline=case["headline"],
            docsource=case["docsource"],
            cite_titles=cite_titles,
        )
        all_tags[tid] = tags.to_dict()

    return all_tags


def print_tags(all_tags: dict, cases: list[dict]) -> None:
    """Pretty-print auto-generated tags."""
    case_lookup = {str(c["tid"]): c for c in cases}

    for tid, tags in all_tags.items():
        case = case_lookup.get(tid, {})
        title = case.get("title", "Unknown")
        print(f"\n{'='*70}")
        print(f"  [{tid}] {title}")
        print(f"{'='*70}")
        print(f"  Keywords:   {tags['keywords']}")
        print(f"  Outcome:    {tags['outcome']}")
        print(f"  Issues:     {tags['legal_issues']}")
        print(f"  Statutes:   {tags['statutes_referenced']}")


def compare_tags(auto_tags: dict, hand_tags: dict, cases: list[dict]) -> None:
    """Compare auto-generated tags with hand-written ones."""
    case_lookup = {str(c["tid"]): c for c in cases}

    for tid in auto_tags:
        case = case_lookup.get(tid, {})
        title = case.get("title", "Unknown")
        auto = auto_tags[tid]
        hand = hand_tags.get(tid, {})

        if not hand:
            print(f"\n[{tid}] {title}")
            print(f"  ⚠ No hand-written tags — auto-generated only")
            continue

        print(f"\n{'='*70}")
        print(f"  [{tid}] {title}")
        print(f"{'='*70}")

        # Keywords comparison
        auto_kw = set(auto["keywords"])
        hand_kw = set(hand.get("keywords", []))
        overlap = auto_kw & hand_kw
        auto_only = auto_kw - hand_kw
        hand_only = hand_kw - auto_kw
        print(f"  Keywords overlap:   {len(overlap)}/{len(hand_kw)} hand-written matched")
        if auto_only:
            print(f"    + Auto found:     {auto_only}")
        if hand_only:
            print(f"    - Auto missed:    {hand_only}")

        # Issues comparison
        auto_iss = set(auto["legal_issues"])
        hand_iss = set(hand.get("legal_issues", []))
        print(f"  Issues overlap:     {len(auto_iss & hand_iss)}/{len(hand_iss)}")
        if auto_iss - hand_iss:
            print(f"    + Auto found:     {auto_iss - hand_iss}")
        if hand_iss - auto_iss:
            print(f"    - Auto missed:    {hand_iss - auto_iss}")

        # Statutes comparison
        auto_st = set(auto["statutes_referenced"])
        hand_st = set(hand.get("statutes_referenced", []))
        print(f"  Statutes overlap:   {len(auto_st & hand_st)}/{len(hand_st)}")
        if auto_st - hand_st:
            print(f"    + Auto found:     {auto_st - hand_st}")
        if hand_st - auto_st:
            print(f"    - Auto missed:    {hand_st - auto_st}")


def write_tags(all_tags: dict) -> None:
    """Write tags to vidhimur_tags.json."""
    with open(VIDHIMUR_TAGS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_tags, f, indent=4, ensure_ascii=False)
    print(f"\n✅ Written {len(all_tags)} entries to {VIDHIMUR_TAGS_FILE}")


if __name__ == "__main__":
    cases = load_raw_cases()
    auto_tags = generate_all_tags(cases)

    if "--compare" in sys.argv:
        hand_tags = load_existing_tags()
        compare_tags(auto_tags, hand_tags, cases)
    elif "--write" in sys.argv:
        print_tags(auto_tags, cases)
        write_tags(auto_tags)
    else:
        print_tags(auto_tags, cases)
        print(f"\n💡 Run with --write to save, or --compare to diff against hand-written tags.")
