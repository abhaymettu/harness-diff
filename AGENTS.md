# AGENTS.md

Python 3.10+, standard library only, macOS (model code runs under `sandbox-exec` with `/opt/homebrew/bin/python3`).

- Test: `python3 -m unittest discover -s tests -t .`
- Build the arm texts: `python3 scripts/build_arms.py` (fetches the unlicensed Karpathy file; checks every sha256).
- Plan, run, report: `python3 -m harness_diff.cli plan|run|report experiments/<id>.json`; one diff:
  `python3 -m harness_diff.cli diff BEFORE.md AFTER.md --model haiku --plan`.

Rules for changes:
- `weather/battery.py`, `weather/harness.py`, `weather/sandbox.py` and `battery/` are the frozen instrument, pinned in
  `tests/test_pins.py`. Never edit them; a new battery is a new version and a new experiment.
- Never edit or delete a receipt under `runs/`. A preregistered experiment changes only through a dated line in its
  PREREGISTRATION.md section 11.
- `harness-diff run` refuses a dirty tree, so commit before running.
- Keys: `HARNESS_DIFF_API_KEY` is read at call time and never written to a receipt or a log.
