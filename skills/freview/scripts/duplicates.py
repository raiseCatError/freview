#!/usr/bin/env python3
"""Read-only duplicate candidates from supplied issue/PR metadata. No source code."""
import argparse
import json
from pathlib import Path
import re
import sys

STOP = {"a", "an", "the", "to", "and", "or", "for", "of", "with", "in", "on",
        "at", "from", "by", "into", "as", "is", "are", "this", "that", "its",
        "be", "via", "fix", "feature", "issue", "pr", "pull", "request",
        "add", "implement", "update"}


def tokens(text):
    return {x for x in re.findall(r"[a-z0-9][a-z0-9._/-]*", text.lower())
            if len(x) > 2 and x not in STOP}


def candidates(items, max_pairs=1000):
    rows = []
    if len(items) > 3000:
        raise ValueError("Too many records")
    if type(max_pairs) is not int or not 1 <= max_pairs <= 5000:
        raise ValueError("max_pairs must be between 1 and 5000")
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Expected object records")
        ident = item.get("id", item.get("number"))
        title = item.get("title")
        kind = item.get("kind", item.get("type", "issue"))
        body = item.get("body", "")
        if not isinstance(ident, (str, int)) or not isinstance(title, str) or not isinstance(body, str):
            raise ValueError("Each item needs id, title and optional body")
        if kind not in ("issue", "pr", "roadmap", "milestone", "document", "tracker"):
            raise ValueError("Unknown work-item kind")
        if len(title) > 500 or len(body) > 5000:
            raise ValueError("Oversized work-item metadata")
        rows.append({"id": str(ident), "kind": kind, "title": title,
                     "url": item.get("url") if isinstance(item.get("url"), str) else None,
                     "t": tokens(title),
                     "duplicate_refs": set(re.findall(r"(?:duplicate|dupe)\s+of\s+#(\d+)",
                                                      body.lower())),
                     "implements_refs": set(re.findall(r"(?:closes|fixes|resolves)\s+#(\d+)",
                                                      body.lower()))})
    output = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a["id"] == b["id"] and a["kind"] == b["kind"]:
                continue
            # A PR explicitly implementing an issue is not a duplicated work item.
            if ((a["kind"] == "pr" and b["kind"] == "issue" and
                 b["id"].lstrip("#") in a["implements_refs"]) or
                (b["kind"] == "pr" and a["kind"] == "issue" and
                 a["id"].lstrip("#") in b["implements_refs"])):
                continue
            intersection = len(a["t"] & b["t"])
            similarity = intersection / len(a["t"] | b["t"]) if a["t"] | b["t"] else 0
            explicit = ((b["kind"] == "issue" and b["id"].lstrip("#") in a["duplicate_refs"]) or
                        (a["kind"] == "issue" and a["id"].lstrip("#") in b["duplicate_refs"]))
            exact = len(a["t"]) >= 4 and a["t"] == b["t"]
            near = intersection >= 4 and similarity >= .78
            if not (explicit or exact or near):
                continue
            signals = []
            if explicit:
                signals.append("explicit-duplicate-reference")
            if exact:
                signals.append("matching-title-terms")
            elif near:
                signals.append("strong-title-overlap")
            output.append({
                "first": {k: a[k] for k in ("id", "kind", "title", "url")},
                "second": {k: b[k] for k in ("id", "kind", "title", "url")},
                "status": "candidate-unverified", "signals": signals,
                "title_overlap": round(similarity, 3),
                "review": "Compare deliverable, acceptance and release scope; distinguish parent/child, backport and issue-to-implementation PR."
            })
            if len(output) >= max_pairs:
                return output  # Result cap reached; report coverage as possibly truncated.
    return output


def main():
    parser = argparse.ArgumentParser(description="Report possible duplicate work items")
    parser.add_argument("input", help="JSON list or object with items list")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--max-pairs", type=int, default=1000, help="limit candidate output (1–5000)")
    args = parser.parse_args()
    try:
        source = Path(args.input)
        if source.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Input exceeds 16 MiB")
        value = json.loads(source.read_text(encoding="utf-8"))
        items = value.get("items") if isinstance(value, dict) else value
        if not isinstance(items, list):
            raise ValueError("Expected item list")
        pairs = candidates(items, max_pairs=args.max_pairs)
        cap_reached = len(pairs) >= args.max_pairs
        if args.format == "json":
            print(json.dumps({"kind": "freview-duplicate-candidates/1",
                              "scanned": len(items), "pairs": pairs,
                              "candidate_cap_reached": cap_reached,
                              "coverage": "Possibly truncated at the candidate limit" if cap_reached else "Complete for supplied metadata",
                              "notice": "No automated duplicate confirmation or issue mutations"}, indent=2))
        else:
            print("# Potential duplicate work items\n\nNone are automatically confirmed.\n")
            for pair in pairs:
                x, y = pair["first"], pair["second"]
                print("- " + x["kind"] + " " + x["id"] + " / " + y["kind"] + " " +
                      y["id"] + ": " + ", ".join(pair["signals"]))
            print("\nCandidates: " + str(len(pairs)))
            if cap_reached:
                print("Candidate cap reached; remaining pairs were not analyzed.")
        return 0
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        print("freview duplicates: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
