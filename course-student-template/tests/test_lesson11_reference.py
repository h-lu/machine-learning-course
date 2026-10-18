"""Keep the documented single real-SMS walkthrough executable and auditable."""
from collections import Counter
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

STUDENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDENT))
from mlcourse import sms_course
from mlcourse.text_representations import explain_text, fit_representation, run, tokenize, transform


class DocumentedReference(unittest.TestCase):
    def test_supplied_single_TFIDF_configuration_reproduces_the_real_walkthrough(self):
        config = json.loads((STUDENT / "lesson-11/tfidf-reference.json").read_text())
        self.assertEqual(config["representation"], "tfidf")
        self.assertEqual((config["min_df"], config["max_features"], config["steps"]), (2, 1200, 400))
        self.assertEqual((config["threshold"], config["capacity_fraction"], config["trace_id"]), (.5, 1., "sms-00004"))
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "reference"
            run(config, out)
            trace = json.loads((out / "prediction_trace.json").read_text())
            rep = json.loads((out / "representation.json").read_text())
            self.assertEqual(trace["id"], "sms-00004")
            self.assertEqual(trace["text"], "U dun say so early hor... U c already then say...")
            self.assertEqual(trace["tokens"], ["u", "dun", "say", "so", "early", "hor", "u", "c", "already", "then", "say"])
            self.assertEqual(trace["unknown_tokens"], [{"token": "hor", "count": 1}])
            by_name = {item["name"]: item for item in trace["features"]}
            say = by_name["say"]
            self.assertEqual((say["index"], say["count"], say["df"]), (891, 2, 56))
            self.assertEqual(rep["names"][891], "say")
            train = sms_course.load_rows("train")
            df = sum("say" in set(tokenize(row["text"])) for row in train)
            self.assertEqual(df, 56)
            self.assertAlmostEqual(say["idf"], math.log(3878 / 57) + 1, places=13)
            self.assertAlmostEqual(say["value"], say["count"] * say["idf"] / trace["row_norm"], places=13)
            self.assertAlmostEqual(trace["row_norm"], 17.150729461164808, places=10)
            self.assertAlmostEqual(say["weight"], -.13080819760219256, places=10)
            score = math.fsum(item["value"] * item["weight"] for item in trace["features"]) + trace["intercept"]
            self.assertAlmostEqual(score, trace["logit"], places=12)
            self.assertAlmostEqual(score, -2.4582665228588008, places=10)
            self.assertAlmostEqual(1 / (1 + math.exp(-score)), trace["probability"], places=13)
            self.assertAlmostEqual(trace["probability"], .07883613213614646, places=11)
            self.assertEqual(trace["action"], 0)
            # Reconstruct one vector directly from counts and saved fitted data,
            # without invoking the representation transform or trace routines.
            counts = Counter(trace["tokens"])
            vector = np.asarray([counts[name] * idf for name, idf in zip(rep["names"], rep["idf"])])
            vector /= np.linalg.norm(vector)
            with np.load(out / "model.npz") as model:
                self.assertAlmostEqual(float(vector @ model["w"] + model["b"]), score, places=12)

    def test_failed_settings_and_unknown_inputs_preserve_explicit_boundaries(self):
        toy = ["green tea", "green tea tea", "red coffee"]
        for settings in ({"min_df": 0}, {"min_df": 4}, {"max_features": 0}, {"max_features": True}, {"token_pattern": "unsupported"}, {"normalization": "unsupported"}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                fit_representation(toy, kind="tfidf", **settings)
        with self.assertRaises(ValueError):
            fit_representation([], kind="tfidf")
        with self.assertRaises(ValueError):
            fit_representation(["", ""], kind="tfidf", min_df=1)
        rep = fit_representation(toy, kind="tfidf", min_df=1)
        matrix = transform(["", "gold"], rep)
        np.testing.assert_array_equal(matrix.to_dense(), np.zeros((2, 4)))
        self.assertEqual(explain_text("gold", rep)["unknown_tokens"], [{"token": "gold", "count": 1}])
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "invalid-trace"
            with self.assertRaisesRegex(ValueError, "actual dev record"):
                run({"representation": "tfidf", "steps": 1, "trace_id": "not-a-dev-id"}, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
