"""An experiment is a set of arms (AGENTS.md texts, or none) run on the frozen battery, and the rows that compare
them. Runs are idempotent: a run with a pass or fail receipt is never redone, so the same command resumes.

Receipts: runs/<experiment>/<model>/<arm>/<task>/r<k>.json, k = round * slots + slot. An arm with three slots gets
three runs per task per round; the shared baseline does, so it is not the noisiest side of every comparison.
"""
import hashlib
import json
import os
import platform
import random
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from weather import battery
from weather.harness import run_episode

from . import providers

REPO = Path(__file__).resolve().parent.parent
SCHEMA = 1
PROBE_LINE = "# Reviewed under AGENTS.md"


def compose(agents_md: str | None, prompt: str) -> str:
    """The task prompt as the agent sees it, with the project's AGENTS.md ahead of it the way coding agents inject
    instruction files: as context in the first user message, not in the system prompt."""
    if agents_md is None:
        return prompt
    return f"# AGENTS.md instructions for this project\n\n<INSTRUCTIONS>\n{agents_md.rstrip()}\n</INSTRUCTIONS>\n\n{prompt}"


@dataclass(frozen=True)
class Arm:
    id: str
    text: str | None

    @property
    def sha256(self) -> str | None:
        return None if self.text is None else hashlib.sha256(self.text.encode()).hexdigest()


@dataclass(frozen=True)
class Experiment:
    id: str
    battery: str
    battery_sha256: str
    max_turns: int
    rounds: int
    seed: int
    caps_usd: dict[str, float]
    slots: dict[str, dict[str, int]]  # model -> arm id -> runs per task per round
    arms: dict[str, Arm]
    rows: list[dict]
    controls: list[dict]
    root: Path
    off_peak_only: bool = False

    @classmethod
    def load(cls, path: Path) -> "Experiment":
        cfg = json.loads(path.read_text())
        arms = {}
        for arm_id, spec in cfg["arms"].items():
            text = None if spec is None else (path.parent / spec["path"]).resolve().read_text()
            arm = Arm(arm_id, text)
            if spec is not None and spec.get("sha256") and arm.sha256 != spec["sha256"]:
                raise SystemExit(f"arm {arm_id}: text sha256 {arm.sha256} is not the preregistered {spec['sha256']}")
            arms[arm_id] = arm
        exp = cls(cfg["id"], cfg["battery"], cfg["battery_sha256"], cfg["max_turns"], cfg["rounds"], cfg["seed"],
                  cfg["caps_usd"], cfg["slots"], arms, cfg["rows"], cfg.get("controls", []),
                  (path.parent / cfg.get("runs", "runs")).resolve() / cfg["id"], cfg.get("deepseek_off_peak_only", False))
        if battery.digest(exp.battery) != exp.battery_sha256:
            raise SystemExit("the battery on disk is not the preregistered one")
        return exp

    def receipt_path(self, model: str, arm: str, task: str, k: int) -> Path:
        return self.root / model / arm / task / f"r{k}.json"

    def jobs(self, model: str, rnd: int, tasks: list) -> list[tuple]:
        """Every run of one round for one model, in a seeded shuffle so no arm always runs first."""
        jobs = [(model, arm, rnd * m + s, task) for arm, m in self.slots[model].items() for s in range(m)
                for task in tasks]
        random.Random(f"{self.seed}/{model}/{rnd}").shuffle(jobs)
        return jobs


def read_receipt(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_atomic(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, p)


def repo_state() -> tuple[str, bool]:
    """The commit this code runs from, and whether the tree differs from it outside runs/ and results/."""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True)
        status = subprocess.run(["git", "status", "--porcelain", "--", ".", ":!runs", ":!results"], cwd=REPO,
                                capture_output=True, text=True)
    except OSError:
        return "", True
    if head.returncode:
        return "", True
    return head.stdout.strip(), bool(status.stdout.strip())


def written_files(work: Path, setup: dict[str, str]) -> dict[str, str]:
    """Files the agent created or changed, with their final text."""
    out = {}
    for p in sorted(work.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(work))
            text = p.read_text(errors="replace")
            if setup.get(rel) != text:
                out[rel] = text
    return out


class Spend:
    """List-price spend per provider family for one experiment, seeded from receipts already on disk."""

    def __init__(self, exp: Experiment):
        self.lock = threading.Lock()
        self.caps = exp.caps_usd
        self.usd = {f: 0.0 for f in self.caps}
        for p in exp.root.glob("*/*/*/r*.json"):
            r = read_receipt(p)
            if r:
                self.usd[providers.family(r["model"])] += r.get("cost_usd", 0.0)

    def over(self, fam: str) -> bool:
        with self.lock:
            return self.usd[fam] >= self.caps[fam]

    def add(self, fam: str, usd: float) -> None:
        with self.lock:
            self.usd[fam] += usd


def one_run(exp: Experiment, model: str, arm_id: str, k: int, task, spend: Spend, commit: str) -> str:
    path = exp.receipt_path(model, arm_id, task.id, k)
    old = read_receipt(path)
    if old and old["outcome"] in ("pass", "fail"):
        return "skip"
    fam = providers.family(model)
    if spend.over(fam):
        return "cap"
    arm = exp.arms[arm_id]
    slots = exp.slots[model][arm_id]
    base = {
        "schema": SCHEMA, "experiment": exp.id, "model": model, "arm": arm_id, "arm_sha256": arm.sha256,
        "task": task.id, "category": task.category, "run": k, "round": k // slots, "slot": k % slots,
        "battery": exp.battery, "battery_sha256": exp.battery_sha256, "max_turns": exp.max_turns,
        "repo_commit": commit, "python": platform.python_version(),
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with tempfile.TemporaryDirectory(prefix="hd-") as d:
        work = Path(d)
        task.materialize(work)
        try:
            ep = run_episode(providers.make(model), compose(arm.text, task.prompt), work, exp.max_turns)
        except providers.InfraError as e:
            write_atomic(path, {**base, "outcome": "infra_error", "error": str(e)[:500], "cost_usd": 0.0,
                                "attempts": (old or {}).get("attempts", 0) + 1})
            return "infra_error"
        except OSError as e:
            # The provider turns its own OS errors into InfraError, so this came from acting on the model's reply,
            # e.g. a write to a path that is a directory. The model chose the action; it counts as a fail.
            write_atomic(path, {**base, "outcome": "fail", "check_detail": f"action raised {e!r}"[:500],
                                "ended": "action_error", "turns_used": None, "cost_usd": 0.0, "written_bytes": 0,
                                "py_written": 0, "py_with_probe": 0, "calls": [], "transcript": []})
            return "fail"
        written = written_files(work, task.setup)
        ok, detail = task.check(work)
    cost = sum(c.get("cost_usd", 0.0) for c in ep["calls"])
    spend.add(fam, cost)
    py = [rel for rel in written if rel.endswith(".py")]
    write_atomic(path, {
        **base, "outcome": "pass" if ok else "fail", "check_detail": detail, "ended": ep["ended"],
        "turns_used": len(ep["turns"]), "cost_usd": cost,
        "written_bytes": sum(len(t.encode()) for t in written.values()),
        "py_written": len(py),
        "py_with_probe": sum(written[rel].split("\n", 1)[0].strip() == PROBE_LINE for rel in py),
        "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "calls": ep["calls"], "transcript": ep["turns"], "files": written,
    })
    return "pass" if ok else "fail"


def wait_for_off_peak(model: str) -> None:
    while model in providers.DEEPSEEK_PEAK_PRICES and providers.deepseek_is_peak(datetime.now(timezone.utc)):
        print(f"{model}: DeepSeek peak hours; waiting for the off-peak price", flush=True)
        time.sleep(300)


def run(exp: Experiment, models: list[str], workers: int, retries: int = 2, task_ids: list[str] | None = None,
        commit: str = "") -> None:
    tasks = battery.load(exp.battery)
    if task_ids:
        tasks = [t for t in tasks if t.id in set(task_ids)]
    spend = Spend(exp)
    t0 = time.time()
    for model in models:
        for rnd in range(exp.rounds):
            if exp.off_peak_only:
                wait_for_off_peak(model)
            jobs = exp.jobs(model, rnd, tasks)
            for attempt in range(1 + retries):
                with ThreadPoolExecutor(workers) as pool:
                    results = list(pool.map(lambda j: one_run(exp, *j, spend, commit), jobs))
                counts = {s: results.count(s) for s in sorted(set(results))}
                spent = {f: round(v, 4) for f, v in spend.usd.items()}
                print(f"{model} round {rnd} pass {attempt + 1}: {counts} spend {spent} at {time.time() - t0:.0f} s",
                      flush=True)
                if not counts.get("infra_error"):
                    break
            if counts.get("cap"):
                print(f"{model}: list-price cap reached in round {rnd}; later rounds not started", flush=True)
                break
            if counts.get("infra_error"):
                print(f"{model}: round {rnd} still has infrastructure errors; later rounds not started", flush=True)
                break
