"""The paired estimate, its interval, the verdict, and the power analysis by simulation.

A cell is one task under one arm: k passes out of n runs. Every comparison is paired by task, so differences between
tasks cancel and only run-to-run noise is left in the interval.

- Effect: the mean over tasks of (treatment pass rate minus control pass rate), in raw proportions, which is
  unbiased for the battery's mean difference.
- Interval: effect plus or minus z standard errors. Each task's variance is p(1 - p)(1/n_control + 1/n_treatment)
  with p pooled over both arms plus half a pass and half a fail, so a task that went 5 of 5 and 15 of 15 still
  carries the variance 20 runs cannot rule out. In simulation from the prior (2,000 draws per setting, log-odds
  shifts from -1.5 to +1.5) a nominal 95% interval covered 94.9% to 99.8%. Centring on an Agresti-Caffo adjusted
  difference instead was biased when the arms have different n (the baseline has 3x the runs) and covered 66%.
  z is for a simultaneous 95% over the rows of one model (Bonferroni).
- Verdict: helps when the whole interval is above zero, hurts when it is below, otherwise too small to see.
"""
import math
import random
from dataclasses import dataclass
from statistics import NormalDist

Cells = dict[str, tuple[int, int]]  # task id -> (passes, runs)


def z_for(rows: int, alpha: float = 0.05) -> float:
    return NormalDist().inv_cdf(1 - alpha / (2 * rows))


@dataclass(frozen=True)
class Effect:
    tasks: int
    runs_control: int
    runs_treatment: int
    rate_control: float
    rate_treatment: float
    effect: float
    lo: float
    hi: float

    @property
    def verdict(self) -> str:
        if self.lo > 0:
            return "helps"
        if self.hi < 0:
            return "hurts"
        return "too small to see"


def paired_effect(control: Cells, treatment: Cells, z: float) -> Effect:
    tasks = sorted(t for t in control.keys() & treatment.keys() if control[t][1] and treatment[t][1])
    if not tasks:
        raise ValueError("no task has runs in both arms")
    T = len(tasks)
    var = rc = rt = 0.0
    for t in tasks:
        (ka, na), (kb, nb) = control[t], treatment[t]
        rc += ka / na
        rt += kb / nb
        p = (ka + kb + 0.5) / (na + nb + 1)
        var += p * (1 - p) * (1 / na + 1 / nb)
    effect, se = (rt - rc) / T, math.sqrt(var) / T
    return Effect(
        tasks=T,
        runs_control=sum(control[t][1] for t in tasks),
        runs_treatment=sum(treatment[t][1] for t in tasks),
        rate_control=rc / T,
        rate_treatment=rt / T,
        effect=effect,
        lo=effect - z * se,
        hi=effect + z * se,
    )


def mean_diff(control: dict[str, list[float]], treatment: dict[str, list[float]], z: float) -> tuple[float, float, float]:
    """Paired-by-task mean difference of a continuous outcome (turns, bytes written), with a normal interval."""
    tasks = sorted(t for t in control.keys() & treatment.keys() if control[t] and treatment[t])
    T = len(tasks)
    d = var = 0.0
    for t in tasks:
        a, b = control[t], treatment[t]
        d += sum(b) / len(b) - sum(a) / len(a)
        var += _var(a) / len(a) + _var(b) / len(b)
    d /= T
    se = math.sqrt(var) / T
    return d, d - z * se, d + z * se


def _var(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


# Power analysis. A line is modelled as one shift on the log-odds scale applied to every task, so tasks near the
# ceiling move less than tasks in the middle, which is how a real instruction behaves on an easy battery.

def _shift(p: float, delta: float) -> float:
    return 1 / (1 + math.exp(-(math.log(p / (1 - p)) + delta)))


def simulate(p: list[float], delta: float, n_control: int, n_treatment: int, z: float, sims: int,
             rng: random.Random) -> dict:
    """Draw `sims` experiments from per-task true rates p and a shift delta. Returns the true mean effect, the share
    of intervals that cover it, and the share whose verdict is helps and hurts."""
    q = [_shift(x, delta) for x in p]
    truth = sum(b - a for a, b in zip(p, q)) / len(p)
    cover = helps = hurts = 0
    for _ in range(sims):
        c = {str(i): (sum(rng.random() < a for _ in range(n_control)), n_control) for i, a in enumerate(p)}
        t = {str(i): (sum(rng.random() < b for _ in range(n_treatment)), n_treatment) for i, b in enumerate(q)}
        e = paired_effect(c, t, z)
        cover += e.lo <= truth <= e.hi
        helps += e.verdict == "helps"
        hurts += e.verdict == "hurts"
    return {"delta": delta, "truth": truth, "coverage": cover / sims, "helps": helps / sims, "hurts": hurts / sims}


def mde(p: list[float], n_control: int, n_treatment: int, z: float, direction: int, power: float = 0.8,
        sims: int = 400, seed: int = 0) -> float | None:
    """Smallest mean effect (in proportion, signed by direction) that gets the right verdict with the given power,
    or None when even a log-odds shift of 6 does not. Bisection on the shift, every probe on the same seed."""
    want = "helps" if direction > 0 else "hurts"
    lo, hi = 0.0, 6.0
    if simulate(p, direction * hi, n_control, n_treatment, z, sims, random.Random(seed))[want] < power:
        return None
    for _ in range(14):
        mid = (lo + hi) / 2
        r = simulate(p, direction * mid, n_control, n_treatment, z, sims, random.Random(seed))
        if r[want] >= power:
            hi = mid
        else:
            lo = mid
    q = [_shift(x, direction * hi) for x in p]
    return sum(b - a for a, b in zip(p, q)) / len(p)


def prior_rates(cells: Cells) -> list[float]:
    """Per-task true rates for the simulation, from earlier runs: each task's k of n plus one run at the pooled
    rate, so no task sits at exactly 0 or 1 and the battery mean is kept."""
    k_all, n_all = sum(k for k, _ in cells.values()), sum(n for _, n in cells.values())
    mu = k_all / n_all
    return [(k + mu) / (n + 1) for k, n in cells.values() if n]
