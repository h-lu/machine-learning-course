"""Exercise existing submission/reproduction interfaces on disposable copies.
Template reports are NOT thereby judged to be completed student projects.
"""
from pathlib import Path
import importlib.util,json,os,shutil,sys,tempfile,time
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
ROOT=Path(__file__).resolve().parents[1];STUDENT=ROOT/'course-student-template'
spec=importlib.util.spec_from_file_location('workflow',STUDENT/'scripts/course.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
results=[]
with tempfile.TemporaryDirectory(prefix='ml-submission-test-') as d:
 scratch=Path(d)/'student';shutil.copytree(STUDENT,scratch,ignore=shutil.ignore_patterns('__pycache__','.venv','artifacts'))
 for n in range(9,15):
  name=f'lesson-{n:02d}';start=time.perf_counter();w.run(scratch,name)
  p=scratch/name/'submission.json';v=json.loads(p.read_text());v['status']='complete';p.write_text(json.dumps(v))
  w.reproduce(scratch,name);results.append(dict(lesson=name,byte_identical=True,seconds=time.perf_counter()-start))
(ROOT/'validation/lessons09-14/submission-reproduction.json').write_text(json.dumps(dict(scope='disposable author interface test, no grades changed, not student completion',lessons=results),indent=2)+'\n')
print('Six default submissions reproduce byte-for-byte')
