"""Replay the author-simulated student sample in a new disposable student copy.
Does not upload, tag, score, or modify the real student template.
"""
from pathlib import Path
import argparse,shutil,subprocess,sys,os
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise ValueError('Choose a new output directory')
shutil.copytree(R/'course-student-template',a.output,ignore=shutil.ignore_patterns('__pycache__','artifacts','.venv'))
s=R/'validation/lesson09-student-walkthrough/sample/lesson-09'
for file in s.iterdir():
 if file.is_file():shutil.copyfile(file,a.output/'lesson-09'/file.name)
shutil.copytree(s/'results/my-study',a.output/'lesson-09/artifacts/my-study')
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
subprocess.run([sys.executable,'scripts/course.py','ci'],cwd=a.output,env=env,check=True)
print('Author sample reproduced byte-for-byte; this is not a student grade or human trial')
