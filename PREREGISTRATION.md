# Preregistration: harness-diff, experiment 2026-11-04

Frozen at the commit that adds this file, before the first counted run. The commit is pushed to the public
repository before any run under `runs/2026-11-04/` starts, and every receipt records the commit it ran from, so the
order can be checked: `git log -1 --format=%cI <commit>` against the earliest `started_utc` in the receipts. Anything
that changes later is logged in section 11 with its time and reason.

## 1. Question

Do the most-shared AGENTS.md and CLAUDE.md lines change whether a coding agent finishes a task correctly, by more
than the run-to-run noise of the agent itself? For each line the answer is one of three verdicts: helps, hurts, or
too small to see at this n, with the smallest effect this run could have seen stated next to it.

The noise is not small. In [agent-run-reliability](https://github.com/abhaymettu/agent-run-reliability), 384 Claude
Code runs put run-to-run noise at 50.1% of pass/fail variance. A line that moves a pass rate by a few points cannot
be told apart from rerunning the same agent, unless the design is built for it.

## 2. Lines

Nine rows, listed with their sources in [LINES.md](LINES.md). Each arm's exact text is in `arms/`, pinned by
sha256 in `arms/arms.json`; `harness_diff.experiment.Experiment.load` refuses to run an arm whose text does not match.
The lines were chosen from posts before any counted run, and the battery was frozen by another project
(reliability-weather, commit 30edb70) before the lines were chosen, so the battery cannot have been fitted to them.

## 3. Battery and harness

- reliability-weather's battery v1: 30 small Python tasks in four categories (8 `codefix`, 8 `implement`, 8 `data`,
  6 `chore`), each with starting files and a deterministic check. sha256 over the battery files:
  `b407a8cf9f16863d670d00d6aa27b846f4ec301dd8485bae4625d672a3bb0ffe`.
- Its harness, vendored byte for byte (`weather/battery.py`, `harness.py`, `sandbox.py`, pinned in
  `tests/test_pins.py`): a system prompt defining five JSON actions (list, read, write, run python3, finish), one
  action per turn, at most 4 turns, model-written code under macOS `sandbox-exec` with no network.
- **Graders do not leak.** A check never calls a model and is never shown to the model; it reads the files left when
  the agent finishes or runs out of turns. The model sees the task prompt, the starting files it chooses to read and
  the results of its own actions. No judge model is used anywhere in this experiment.
- **How the AGENTS.md reaches the agent.** Coding agents pass instruction files as context in the conversation, not
  in the system prompt, so the arm's text goes ahead of the task prompt in the first user message:

  ```
  # AGENTS.md instructions for this project

  <INSTRUCTIONS>
  {the arm's text}
  </INSTRUCTIONS>

  {the task prompt}
  ```

  The baseline arm has no AGENTS.md at all; its first message is the task prompt alone. The system prompt and
  everything else are identical across arms.

## 4. Models

- `haiku`: Claude Haiku through `claude -p` with `--tools "" --setting-sources "" --strict-mcp-config
  --disable-slash-commands` (no tools, no user settings, CLAUDE.md, hooks or MCP servers), through `claude-batch` on the
  machine this ran on, one resumed session per run. The pilot was served `claude-haiku-5-5`; the served id is recorded per call.
- `deepseek-flash`: the DeepSeek API, OpenAI-compatible chat completions, default sampling and default thinking mode.
  The pricing page served DeepSeek-V4.1-Flash-1017 under this name on 2026-11-04.
- Sonnet is left out. Its prior pass rate on this battery is 97.9%, so a line could not be seen helping it, and it
  costs about twelve times Haiku per run. Opus is left out for cost.
- The three long arms (section 5) run on `deepseek-flash` only. Their first message is about 12,600 tokens; DeepSeek
  serves the shared prefix from its cache after the first call, while `claude -p` pays a cache write of that size on
  every run, which would cost more than the whole Haiku budget.

## 5. Arms and design

- Arms: `baseline` (no file), the six line arms, `probe-only` (section 7), and on `deepseek-flash` also `long-full`,
  `long-trunc32` and `long-cut25`.
- Paired by task: every arm runs every task, and every comparison is made task by task, so the large differences
  between tasks cancel out of the interval.
- 5 rounds. In each round every arm runs every task once, except `baseline`, which runs three times (it is the
  control of seven rows, and giving the shared control about the square root of the number of comparisons times the
  runs is the usual allocation), and `long-full` on `deepseek-flash`, which runs twice (it is the control of two
  rows). Per task that is n = 15 for the baseline, 10 for `long-full` on Flash, and 5 for every other arm.
- Within a round the runs are shuffled with a seed (`20261104/<model>/<round>`), so no arm always runs first or
  last. Rounds run in order, so if a cap or a crash stops the run, every arm has the same number of complete rounds.
- `haiku` runs first. `deepseek-flash` rounds start only in DeepSeek's off-peak hours (half of peak; peak is 01:00 to
  04:00 and 06:00 to 10:00 UTC on weekdays): the experiment sets `deepseek_off_peak_only` and the runner waits. The two models are never compared with each other,
  so running them at different times confounds nothing in a row.
- Total: 1,500 `haiku` runs and 2,100 `deepseek-flash` runs if both finish.

## 6. Outcome, statistic, interval, verdict

- **Primary outcome**: pass or fail of the task's check on the final files.
- **Effect** for a row: the mean over the tasks of (treatment pass rate minus control pass rate), in percentage
  points. Inference is about this battery, so the only randomness is run to run.
- **Tasks per row**: all 30, except the three rows with a probe arm on either side (`long-file`, `cut-25`,
  `trunc-32k`), which leave out `chore_version_bump`. Its check compares `src/fmt/__init__.py` to an exact text, so
  an agent that obeys the probe rule fails it. `scripts/probe_conflicts.py` finds such tasks mechanically: it puts
  the probe line first in every Python file of each reference solution and runs the check; `chore_version_bump` is
  the only one that fails. Those three rows report all 30 tasks as well, as description only.
- **Interval**: the effect plus or minus z standard errors, where the variance is the sum over tasks of
  p(1 - p)(1/n_control + 1/n_treatment) divided by the number of tasks squared, with p = (passes in both arms + 0.5) / (runs in both
  arms + 1). The pseudo-count keeps a task that passed every run from claiming zero variance. Code:
  `harness_diff/stats.py`, `paired_effect`; tested against a hand-worked example in `tests/test_stats.py`.
- **Multiplicity**: z gives a simultaneous 95% over the rows of one model (Bonferroni): 6 rows on `haiku`
  (z = 2.638), 9 rows on `deepseek-flash` (z = 2.773). The controls in section 7 are not in the family and use 1.960.
- **Verdict**: helps when the whole interval is above zero, hurts when it is below zero, otherwise too small to see.
- **Secondary outcomes, descriptive only** (95% intervals, no verdicts): turns used per run, and bytes of files the
  agent created or changed. They say whether a line changed behaviour even when it did not change the pass rate.

## 7. Controls

- **Placebo (A/A)**: the baseline's first slot against its second slot in each round, 5 runs each per task. The two
  arms are the same thing, so its interval should contain zero. If it does not, that is reported as a warning about
  the method, not hidden.
- **Probe (positive control)**: `probe-only` is one rule an agent can visibly follow, "Every Python file you create
  or modify must begin with this exact first line: # Reviewed under AGENTS.md". Outcome: among runs that created or
  changed at least one `.py` file, whether every such file starts with that line. `probe-only` against `baseline`
  shows that the instrument sees an effect when one exists.
- **Probe buried** (`deepseek-flash`): the same compliance outcome, `long-full` (rule at byte 52,392 of a 52 KB file)
  against `probe-only`. **Probe after the cut**: `long-cut25` against `long-full`, the dilution claim behind "only
  rules the agent actually breaks stay in". The truncated arm loses the rule by construction, so it is not tested.

## 8. Power analysis, done before any counted run

The prior for each model is reliability-weather's day-1 runs of the same battery and harness with no AGENTS.md
(snapshot 2026-11-04 06:49 UTC in `prior/`: 93 `haiku` runs at a 94.6% pass rate, 94 `deepseek-flash` runs at
84.0%). Each task's true rate is taken as its k of n plus one run at the pooled rate. A line is modelled as one shift
on the log-odds scale applied to every task, so tasks near the ceiling move less, as a real instruction would. The
minimum detectable effect is the smallest such shift (reported in percentage points) that gets the right verdict in
80% of 1,000 simulated experiments at the design in section 5 and the z in section 6 (`harness-diff plan
experiments/2026-11-04.json --sims 1000`):

| Model | Rows | n control vs treatment | Smallest help it can see | Smallest hurt it can see |
|---|---|---|---|---|
| haiku | the six lines | 15 vs 5 | not reachable | -8.3 pp |
| deepseek-flash | the six lines | 15 vs 5 | +10.4 pp | -12.0 pp |
| deepseek-flash | long-file (29 tasks) | 15 vs 10 | +8.0 pp | -9.2 pp |
| deepseek-flash | cut-25, trunc-32k (29 tasks) | 10 vs 5 | +10.8 pp | -12.8 pp |

Haiku passes 94.6% of this battery with no AGENTS.md, so no line can be seen helping it at this n: the room above the
baseline is smaller than the noise. A line can still be seen hurting it. That asymmetry is the main limitation of the
experiment and is reported with every Haiku row.

Interval coverage was checked the same way before freezing: across log-odds shifts from -1.5 to +1.5 and the three
allocations above, a nominal 95% interval covered 94.9% to 99.8% of the time (2,000 draws per setting). A first
version centred the interval on an Agresti-Caffo adjusted difference; it was biased when the arms have different n
and covered 66%, so it was replaced before any counted run.

## 9. Exclusions and infrastructure errors

- A reply that is not a parseable action uses a turn and counts against the model.
- An infrastructure error (timeout, 5xx or 429 after four tries, unreadable envelope, a `claude -p` that cannot
  start) is not an outcome. It is retried in up to two more passes within the same round; if it still fails, that
  round is incomplete and the runner starts no later round for that model.
- An exception raised while carrying out the model's own action (for example, a write to a path that is a
  directory) ends the run as a fail: the model chose the action.
- The analysis uses complete rounds only: a round counts for a model when every run it scheduled has a pass or fail.
- `harness-diff run` refuses to start when the working tree differs from its commit outside `runs/` and `results/`,
  so the commit in each receipt is the code that produced it.
- Pilot runs (`runs/pilot/`, 8 runs on 2 tasks, 2026-11-04 06:48 UTC) tested the plumbing and cost and are excluded.

## 10. Budget

- List-price caps for the experiment: $1.40 for Claude (on the subscription, so no money changes hands; the figure is
  what the same calls would cost on the API, from `claude -p`'s own cost field) and $1.50 for DeepSeek (real spend,
  priced per call from api-docs.deepseek.com, read 2026-11-04 06:53 UTC). A model whose provider reaches its cap starts
  no new run; the analysis then uses the complete rounds, and the minimum detectable effects are restated for the
  achieved n.
- Every call's usage object is stored verbatim in its run receipt.

## 11. Changes before the freeze, and deviations

Before the freeze, an independent reviewer (a separate Opus 5.5 agent that wrote none of the code) read this document
and the code. Changes made from that review: the probe conflict and the 29-task rule in section 6; the off-peak wait
in section 5; the commit check and the first-incomplete-round stop in section 9; explicit `claude -p` isolation flags
in section 4, so a machine without `claude-batch` runs the same experiment; bytes written are now counted before the
check runs, so files the check itself creates are not counted. Not changed: a run that hits an infrastructure error
records $0 for the calls it made before the error, so the spend counter can run slightly under the true figure.

Deviations after the freeze: none yet.
