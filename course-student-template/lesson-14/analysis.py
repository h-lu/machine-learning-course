from pathlib import Path
import argparse,json,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from mlcourse.transfer13 import run
p=argparse.ArgumentParser();p.add_argument("--config",type=Path,default=HERE/"config.json");p.add_argument("--output",type=Path,default=HERE/"artifacts/baseline");a=p.parse_args()
print(json.dumps(run(json.loads(a.config.read_text()),a.output),ensure_ascii=False,indent=2))
