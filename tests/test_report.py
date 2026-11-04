import json
import tempfile
import unittest
from pathlib import Path

from harness_diff import experiment, report
from weather import battery


def receipt(arm: str, task: str, k: int, slots: int, passed: bool) -> dict:
    return {"model": "haiku", "arm": arm, "task": task, "run": k, "round": k // slots, "slot": k % slots,
            "outcome": "pass" if passed else "fail", "turns_used": 2, "written_bytes": 100, "py_written": 1,
            "py_with_probe": 0, "cost_usd": 0.001, "calls": [{"modelUsage": {"claude-haiku-5-5": {}}}]}


class Report(unittest.TestCase):
    def test_complete_rounds_and_verdicts_from_receipts(self):
        tasks = [t.id for t in battery.load("v1")]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "line.md").write_text("- Be brief.\n")
            cfg = {"id": "t", "battery": "v1", "battery_sha256": battery.digest("v1"), "max_turns": 4, "rounds": 2,
                   "seed": 1, "caps_usd": {"claude": 1, "openai": 1}, "runs": ".",
                   "slots": {"haiku": {"baseline": 2, "line": 1}},
                   "arms": {"baseline": None, "line": {"path": "line.md"}},
                   "rows": [{"id": "line", "control": "baseline", "treatment": "line"},
                            {"id": "line-29", "control": "baseline", "treatment": "line",
                             "exclude_tasks": [tasks[0]]}],
                   "controls": [{"id": "placebo", "control": "baseline@0", "treatment": "baseline@1"}]}
            (root / "exp.json").write_text(json.dumps(cfg))
            exp = experiment.Experiment.load(root / "exp.json")
            # Round 0 complete: baseline always passes, the line always fails. Round 1 has one run only.
            for t in tasks:
                for k in (0, 1):
                    experiment.write_atomic(exp.receipt_path("haiku", "baseline", t, k), receipt("baseline", t, k, 2, True))
                experiment.write_atomic(exp.receipt_path("haiku", "line", t, 0), receipt("line", t, 0, 1, False))
            experiment.write_atomic(exp.receipt_path("haiku", "line", tasks[0], 1), receipt("line", tasks[0], 1, 1, True))

            res = report.analyse(exp, "haiku")
            self.assertEqual((res["complete_rounds"], res["runs"], res["served"]), ([0], 90, ["claude-haiku-5-5"]))
            line, line29 = res["rows"]
            self.assertEqual((line["tasks"], line["runs_control"], line["runs_treatment"]), (30, 60, 30))
            self.assertEqual((line["effect"], line["verdict"]), (-1.0, "hurts"))
            self.assertEqual((line29["tasks"], line29["all_tasks"]["tasks"]), (29, 30))
            placebo = res["controls"][0]
            self.assertEqual((placebo["effect"], placebo["verdict"]), (0.0, "too small to see"))


if __name__ == "__main__":
    unittest.main()
