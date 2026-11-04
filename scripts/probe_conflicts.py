"""Which tasks can an agent not pass while obeying the probe rule? For each task, take the reference solution, put the
probe line first in every Python file the solution creates or changes, and run the task's check. A task that fails
is left out of every row with a probe arm on either side (preregistration section 6).

  python3 scripts/probe_conflicts.py      # prints the task ids, one per line
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness_diff.experiment import PROBE_LINE  # noqa: E402
from weather import battery  # noqa: E402


def conflicts(version: str = "v1") -> list[str]:
    out = []
    for task in battery.load(version):
        with tempfile.TemporaryDirectory(prefix="hd-probe-") as d:
            work = Path(d)
            task.materialize(work, with_solution=True)
            for rel in task.solution:
                if rel.endswith(".py"):
                    p = work / rel
                    p.write_text(f"{PROBE_LINE}\n{p.read_text()}")
            ok, _ = task.check(work)
        if not ok:
            out.append(task.id)
    return out


if __name__ == "__main__":
    print("\n".join(conflicts()))
