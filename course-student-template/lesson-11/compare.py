"""Train two representations on the same SMS split and compare aligned results."""
from pathlib import Path
import argparse
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.text_representations import run


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def compare(first_config, second_config, output):
    configs = [read_json(first_config), read_json(second_config)]
    # Representation settings may differ; keep the learning and action protocol fixed.
    defaults = dict(lr=1., steps=400, l2=.001, spam_weight=1., seed=0,
                    initial_scale=0., threshold=.5, capacity_fraction=1.)
    for key, default in defaults.items():
        if configs[0].get(key, default) != configs[1].get(key, default):
            raise ValueError(f"两方案的 {key} 不同；本课示范先保持训练与复核设置一致")
    if configs[0].get("representation", "manual") == configs[1].get("representation", "manual"):
        raise ValueError("请选择两种不同表示：manual、bow、tfidf")
    if output.exists():
        raise FileExistsError("输出目录已存在，请选新目录，保留原结果")
    output.mkdir(parents=True)
    summaries = []
    for name, config in zip(("first", "second"), configs):
        run(config, output / name)
        summaries.append(read_json(output / name / "summary.json"))
    for key in ("train_ids_sha256", "dev_ids_sha256", "train_data_sha256", "dev_data_sha256"):
        if summaries[0][key] != summaries[1][key]:
            raise ValueError("两方案的数据或划分不一致")
    rows = []
    for name, summary in zip(("first", "second"), summaries):
        m = summary["metrics"]
        rows.append(dict(scheme=name, representation=summary["config"]["representation"],
                         dimensions=summary["dimensions"], n=m["n"], reviewed=m["reviewed"],
                         tp=m["tp"], fp=m["fp"], fn=m["fn"], tn=m["tn"],
                         precision=m["precision"], recall=m["recall"], accuracy=m["accuracy"]))
    write_csv(output / "comparison.csv", rows)
    records = []
    for name in ("first", "second"):
        with (output / name / "records.csv").open(encoding="utf-8", newline="") as f:
            records.append({row["id"]: row for row in csv.DictReader(f)})
    if records[0].keys() != records[1].keys():
        raise ValueError("开发集ID不一致")
    pairs = []
    for rid in sorted(records[0]):
        a, b = records[0][rid], records[1][rid]
        if a["label"] != b["label"] or a["text_sha256"] != b["text_sha256"]:
            raise ValueError("同ID记录内容或标签不一致")
        pairs.append(dict(id=rid, label=a["label"], first_probability=a["probability"],
                          second_probability=b["probability"], first_action=a["action"],
                          second_action=b["action"], changed=int(a["action"] != b["action"])))
    write_csv(output / "paired_predictions.csv", pairs)
    print(json.dumps(dict(results=rows, changed_predictions=sum(r["changed"] for r in pairs)),
                     ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first-config", type=Path, default=ROOT / "lesson-11/config.json")
    parser.add_argument("--second-config", type=Path, default=ROOT / "lesson-11/tfidf-reference.json")
    parser.add_argument("--output", type=Path, default=ROOT / "lesson-11/artifacts/comparison")
    args = parser.parse_args()
    try:
        compare(args.first_config, args.second_config, args.output)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"比较未完成：{error}\n")


if __name__ == "__main__":
    main()
