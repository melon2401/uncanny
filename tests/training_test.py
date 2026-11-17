import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

from detector.training_data import select, validate, REPO, REVISION, SOURCES
from detector.trained_features import clip_feature, capture_image, FEATURE_VERSION
from detector.evaluate_trained_exports import samples
from detector.extract_training import key
from detector.train_visual import load_features, linear_scores, metrics, validation_threshold, wilson


def plan():
    files = {f"{s}/{i}/a.mp4": dict(bytes=1, sha256=hashlib.sha256(f"{s}:{i}".encode()).hexdigest())
             for s in SOURCES for i in range(100)}
    return dict(dataset=REPO, revision=REVISION, rows=select(files))


class TrainingTests(unittest.TestCase):
    def test_split_keeps_prompts_together_and_generator_unseen(self):
        p = validate(plan())
        self.assertEqual(len(p["rows"]), 620)
        for split, count in [("train",360),("validation",120),("test",140)]:
            self.assertEqual(sum(r["split"] == split for r in p["rows"]), count)
        self.assertTrue(all(r["split"] == "test" for r in p["rows"] if r["source"] == "Veo"))
        self.assertEqual(plan(), plan())

    def test_cross_split_content_and_group_leakage_are_rejected(self):
        p = plan()
        held = next(r for r in p["rows"] if r["split"] == "test")
        held["sha256"] = p["rows"][0]["sha256"]
        with self.assertRaisesRegex(ValueError, "Identical content"):
            validate(p)
        p = plan()
        p["rows"][0]["split"] = "test"
        with self.assertRaisesRegex(ValueError, "crosses splits"):
            validate(p)

    def test_cached_training_does_not_read_test_features(self):
        p = plan()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "features").mkdir()
            (root / "plan.json").write_text(json.dumps(p))
            for row in p["rows"]:
                if row["split"] != "train":
                    continue
                np.savez(root / "features" / (key(row)+".npz"), source_file=row["file"],
                         video_sha256=row["sha256"], feature_version=FEATURE_VERSION,
                         feature=np.ones(1024), augmented=np.ones(1024))
            rows, x, _, y = load_features(root / "plan.json", {"train"})
            self.assertEqual(x.shape, (360,1024))
            self.assertEqual(int(y.sum()), 300)

    def test_validation_threshold_is_strictly_above_real_scores(self):
        scores = np.array([-.3, .8, .8, .9, 1.2])
        labels = np.array([0,0,1,1,1])
        t = validation_threshold(scores, labels)
        self.assertGreater(t, .8)
        self.assertEqual(metrics(labels, scores >= t)["real_false_flags"], 0)
        self.assertEqual(metrics(labels, scores >= t)["ai_missed"], 1)

    def test_metrics_count_misses_and_false_flags_separately(self):
        m = metrics([1,1,0,0], [True,False,True,False])
        self.assertEqual((m["ai_missed"],m["real_false_flags"]),(1,1))
        self.assertEqual(m["balanced_accuracy"], .5)
        # Zero false flags in 20 clips still allows a material population rate.
        self.assertGreater(wilson(0,20)[1], .15)

    def test_training_and_runtime_linear_scores_match(self):
        weights = np.linspace(-1,1,1024)
        x = np.ones((3,1024))
        model = dict(feature_version=FEATURE_VERSION,coefficients=weights.tolist(),intercept=.4)
        np.testing.assert_allclose(linear_scores(model,x), x @ weights + .4)

    def test_clip_pooling_is_finite_unit_length(self):
        f = clip_feature(np.arange(6*1024).reshape(6,1024))
        self.assertAlmostEqual(float(np.linalg.norm(f)), 1, places=6)
        with self.assertRaises(ValueError):
            clip_feature(np.full((6,1024),np.nan))

    def test_baseline_receives_exact_same_captured_pixels(self):
        import io
        from PIL import Image
        image = Image.fromarray(np.random.default_rng(2).integers(0,256,(200,160,3),dtype=np.uint8))
        captured = capture_image(image)
        baseline = Image.open(io.BytesIO(captured.info["capture_jpeg"])).convert("RGB")
        np.testing.assert_array_equal(np.asarray(captured),np.asarray(baseline))

    def test_exports_group_recaptures_and_include_motion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for i,schema in enumerate((1,2)):
                n = 6 if schema == 1 else 16
                sample = dict(schema=schema,label="real",source=f"https://www.youtube.com/shorts/abc?tracking={i}",
                              frames=[dict(data=f"fixture-{i}-{j}") for j in range(n)])
                (root/f"{i}.json").write_text(json.dumps(sample))
            grouped = samples(root)
            self.assertEqual(len(grouped),1)
            captures = next(iter(grouped.values()))
            self.assertEqual(len(captures),2)
            self.assertEqual(captures[1][1]["selected_indices"],[0,3,6,9,12,15])
            sample["label"] = "ai"
            (root/"1.json").write_text(json.dumps(sample))
            with self.assertRaisesRegex(ValueError,"conflicting labels"):
                samples(root)


if __name__ == "__main__":
    unittest.main()
