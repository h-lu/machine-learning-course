"""Teacher-only finite comparison and independent output checks, not a student solution."""
from pathlib import Path
from collections import Counter
import argparse
import json
import math
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "course-student-template"))
from mlcourse import sms_course
from mlcourse.text_representations import run, tokenize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "validation/lesson11-20261018/teacher-reference")
    args = parser.parse_args()
    output = args.output
    if output.exists() and any(output.iterdir()):
        parser.error("Use a new output directory; preserve older reference evidence")
    config = json.loads((ROOT / "course-student-template/lesson-11/config.json").read_text())
    train, dev = sms_course.load_rows("train"), sms_course.load_rows("dev")
    summaries, checks = {}, {}
    for kind in ("manual", "bow", "tfidf"):
        selected = dict(config, representation=kind)
        summaries[kind] = run(selected, output / kind)
        trace = json.loads((output / kind / "prediction_trace.json").read_text())
        rep = json.loads((output / kind / "representation.json").read_text())
        actual = next(row for row in dev if row["id"] == trace["id"])
        assert actual["text"] == trace["text"] and actual["text_sha256"] == trace["text_sha256"]
        # Recompute saved contributions from the model and a fresh one-record
        # count, without using explain_text or the transform implementation.
        model = np.load(output / kind / "model.npz")
        if kind == "manual":
            t = actual["text"]
            raw = [len(t), sum(c.isdigit() for c in t), t.count("!"), len(sms_course.tokens(t)), int("free" in sms_course.tokens(t)), int(bool(__import__("re").search(r"https?://|www\.", t.lower())))]
            vector = (np.asarray(raw) - np.asarray(rep["mean"])) / np.asarray(rep["scale"])
        else:
            counts = Counter(tokenize(actual["text"], rep["token_pattern"]))
            vector = np.asarray([counts[word] for word in rep["names"]], dtype=float)
            for item in trace["features"]:
                df = sum(item["name"] in set(tokenize(row["text"], rep["token_pattern"])) for row in train)
                expected_idf = math.log((1 + len(train)) / (1 + df)) + 1
                assert item["count"] == counts[item["name"]] and item["df"] == df
                assert math.isclose(item["idf"], expected_idf, rel_tol=1e-14)
            if kind == "tfidf":
                vector *= np.asarray(rep["idf"])
            if rep["normalization"] == "l2" and np.linalg.norm(vector):
                vector /= np.linalg.norm(vector)
        logit = float(vector @ model["w"] + model["b"])
        probability = 1 / (1 + math.exp(-logit))
        assert math.isclose(logit, trace["logit"], abs_tol=1e-11)
        assert math.isclose(probability, trace["probability"], abs_tol=1e-12)
        assert math.isclose(sum(x["contribution"] for x in trace["features"]) + trace["intercept"], logit, abs_tol=1e-11)
        checks[kind] = {"actual_dev_trace_independently_recomputed": True, "trace_id": trace["id"], "token_sequence_length": len(trace["tokens"]), "nonzero_or_manual_features": len(trace["features"])}
    common = ("lr", "steps", "l2", "spam_weight", "seed", "initial_scale", "threshold", "capacity_fraction")
    for key in common:
        assert len({summary["config"][key] for summary in summaries.values()}) == 1
    for key in ("train_ids_sha256", "dev_ids_sha256", "train_data_sha256", "dev_data_sha256", "data_manifest_sha256"):
        assert len({summary[key] for summary in summaries.values()}) == 1
    report = {"scope": "fixed protocol demonstration, no model or setting selected as optimal", "common_protocol": {key: summaries["manual"]["config"][key] for key in common}, "summaries": summaries, "checks": checks, "same_ids_data_and_protocol": True, "finalholdout_opened": False, "grading_or_bank_or_session_changes": False}
    sms_course.save_json(output / "reference-checks.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
