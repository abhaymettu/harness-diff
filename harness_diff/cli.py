"""harness-diff: does an AGENTS.md change move a coding agent's pass rate by more than run-to-run noise?

  harness-diff diff BEFORE.md AFTER.md --model haiku --n 5     run both on the battery, print the verdict
  harness-diff diff BEFORE.md AFTER.md --model haiku --plan    only print what the run could detect, and its cost
  harness-diff plan experiments/2026-11-04.json                the power analysis for a preregistered experiment
  harness-diff run experiments/2026-11-04.json --models haiku  run (or resume) it
  harness-diff report experiments/2026-11-04.json              the results table from its receipts

Use /dev/null for "no AGENTS.md". Receipts go under runs/; rerunning a command resumes where it stopped.
"""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

from weather import battery

from . import experiment, report, stats

REPO = Path(__file__).resolve().parent.parent
PRIOR = REPO / "prior"
# Measured on battery v1 on 2026-11-04 (Flash at the peak price; off-peak is half).
PER_RUN_USD = {"haiku": 0.0014, "sonnet": 0.012, "deepseek-flash": 0.0022, "deepseek-v4-pro": 0.011}


def prior_for(model: str, exclude=()) -> list[float]:
    path = PRIOR / f"{model}.json"
    if not path.exists():
        path = PRIOR / "haiku.json"
    cells = {t: tuple(v) for t, v in json.loads(path.read_text())["cells"].items() if t not in exclude}
    return stats.prior_rates(cells)


def power_table(exp: experiment.Experiment, model: str, sims: int) -> list[dict]:
    rows = report.applicable(exp, model, exp.rows)
    z = stats.z_for(max(len(rows), 1))
    cache, out = {}, []
    for row in rows:
        nc = exp.rounds * exp.slots[model][row["control"].partition("@")[0]]
        nt = exp.rounds * exp.slots[model][row["treatment"].partition("@")[0]]
        key = (nc, nt, tuple(row.get("exclude_tasks", ())))
        if key not in cache:
            p = prior_for(model, key[2])
            cache[key] = (stats.mde(p, nc, nt, z, +1, sims=sims), stats.mde(p, nc, nt, z, -1, sims=sims))
        up, down = cache[key]
        out.append({"row": row["id"], "n_control": nc, "n_treatment": nt, "mde_helps": up, "mde_hurts": down})
    return out


def pp(x: float | None) -> str:
    return "not reachable" if x is None else f"{100 * x:+.1f} pp"


def cmd_plan(a) -> int:
    exp = experiment.Experiment.load(Path(a.experiment))
    for model in exp.slots:
        p = prior_for(model)
        rows = report.applicable(exp, model, exp.rows)
        z = stats.z_for(max(len(rows), 1))
        print(f"\n{model}: prior mean pass rate {sum(p) / len(p):.3f} over {len(p)} tasks; "
              f"{len(rows)} rows, simultaneous z {z:.3f}")
        for r in power_table(exp, model, a.sims):
            print(f"  {r['row']:18} n {r['n_control']:>2} vs {r['n_treatment']:>2} per task   "
                  f"smallest visible help {pp(r['mde_helps'])}, hurt {pp(r['mde_hurts'])}")
        cov = [stats.simulate(p, d, exp.rounds * 3, exp.rounds, stats.z_for(1), a.sims, random.Random(1))
               for d in (-1.0, 0.0, 1.0)]
        print("  coverage of a single 95% interval at log-odds shift -1, 0, +1: "
              + ", ".join(f"{c['coverage']:.3f}" for c in cov))
        runs = len(battery.load(exp.battery)) * exp.rounds * sum(exp.slots[model].values())
        print(f"  {runs} runs, about ${runs * PER_RUN_USD.get(model, 0.002):.2f} at list price for short arms")
    return 0


def cmd_run(a) -> int:
    exp = experiment.Experiment.load(Path(a.experiment))
    commit, dirty = experiment.repo_state()
    if dirty and not a.tasks:
        print("refusing to run: commit first, so every receipt names the exact code it ran from", file=sys.stderr)
        return 2
    models = a.models.split(",") if a.models else list(exp.slots)
    experiment.run(exp, models, a.workers, task_ids=a.tasks.split(",") if a.tasks else None, commit=commit)
    return 0


def fmt_row(r: dict) -> str:
    lo, hi = max(r["lo"], -1.0), min(r["hi"], 1.0)  # a normal interval can pass 100 pp; no effect can
    return (f"| {r['id']} | {100 * r['rate_control']:.1f}% | {100 * r['rate_treatment']:.1f}% | "
            f"{100 * r['effect']:+.1f} pp | [{100 * lo:+.1f}, {100 * hi:+.1f}] | "
            f"{r['runs_control']} / {r['runs_treatment']} | {r['verdict']} |")


def cmd_report(a) -> int:
    exp = experiment.Experiment.load(Path(a.experiment))
    results = {m: report.analyse(exp, m) for m in exp.slots}
    out = REPO / "results" / f"{exp.id}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=1) + "\n")
    for m, res in results.items():
        print(f"\n### {m}: {res['runs']} runs in complete rounds {res['complete_rounds']}, "
              f"${res['cost_usd']:.2f} list, served {', '.join(res['served'])}")
        if not res["rows"]:
            continue
        print("\n| row | control | treatment | effect | interval | runs | verdict |\n|---|---|---|---|---|---|---|")
        for r in res["rows"] + res["controls"]:
            print(fmt_row(r))
    print(f"\nwrote {out.relative_to(REPO)}")
    return 0


def cmd_diff(a) -> int:
    texts = {}
    for name, path in (("before", a.before), ("after", a.after)):
        p = Path(path)
        texts[name] = None if path == "/dev/null" or not p.exists() or not p.read_text().strip() else p.read_text()
    key = hashlib.sha256(json.dumps([texts["before"], texts["after"], a.model]).encode()).hexdigest()[:12]
    folder = REPO / "runs" / "diffs" / key
    folder.mkdir(parents=True, exist_ok=True)
    arms = {}
    for name, text in texts.items():
        if text is None:
            arms[name] = None
        else:
            (folder / f"{name}.md").write_text(text)
            arms[name] = {"path": f"{name}.md", "sha256": hashlib.sha256(text.encode()).hexdigest()}
    cfg = {"id": f"diff-{key}", "battery": "v1", "battery_sha256": battery.digest("v1"), "max_turns": 4,
           "rounds": a.n, "seed": int(key, 16) % 10**9, "caps_usd": {"claude": a.cap, "openai": a.cap},
           "slots": {a.model: {"before": 1, "after": 1}}, "arms": arms, "runs": ".",
           "rows": [{"id": "after vs before", "control": "before", "treatment": "after"}], "controls": []}
    cfg_path = folder / "experiment.json"
    cfg_path.write_text(json.dumps(cfg, indent=1) + "\n")
    exp = experiment.Experiment.load(cfg_path)
    (up, down), = [(r["mde_helps"], r["mde_hurts"]) for r in power_table(exp, a.model, a.sims)]
    runs = 2 * a.n * len(battery.load("v1"))
    print(f"{runs} runs on {a.model}, about ${runs * PER_RUN_USD.get(a.model, 0.002):.2f} at list price. "
          f"At n={a.n} it can see a help of {pp(up)} or a hurt of {pp(down)}; anything smaller reads as too small.")
    if a.plan:
        return 0
    experiment.run(exp, [a.model], a.workers, commit=experiment.repo_state()[0])
    res = report.analyse(exp, a.model)
    if not res["rows"]:
        print("no complete round yet; rerun the same command to resume")
        return 1
    r = res["rows"][0]
    print(f"\nbefore {100 * r['rate_control']:.1f}%, after {100 * r['rate_treatment']:.1f}%: "
          f"{100 * r['effect']:+.1f} pp, 95% interval [{100 * r['lo']:+.1f}, {100 * r['hi']:+.1f}], "
          f"{r['runs_control']} + {r['runs_treatment']} runs: {r['verdict']}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="harness-diff", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("experiment")
    p.add_argument("--sims", type=int, default=400)
    p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("run")
    p.add_argument("experiment")
    p.add_argument("--models")
    p.add_argument("--tasks", help="comma-separated task ids, for a pilot")
    p.add_argument("--workers", type=int, default=8)
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("report")
    p.add_argument("experiment")
    p.set_defaults(fn=cmd_report)
    p = sub.add_parser("diff")
    p.add_argument("before")
    p.add_argument("after")
    p.add_argument("--model", default="haiku")
    p.add_argument("--n", type=int, default=5, help="runs per task per arm")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--cap", type=float, default=2.0, help="list-price dollars at which no new run starts")
    p.add_argument("--sims", type=int, default=400)
    p.add_argument("--plan", action="store_true", help="print the power and cost, run nothing")
    p.set_defaults(fn=cmd_diff)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
