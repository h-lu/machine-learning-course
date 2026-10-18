"""Run one chosen representation; build your own comparison and interpretation."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mlcourse.text_representations import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "artifacts/baseline")
    args = parser.parse_args()
    try:
        print(json.dumps(run(json.loads(args.config.read_text()), args.output), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f"运行未完成：{error}\n")


if __name__ == "__main__":
    main()
