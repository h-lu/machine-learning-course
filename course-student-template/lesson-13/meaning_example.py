"""Separate teaching example: actual frozen CPU encoding, no SMS labels."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mlcourse.sms_encoder import Encoder

TEXTS = [
    "The meeting has been postponed.",
    "The appointment will take place later.",
    "The cat is sleeping on the sofa.",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error("Output already exists; choose a new path to preserve evidence.")
    encoder = Encoder()
    vectors = encoder.encode(TEXTS)
    result = {
        "kind": "author-created English teaching examples; actual frozen-model CPU encoding, not labelled SMS evaluation",
        "texts": TEXTS,
        "model": encoder.manifest["model"],
        "revision": encoder.manifest["revision"],
        "dimension": 384,
        "cosine_similarity": (vectors @ vectors.T).tolist(),
        "vectors": vectors.tolist(),
        "backend": encoder.manifest["backend"],
        "pooling": encoder.manifest["pooling"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["cosine_similarity"], indent=2))


if __name__ == "__main__":
    main()
