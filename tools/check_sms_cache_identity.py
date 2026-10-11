"""Independent mutation tests on disposable cache copies, never on shipped resources."""
from pathlib import Path
import json,shutil,sys,tempfile
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'course-student-template'))
from mlcourse.sms_course import DATA,load_rows,save_json
from mlcourse.sms_encoder import load_cache
if __name__=='__main__':
 rows=load_rows('dev');checks=[]
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'dev'
  for ext in ('.json','.npy'):shutil.copyfile((DATA/'cache/dev').with_suffix(ext),p.with_suffix(ext))
  original=json.loads(p.with_suffix('.json').read_text())
  for field,value in [('revision','wrong'),('dimension',42),('max_length',64),('pooling','wrong'),('vectors_sha256','wrong'),('split','train')]:
   mutated=dict(original);mutated[field]=value;save_json(p.with_suffix('.json'),mutated)
   try:load_cache(rows,p)
   except ValueError:checks.append(field)
   else:raise AssertionError(field+' mutation accepted')
  save_json(p.with_suffix('.json'),original)
  altered=[dict(r) for r in rows];altered[0]['text']='different bytes'
  try:load_cache(altered,p)
  except ValueError:checks.append('text bytes with stale digest')
  else:raise AssertionError('changed input accepted')
  x=load_cache(rows,p)
 save_json(R/'validation/lessons09-14/cache-mutations.json',dict(rejected=checks,original_cache_still_valid=True,shape=list(x.shape)))
 print(checks)
