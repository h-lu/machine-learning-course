from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mlcourse.transfer13 import predict_new
p=argparse.ArgumentParser();p.add_argument("--system",required=True);p.add_argument("--text",action="append",required=True);p.add_argument("--output",required=True);a=p.parse_args()
r=predict_new(a.text,a.system,a.output);print(r["probabilities"])
