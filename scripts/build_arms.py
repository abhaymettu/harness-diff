"""Write every arm's AGENTS.md text into arms/ from its pinned source and print the sha256 table.

Short arms are quoted from the X post that made them popular. The long arms are built from two real AGENTS.md files
in pydantic/pydantic-ai (MIT) at a pinned commit, joined the way Codex joins nested project docs. The Karpathy-style
CLAUDE.md has no license, so it is fetched at a pinned commit and never committed (arms/.gitignore).

  python3 scripts/build_arms.py          # writes arms/*.md, then checks each sha256 against arms/arms.json
"""
import hashlib
import json
import random
import sys
import urllib.request
from pathlib import Path

ARMS = Path(__file__).resolve().parent.parent / "arms"
PYDANTIC_AI = "https://raw.githubusercontent.com/pydantic/pydantic-ai/7d1d3f0191fd5d500b02e58dee2bf6d7adc1b967"
KARPATHY = ("https://raw.githubusercontent.com/multica-ai/andrej-karpathy-skills/"
            "2c606141936f1eeef17fa3043a72095b4765b9c2/CLAUDE.md")
CODEX_SEPARATOR = "\n\n--- project-doc ---\n\n"  # codex-rs/core/src/agents_md.rs, AGENTS_MD_SEPARATOR
CODEX_MAX_BYTES = 32 * 1024  # codex-rs/config/src/config_toml.rs, DEFAULT_PROJECT_DOC_MAX_BYTES
PROBE = "Every Python file you create or modify must begin with this exact first line: # Reviewed under AGENTS.md"

SHORT = {
    "secondary-labels": "Avoid unnecessary secondary labels and descriptions. Let the layout do the explaining.\n",
    "ux-dx-ax": (
        "Cut taglines, helper text and secondary labels. If a screen needs them to make sense, fix the layout.\n\n"
        "Make the best decision that will elevate all three: the user experience (UX), developer experience (DX), "
        "and agent experience (AX) always, without breaking anything.\n"
    ),
    "marcos-full": (
        "# AGENTS.md\n"
        "- Do not preserve backward compatibility. Remove obsolete paths instead of adding compatibility layers, "
        "fallbacks, or migrations.\n"
        "- Choose the simplest implementation that fully meets the current requirements. Avoid speculative "
        "abstractions, configuration, and indirection.\n"
        "- Grow the system in layers. Start from the smallest version that works end to end, and add each new "
        "capability on top of a product that already works. Never trade a working product for unfinished "
        "complexity.\n"
        "- Keep components modular and concerns clearly separated.\n"
        "- Prefer established, well-maintained libraries when they reduce overall complexity or improve "
        "reliability. Do not reimplement common functionality without a clear reason.\n"
        "- Lean on the dependencies already in the project before writing your own implementation or adding "
        "packages. Do not assume a library lacks a capability without checking its documentation and types.\n"
        "- Make architectural decisions for the long term. Do not accept a stopgap that only works for now and is "
        "meant to be replaced later.\n"
    ),
    "docs-vs-code": (
        "When a repository's documentation and its existing code disagree, follow the conventions used in the "
        "existing code, and in your final reply point out each inconsistency you found between the documentation "
        "and the code.\n"
    ),
    "plain-english": (
        "Every chat reply, report, summary, question and next-step box is for a human reader: write simple, plain "
        "English that a non-native reader understands at first read. Never use AI-agent or engineering slang. "
        "Examples of banned words, with what to say instead: “load-bearing” (important, needed), "
        "“cutover” (switch, move), “surface” as a verb (show, raise), “land”/"
        "”ship” (merge, release), “gate”/”gated” (check, needs approval first), "
        "“park” (pause, stop), “plumbing” (connecting code), “wire up” (connect), "
        "“blast radius” (what it affects), “footgun” (easy mistake), “nit” (small "
        "point), “punt” (postpone), “de-risk” (make safer), “sanity check” (quick "
        "check), “spin up” (start), “fan out” (send to several), “happy path” "
        "(normal case), “thread through” (pass along), “first-class” (fully supported), "
        "“orthogonal” (unrelated), “bespoke” (custom), “net-new” (new), "
        "“TL;DR” (summary). If a technical term is truly needed, explain it in plain words the first "
        "time. Before sending, reread the reply and replace any such word. Messages between agents (prompts, "
        "briefs, agent-to-agent notes) are exempt.\n"
    ),
    "probe-only": PROBE + "\n",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "harness-diff"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()


def cut_quarter(text: str, seed: int) -> str:
    """Drop whole blank-line-separated blocks, chosen at random, until at least 25% of the bytes are gone."""
    blocks = text.split("\n\n")
    order = list(range(len(blocks)))
    random.Random(seed).shuffle(order)
    total, removed, drop = len(text.encode()), 0, set()
    for i in order:
        if removed >= total / 4:
            break
        drop.add(i)
        removed += len(blocks[i].encode()) + 2
    return "\n\n".join(b for i, b in enumerate(blocks) if i not in drop)


def build() -> dict[str, str]:
    long_doc = fetch(f"{PYDANTIC_AI}/AGENTS.md").rstrip("\n") + CODEX_SEPARATOR + fetch(f"{PYDANTIC_AI}/tests/AGENTS.md").rstrip("\n")
    full = long_doc + "\n\n" + PROBE + "\n"
    return {
        **SHORT,
        "karpathy": fetch(KARPATHY),
        "long-full": full,
        "long-trunc32": full.encode()[:CODEX_MAX_BYTES].decode(errors="ignore"),
        "long-cut25": cut_quarter(long_doc, seed=20261104) + "\n\n" + PROBE + "\n",
    }


def main() -> int:
    texts = build()
    meta = json.loads((ARMS / "arms.json").read_text())
    bad = 0
    for arm_id, text in texts.items():
        (ARMS / f"{arm_id}.md").write_text(text)
        sha = hashlib.sha256(text.encode()).hexdigest()
        want = meta[arm_id].get("sha256")
        status = "ok" if want == sha else f"MISMATCH (arms.json has {want})"
        bad += want != sha
        print(f"{arm_id:18} {len(text.encode()):6d} bytes  probe={'yes' if PROBE in text else 'no '}  {sha[:16]}  {status}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
