"""Read an experiment's receipts and compute every preregistered row. Only complete rounds count: a round is in the
analysis for a model when every run it scheduled has a pass or fail outcome."""
from collections import defaultdict

from weather import battery

from . import stats
from .experiment import Experiment, read_receipt


def load_runs(exp: Experiment, model: str) -> tuple[list[dict], list[int]]:
    tasks = battery.load(exp.battery)
    want = {(arm, rnd * m + s, t.id) for arm, m in exp.slots[model].items() for rnd in range(exp.rounds)
            for s in range(m) for t in tasks}
    got = {}
    for arm in exp.slots[model]:
        for p in (exp.root / model / arm).glob("*/r*.json"):
            r = read_receipt(p)
            if r and r["outcome"] in ("pass", "fail"):
                got[(arm, r["run"], r["task"])] = r
    complete = []
    for rnd in range(exp.rounds):
        keys = {k for k in want if k[1] // exp.slots[model][k[0]] == rnd}
        if keys and keys <= got.keys():
            complete.append(rnd)
    runs = [r for k, r in got.items() if k in want and r["round"] in complete]
    return runs, complete


def select(runs: list[dict], spec: str) -> list[dict]:
    """`arm` selects every run of an arm; `arm@s` selects one slot of it (the A/A placebo splits the baseline)."""
    arm, _, slot = spec.partition("@")
    return [r for r in runs if r["arm"] == arm and (not slot or r["slot"] == int(slot))]


def cells(runs: list[dict], outcome: str = "pass") -> stats.Cells:
    acc: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in runs:
        if outcome == "pass":
            hit = r["outcome"] == "pass"
        elif r["py_written"]:
            hit = r["py_with_probe"] == r["py_written"]
        else:
            continue
        acc[r["task"]][0] += hit
        acc[r["task"]][1] += 1
    return {t: (k, n) for t, (k, n) in acc.items()}


def values(runs: list[dict], key: str) -> dict[str, list[float]]:
    acc: dict[str, list[float]] = defaultdict(list)
    for r in runs:
        if r.get(key) is not None:
            acc[r["task"]].append(float(r[key]))
    return acc


def served(runs: list[dict]) -> list[str]:
    """Model ids the provider reported actually serving: modelUsage keys for Claude, the model field otherwise."""
    ids = set()
    for r in runs:
        for c in r["calls"]:
            ids |= set(c.get("modelUsage") or {})
            if c.get("model"):
                ids.add(c["model"])
    return sorted(ids)


def applicable(exp: Experiment, model: str, rows: list[dict]) -> list[dict]:
    have = exp.slots[model]
    return [row for row in rows if row["control"].partition("@")[0] in have and row["treatment"].partition("@")[0] in have]


def analyse(exp: Experiment, model: str) -> dict:
    runs, complete = load_runs(exp, model)
    rows = applicable(exp, model, exp.rows)
    z_rows = stats.z_for(max(len(rows), 1))
    z_one = stats.z_for(1)
    out = {"model": model, "complete_rounds": complete, "runs": len(runs), "served": served(runs),
           "cost_usd": round(sum(r["cost_usd"] for r in runs), 4), "z_rows": z_rows, "rows": [], "controls": []}
    if not complete:
        return out
    for kind, specs, z in (("rows", rows, z_rows), ("controls", applicable(exp, model, exp.controls), z_one)):
        for row in specs:
            keep = [r for r in runs if r["task"] not in row.get("exclude_tasks", ())]
            a, b = select(keep, row["control"]), select(keep, row["treatment"])
            outcome = row.get("outcome", "pass")
            e = stats.paired_effect(cells(a, outcome), cells(b, outcome), z)
            turns = stats.mean_diff(values(a, "turns_used"), values(b, "turns_used"), z_one)
            size = stats.mean_diff(values(a, "written_bytes"), values(b, "written_bytes"), z_one)
            out[kind].append({**row, "outcome": outcome, "tasks": e.tasks, "runs_control": e.runs_control,
                              "runs_treatment": e.runs_treatment, "rate_control": e.rate_control,
                              "rate_treatment": e.rate_treatment, "effect": e.effect, "lo": e.lo, "hi": e.hi,
                              "verdict": e.verdict, "turns": turns, "written_bytes": size})
            if row.get("exclude_tasks"):
                e30 = stats.paired_effect(cells(select(runs, row["control"]), outcome),
                                          cells(select(runs, row["treatment"]), outcome), z)
                out[kind][-1]["all_tasks"] = {"tasks": e30.tasks, "effect": e30.effect, "lo": e30.lo, "hi": e30.hi}
    return out
