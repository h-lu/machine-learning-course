"""One baseline only. Use your own comparison and diagnosis for the open task."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mlcourse.sms_course import run
p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=Path(__file__).with_name('config.json'));p.add_argument('--output',type=Path,default=Path(__file__).parent/'artifacts/baseline');a=p.parse_args()
print(json.dumps(run(json.loads(a.config.read_text()),a.output),ensure_ascii=False,indent=2))
