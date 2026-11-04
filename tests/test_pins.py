"""The measuring instrument is fixed: these values were pinned in the preregistration before the first counted run."""
import hashlib
import json
import unittest
from pathlib import Path

from harness_diff import experiment
from weather import battery

REPO = Path(__file__).resolve().parent.parent

# weather/*.py as they are in github.com/abhaymettu/reliability-weather at 30edb70, the battery v1 freeze commit.
VENDORED = {
    "weather/battery.py": "c423d8e5a2a3858965a3f4c55530ef7eed429b22d035132b19cffea7ffb75d8b",
    "weather/harness.py": "51a9ce7da0f2d6c91f0ec4b6cd88651fc484838b7ac5445342e076b5cadec350",
    "weather/sandbox.py": "1ba0496ba9e95a21c1f058de4a84c44754e165d7388b8461acf2e449f5507070",
}


class Pins(unittest.TestCase):
    def test_vendored_harness_is_the_frozen_one(self):
        for rel, sha in VENDORED.items():
            self.assertEqual(hashlib.sha256((REPO / rel).read_bytes()).hexdigest(), sha, rel)

    def test_battery_is_v1(self):
        self.assertEqual(battery.digest("v1"), "b407a8cf9f16863d670d00d6aa27b846f4ec301dd8485bae4625d672a3bb0ffe")
        self.assertEqual(len(battery.load("v1")), 30)

    def test_committed_arms_match_their_pins(self):
        meta = json.loads((REPO / "arms/arms.json").read_text())
        for arm_id, m in meta.items():
            path = REPO / "arms" / f"{arm_id}.md"
            if arm_id == "karpathy" and not path.exists():
                continue  # unlicensed upstream text; scripts/build_arms.py fetches it at a pinned commit
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), m["sha256"], arm_id)

    def test_the_experiment_loads_against_its_pins(self):
        if not (REPO / "arms/karpathy.md").exists():
            self.skipTest("arms/karpathy.md is unlicensed and not committed; run scripts/build_arms.py to fetch it")
        exp = experiment.Experiment.load(REPO / "experiments/2026-11-04.json")
        self.assertEqual(exp.slots["haiku"]["baseline"], 3)
        self.assertEqual(len(exp.rows), 9)

    def test_agents_md_goes_in_the_first_user_message(self):
        self.assertEqual(experiment.compose(None, "Fix it."), "Fix it.")
        self.assertEqual(
            experiment.compose("- Be brief.\n", "Fix it."),
            "# AGENTS.md instructions for this project\n\n<INSTRUCTIONS>\n- Be brief.\n</INSTRUCTIONS>\n\nFix it.",
        )

    def test_probe_is_cut_by_the_32k_truncation_and_kept_by_the_cut(self):
        probe = experiment.PROBE_LINE
        self.assertIn(probe, (REPO / "arms/long-full.md").read_text())
        self.assertIn(probe, (REPO / "arms/long-cut25.md").read_text())
        self.assertNotIn(probe, (REPO / "arms/long-trunc32.md").read_text())
        self.assertGreater((REPO / "arms/long-full.md").read_text().index(probe), 32 * 1024)


if __name__ == "__main__":
    unittest.main()
