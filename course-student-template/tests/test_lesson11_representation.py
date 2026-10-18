"""Independent calculations for lesson 11; no quiz or final-holdout answers."""
import copy
import csv
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

STUDENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDENT))
from mlcourse import sms_course as lesson10
from mlcourse import text_representations as representation


class RepresentationCalculations(unittest.TestCase):
    # This is a teaching fixture, not a subset of the SMS corpus.
    TRAIN = ["green tea", "green tea tea", "red coffee"]
    NAMES = ["coffee", "green", "red", "tea"]

    def fit(self, kind, **settings):
        return representation.fit_representation(self.TRAIN, kind=kind, min_df=1,
                                                 max_features=1200, **settings)

    def test_bow_counts_then_l2_normalization(self):
        rep = self.fit("bow", normalization="l2")
        self.assertEqual(rep["names"], self.NAMES)
        rows = representation.transform(["green tea tea"], rep)
        np.testing.assert_allclose(rows.to_dense(),
                                   [[0., 1 / math.sqrt(5), 0., 2 / math.sqrt(5)]])
        raw = self.fit("bow", normalization="none")
        np.testing.assert_allclose(representation.transform(["green tea tea"], raw).to_dense(),
                                   [[0., 1., 0., 2.]])

    def test_idf_uses_document_frequency_and_training_document_count(self):
        rep = self.fit("tfidf", normalization="none")
        rows = representation.transform(["green tea tea", "green coffee"], rep)
        rare = 1 + math.log(4 / 2)
        common = 1 + math.log(4 / 3)
        # "tea" appears three times but in only two training documents.
        np.testing.assert_allclose(rows.to_dense(),
                                   [[0., common, 0., 2 * common],
                                    [rare, common, 0., 0.]])
        normalized = self.fit("tfidf", normalization="l2")
        expected = [rare / math.hypot(rare, common),
                    common / math.hypot(rare, common), 0., 0.]
        np.testing.assert_allclose(
            representation.transform(["green coffee"], normalized).to_dense(), [expected])
        self.assertAlmostEqual(expected[0], .7959605416, places=9)
        self.assertAlmostEqual(expected[1], .6053485081, places=9)

    def test_empty_and_unknown_text_have_finite_zero_rows_without_refitting(self):
        for kind in ("bow", "tfidf"):
            with self.subTest(kind=kind):
                rep = self.fit(kind, normalization="l2")
                before = copy.deepcopy(rep)
                rows = representation.transform(["", "gold", "GOLD gold", "tea gold"], rep)
                self.assertEqual(rep, before)
                self.assertNotIn("gold", rep["names"])
                self.assertEqual(rows.shape, (4, 4))
                np.testing.assert_array_equal(rows.to_dense()[:3], np.zeros((3, 4)))
                np.testing.assert_allclose(rows.to_dense()[3], [0, 0, 0, 1])
                self.assertTrue(np.isfinite(rows.data).all())

    def test_vocabulary_is_fitted_before_development_texts_are_transformed(self):
        rep = self.fit("tfidf", normalization="none")
        before = json.dumps(rep, sort_keys=True)
        expected = representation.transform(["green coffee"], rep).to_dense().copy()
        representation.transform(["gold gold gold"] * 30 + ["coffee"] * 20, rep)
        self.assertEqual(json.dumps(rep, sort_keys=True), before)
        np.testing.assert_array_equal(
            representation.transform(["green coffee"], rep).to_dense(), expected)

    def test_min_df_and_feature_cap_bound_the_actual_feature_space(self):
        common = representation.fit_representation(self.TRAIN, kind="tfidf", min_df=2,
                                                    max_features=1200, normalization="none")
        self.assertEqual(common["names"], ["green", "tea"])
        np.testing.assert_allclose(
            representation.transform(["red coffee green"], common).to_dense(),
            [[1 + math.log(4 / 3), 0.]])
        capped = representation.fit_representation(self.TRAIN, kind="bow", min_df=1,
                                                    max_features=2, normalization="none")
        self.assertEqual(len(capped["names"]), 2)
        self.assertEqual(capped["names"], sorted(capped["names"]))
        self.assertEqual(representation.transform(self.TRAIN, capped).shape, (3, 2))

    def test_words_only_and_words_numbers_are_distinct_explicit_choices(self):
        texts = ["Tea 123", "123 green", "green tea"]
        settings = dict(kind="bow", min_df=1, max_features=20, normalization="none")
        with_numbers = representation.fit_representation(texts, token_pattern="words_numbers", **settings)
        words = representation.fit_representation(texts, token_pattern="words", **settings)
        self.assertIn("123", with_numbers["names"])
        self.assertNotIn("123", words["names"])
        row = representation.transform(["TEA 123 tea!!!"], with_numbers).to_dense()[0]
        self.assertEqual(row[with_numbers["names"].index("tea")], 2)
        self.assertEqual(row[with_numbers["names"].index("123")], 1)

    def test_manual_representation_preserves_the_lesson10_computation(self):
        texts = ["Free tea!", "red 123", "https://example.test"]
        baseline = lesson10.fit_representation(texts, "manual")
        candidate = representation.fit_representation(texts, kind="manual")
        for key in baseline:
            self.assertEqual(candidate[key], baseline[key])
        np.testing.assert_array_equal(representation.transform(["FREE 456!!", ""], candidate),
                                      lesson10.transform(["FREE 456!!", ""], baseline))

    def test_sparse_rows_reconstruct_and_multiply_without_a_dense_matrix(self):
        rep = self.fit("bow", normalization="none")
        rows = representation.transform(["green tea tea", "coffee", "gold", "red tea"], rep)
        expected = np.array([[0., 1., 0., 2.], [1., 0., 0., 0.],
                             [0., 0., 0., 0.], [0., 0., 1., 1.]])
        self.assertNotIsInstance(rows, np.ndarray)
        self.assertEqual(rows.shape, expected.shape)
        self.assertEqual(len(rows.data), 5)
        self.assertEqual(len(rows.indices), 5)
        self.assertEqual(len(rows.indptr), len(expected) + 1)
        for index, dense in enumerate(expected):
            columns, values = rows.row(index)
            self.assertEqual(len(columns), np.count_nonzero(dense))
            np.testing.assert_array_equal(values, dense[columns])
        w = np.array([.4, -.2, .7, 1.3])
        err = np.array([.1, -.3, .6, -.4])
        with patch.object(type(rows), "to_dense", side_effect=AssertionError("sparse operation densified")):
            np.testing.assert_allclose(rows.matvec(w), expected @ w)
            np.testing.assert_allclose(rows.transpose_matvec(err), expected.T @ err)
        with self.assertRaises(ValueError):
            rows.to_dense(max_cells=expected.size - 1)

    def test_trace_explains_count_df_idf_and_both_weighting_stages(self):
        rep = self.fit("tfidf", normalization="l2")
        trace = representation.explain_text("green tea tea gold", rep)
        self.assertEqual(trace["tokens"], ["green", "tea", "tea", "gold"])
        self.assertEqual(trace["unknown_tokens"], [{"token": "gold", "count": 1}])
        common = 1 + math.log(4 / 3)
        self.assertAlmostEqual(trace["row_norm"], common * math.sqrt(5))
        features = {row["name"]: row for row in trace["features"]}
        self.assertEqual(set(features), {"green", "tea"})
        for word, count in (("green", 1), ("tea", 2)):
            feature = features[word]
            self.assertEqual(feature["index"], self.NAMES.index(word))
            self.assertEqual(feature["count"], count)
            self.assertEqual(feature["df"], 2)
            self.assertAlmostEqual(feature["idf"], common)
            self.assertAlmostEqual(feature["weighted_value"], count * common)
            self.assertAlmostEqual(feature["value"], count / math.sqrt(5))


class SparseTrainingCalculations(unittest.TestCase):
    def setUp(self):
        self.texts = ["green tea", "green tea tea", "red coffee", "coffee tea"]
        self.y = np.array([0., 1., 1., 0.])
        self.dev_texts = ["green coffee", "tea red"]
        self.dev_y = np.array([1., 0.])
        self.settings = dict(lr=.17, steps=17, l2=.031, spam_weight=2.5,
                             seed=7, initial_scale=.04)

    def matrices(self, kind="tfidf"):
        rep = representation.fit_representation(self.texts, kind=kind, min_df=1,
                                                max_features=20, normalization="l2")
        return (representation.transform(self.texts, rep),
                representation.transform(self.dev_texts, rep))

    def test_sparse_training_matches_existing_dense_logistic_update_and_curve(self):
        for kind in ("bow", "tfidf"):
            with self.subTest(kind=kind):
                x, dev_x = self.matrices(kind)
                expected = lesson10.fit(x.to_dense(), self.y, dev_x.to_dense(), self.dev_y,
                                        **self.settings)
                with patch.object(type(x), "to_dense", side_effect=AssertionError("fit densified")):
                    actual = representation.fit_classifier(x, self.y, dev_x, self.dev_y,
                                                           **self.settings)
                np.testing.assert_allclose(actual[0], expected[0], atol=1e-13, rtol=1e-13)
                self.assertAlmostEqual(actual[1], expected[1], places=13)
                self.assertEqual(len(actual[2]), self.settings["steps"] + 1)
                for observed, wanted in zip(actual[2], expected[2]):
                    self.assertEqual(set(observed), set(wanted))
                    for name in wanted:
                        self.assertAlmostEqual(observed[name], wanted[name], places=12)
                for name in ("gradient_weights", "weights_before", "weights_after"):
                    np.testing.assert_allclose(actual[3][name], expected[3][name], atol=1e-13)
                for name in ("bias_after", "gradient_bias", "denominator", "objective_after"):
                    self.assertAlmostEqual(actual[3][name], expected[3][name], places=13)

    def test_development_labels_monitor_but_do_not_determine_training(self):
        x, dev_x = self.matrices()
        first = representation.fit_classifier(x, self.y, dev_x, self.dev_y, **self.settings)
        changed = representation.fit_classifier(x, self.y, dev_x, 1 - self.dev_y,
                                                 **self.settings)
        np.testing.assert_array_equal(first[0], changed[0])
        self.assertEqual(first[1], changed[1])
        self.assertEqual(first[3], changed[3])
        self.assertEqual([row["train_objective"] for row in first[2]],
                         [row["train_objective"] for row in changed[2]])
        self.assertNotEqual(first[2][-1]["dev_bce"], changed[2][-1]["dev_bce"])

    def test_first_update_has_the_weighted_full_batch_denominator_and_unpenalized_bias(self):
        rep = representation.fit_representation(["tea", "tea coffee", "coffee"], kind="bow",
                                                min_df=1, max_features=20, normalization="none")
        x = representation.transform(["tea", "tea coffee", "coffee"], rep)
        y = np.array([0., 1., 1.])
        w, bias, _, update = representation.fit_classifier(
            x, y, x, y, lr=.2, steps=1, l2=.5, spam_weight=3., seed=4, initial_scale=0.)
        # Columns coffee, tea; weights [1,3,3] give errors [.5,-1.5,-1.5]/7.
        expected_gradient = np.array([-3 / 7, -1 / 7])
        expected_bias_gradient = -2.5 / 7
        np.testing.assert_allclose(update["gradient_weights"], expected_gradient)
        self.assertAlmostEqual(update["gradient_bias"], expected_bias_gradient)
        self.assertEqual(update["denominator"], 7)
        np.testing.assert_allclose(w, -.2 * expected_gradient)
        self.assertAlmostEqual(bias, -.2 * expected_bias_gradient)

    def test_sparse_gradient_matches_finite_differences_at_nonzero_intercept(self):
        x, _ = self.matrices()
        dense = x.to_dense()
        weights = np.array([.3, -.2, .5, -.4])
        bias, l2 = .6, .27
        sample_weights = np.array([1., 3., 3., 1.])

        def independently_evaluated_objective(w, b):
            logits = dense @ w + b
            losses = np.logaddexp(0, logits) - self.y * logits
            return float(sum(sample_weights * losses) / sum(sample_weights)
                         + l2 * sum(w * w) / 2)

        objective, gradient, bias_gradient = representation.loss_gradient(
            x, self.y, weights, bias, l2, sample_weights)
        self.assertAlmostEqual(objective, independently_evaluated_objective(weights, bias))
        epsilon = 1e-6
        for index in range(len(weights)):
            direction = np.eye(len(weights))[index] * epsilon
            numerical = (independently_evaluated_objective(weights + direction, bias)
                         - independently_evaluated_objective(weights - direction, bias)) / (2 * epsilon)
            self.assertAlmostEqual(gradient[index], numerical, places=8)
        numerical_bias = (independently_evaluated_objective(weights, bias + epsilon)
                          - independently_evaluated_objective(weights, bias - epsilon)) / (2 * epsilon)
        self.assertAlmostEqual(bias_gradient, numerical_bias, places=8)


class SMSRunEvidence(unittest.TestCase):
    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="lesson11-preserve-") as temporary:
            output = Path(temporary) / "already-recorded"
            output.mkdir()
            marker = output / "my-result.txt"
            marker.write_bytes(b"keep this original evidence\n")
            with self.assertRaises(ValueError):
                representation.run({"steps": 1}, output)
            self.assertEqual(list(output.iterdir()), [marker])
            self.assertEqual(marker.read_bytes(), b"keep this original evidence\n")

    def test_default_run_is_one_manual_representation_with_lesson10_training_settings(self):
        with tempfile.TemporaryDirectory(prefix="lesson11-default-") as temporary:
            output = Path(temporary) / "manual-only"
            with patch.object(representation, "fit_classifier", wraps=representation.fit_classifier) as fit:
                representation.run({"steps": 3}, output)
            fit.assert_called_once()
            config = json.loads((output / "config.json").read_text())
            summary = json.loads((output / "summary.json").read_text())
            rep = json.loads((output / "representation.json").read_text())
            self.assertEqual(config["representation"], "manual")
            self.assertEqual(rep["kind"], "manual")
            self.assertEqual(summary["dimensions"], 6)
            for key, expected in dict(lr=1., l2=.001, spam_weight=1., seed=0,
                                      initial_scale=0., threshold=.5, capacity_fraction=1.).items():
                self.assertEqual(config[key], expected)
            self.assertEqual({path.name for path in output.iterdir()},
                             {"config.json", "representation.json", "summary.json", "model.npz",
                              "first_update.json", "prediction_trace.json", "curve.csv", "records.csv"})
            train, dev = lesson10.load_rows("train"), lesson10.load_rows("dev")
            x = lesson10.transform([row["text"] for row in train], rep)
            dev_x = lesson10.transform([row["text"] for row in dev], rep)
            y = np.array([row["label"] == "spam" for row in train], dtype=float)
            dev_y = np.array([row["label"] == "spam" for row in dev], dtype=float)
            expected_w, expected_b, _, _ = lesson10.fit(x, y, dev_x, dev_y, lr=1., steps=3,
                                                        l2=.001, spam_weight=1., seed=0,
                                                        initial_scale=0.)
            with np.load(output / "model.npz") as model:
                np.testing.assert_array_equal(model["w"], expected_w)
                self.assertEqual(float(model["b"]), expected_b)

    def test_real_sms_sparse_run_trace_matches_train_only_idf_and_saved_prediction(self):
        original_open = Path.open
        opened = []

        def development_only(path, *args, **kwargs):
            if path.parent == lesson10.DATA:
                opened.append(path.name)
                if path.name not in {"train.csv", "dev.csv", "provenance.json", "split_manifest.csv"}:
                    raise AssertionError("Lesson 11 opened an undeclared data input: " + path.name)
            return original_open(path, *args, **kwargs)

        with tempfile.TemporaryDirectory(prefix="lesson11-real-sms-") as temporary:
            output = Path(temporary) / "one-representation"
            config = dict(representation="tfidf", min_df=2, max_features=240,
                          token_pattern="words_numbers", normalization="l2", lr=1.,
                          steps=30, l2=.001, spam_weight=1., seed=0, initial_scale=0.,
                          threshold=.5, capacity_fraction=1.)
            with patch.object(Path, "open", development_only):
                result = representation.run(config, output)
            self.assertIn("train.csv", opened)
            self.assertIn("dev.csv", opened)
            summary = json.loads((output / "summary.json").read_text())
            saved_config = json.loads((output / "config.json").read_text())
            rep = json.loads((output / "representation.json").read_text())
            self.assertFalse(summary["final_test_opened"])
            self.assertEqual(summary["partition"], "dev")
            self.assertEqual(saved_config, dict(config, trace_id=None))
            self.assertEqual(result["dimensions"], len(rep["names"]))
            self.assertLessEqual(summary["dimensions"], 240)
            self.assertGreater(summary["training_rows"], 3000)
            self.assertEqual(saved_config["lr"], 1.)
            self.assertEqual(saved_config["steps"], 30)
            self.assertEqual(saved_config["l2"], .001)
            self.assertEqual(saved_config["spam_weight"], 1.)
            with (output / "curve.csv").open(newline="") as stream:
                curve = list(csv.DictReader(stream))
            self.assertEqual([int(row["step"]) for row in curve], list(range(31)))
            self.assertTrue(all(math.isfinite(float(row["train_objective"])) for row in curve))
            with (output / "records.csv").open(newline="") as stream:
                records = list(csv.DictReader(stream))
            train, dev = lesson10.load_rows("train"), lesson10.load_rows("dev")
            self.assertEqual({row["id"] for row in records}, {row["id"] for row in dev})
            self.assertEqual(len(records), len(dev))
            x = representation.transform([row["text"] for row in train], rep)
            dx = representation.transform([row["text"] for row in dev], rep)
            self.assertLess(len(x.data), x.shape[0] * x.shape[1] // 4)
            with np.load(output / "model.npz") as model:
                probability = lesson10.sigmoid(dx.matvec(model["w"]) + float(model["b"]))
            np.testing.assert_allclose([float(row["probability"]) for row in records], probability)
            # Independently count document frequency from train, then explain one
            # real nonempty dev row. No dev labels enter this calculation.
            trace = json.loads((output / "prediction_trace.json").read_text())
            chosen = next(row for row in dev if row["id"] == trace["id"])
            self.assertEqual(trace["text"], chosen["text"])
            self.assertEqual(trace["text_sha256"], chosen["text_sha256"])
            self.assertEqual(trace["partition"], "dev")
            train_sets = [set(lesson10.tokens(row["text"])) for row in train]
            counts = lesson10.tokens(chosen["text"])
            for feature in trace["features"]:
                name = feature["name"]
                df = sum(name in tokens for tokens in train_sets)
                idf = 1 + math.log((1 + len(train)) / (1 + df))
                self.assertEqual(feature["df"], df)
                self.assertEqual(feature["count"], counts.count(name))
                self.assertAlmostEqual(feature["idf"], idf)
                self.assertAlmostEqual(feature["weighted_value"], counts.count(name) * idf)
            weighted = np.array([feature["weighted_value"] for feature in trace["features"]])
            self.assertAlmostEqual(trace["row_norm"], float(np.linalg.norm(weighted)))
            np.testing.assert_allclose([feature["value"] for feature in trace["features"]],
                                       weighted / np.linalg.norm(weighted))
            self.assertAlmostEqual(sum(feature["contribution"] for feature in trace["features"])
                                   + trace["intercept"], trace["logit"])
            self.assertAlmostEqual(float(lesson10.sigmoid(trace["logit"])), trace["probability"])
            for feature in trace["features"]:
                self.assertAlmostEqual(feature["contribution"], feature["weight"] * feature["value"])


if __name__ == "__main__":
    unittest.main()
