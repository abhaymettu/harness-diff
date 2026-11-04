import random
import unittest

from harness_diff import stats


class PairedEffect(unittest.TestCase):
    def test_hand_computed_example(self):
        # Task a: 15/15 vs 5/5. Task b: 10/15 vs 2/5. Pooled p: 20.5/21 and 12.5/21; worked by hand.
        e = stats.paired_effect({"a": (15, 15), "b": (10, 15)}, {"a": (5, 5), "b": (2, 5)}, stats.z_for(1))
        self.assertEqual((e.tasks, e.runs_control, e.runs_treatment), (2, 30, 10))
        self.assertAlmostEqual(e.rate_control, 0.833333, places=6)
        self.assertAlmostEqual(e.rate_treatment, 0.7, places=6)
        self.assertAlmostEqual(e.effect, -0.133333, places=6)
        self.assertAlmostEqual(e.lo, -0.393437, places=6)
        self.assertAlmostEqual(e.hi, 0.126770, places=5)
        self.assertEqual(e.verdict, "too small to see")

    def test_verdicts(self):
        tasks = [str(i) for i in range(30)]
        hurt = stats.paired_effect({t: (15, 15) for t in tasks}, {t: (1, 5) for t in tasks}, stats.z_for(6))
        helped = stats.paired_effect({t: (1, 15) for t in tasks}, {t: (5, 5) for t in tasks}, stats.z_for(6))
        self.assertEqual((hurt.verdict, helped.verdict), ("hurts", "helps"))

    def test_only_shared_tasks_count(self):
        e = stats.paired_effect({"a": (3, 5), "b": (5, 5)}, {"a": (3, 5), "c": (0, 5)}, stats.z_for(1))
        self.assertEqual((e.tasks, e.effect), (1, 0.0))

    def test_bonferroni_z(self):
        self.assertAlmostEqual(stats.z_for(1), 1.959964, places=6)
        self.assertAlmostEqual(stats.z_for(6), 2.638257, places=6)
        self.assertAlmostEqual(stats.z_for(9), 2.772921, places=6)

    def test_mean_diff(self):
        d, lo, hi = stats.mean_diff({"a": [4, 4, 2], "b": [1]}, {"a": [3], "b": [1, 3]}, stats.z_for(1))
        # a: 3 - 3.333 = -0.333; b: 2 - 1 = 1. Mean 0.333.
        self.assertAlmostEqual(d, 0.333333, places=6)
        self.assertLess(lo, d)
        self.assertGreater(hi, d)


class Simulation(unittest.TestCase):
    def test_null_rarely_gives_a_verdict(self):
        p = [0.95] * 10 + [0.8] * 10 + [0.5] * 10
        r = stats.simulate(p, 0.0, 15, 5, stats.z_for(1), 500, random.Random(3))
        self.assertAlmostEqual(r["truth"], 0.0, places=12)
        self.assertGreater(r["coverage"], 0.93)
        self.assertLess(r["helps"] + r["hurts"], 0.07)

    def test_ceiling_makes_help_unreachable(self):
        p = [0.99] * 30
        self.assertIsNone(stats.mde(p, 15, 5, stats.z_for(6), +1, sims=100))
        self.assertLess(stats.mde(p, 15, 5, stats.z_for(6), -1, sims=100), -0.05)

    def test_prior_keeps_the_mean(self):
        p = stats.prior_rates({"a": (3, 3), "b": (1, 3)})
        self.assertAlmostEqual(sum(p) / 2, 4 / 6, places=6)
        self.assertTrue(all(0 < x < 1 for x in p))


if __name__ == "__main__":
    unittest.main()
