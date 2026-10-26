"""Lesson13/14 entry: reuse established submission contract; preserve old work."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

def implementation():
 if (ROOT/'scripts/course_l12.py').exists():
  import course_l12 as core
  core.ACTIVE_LESSONS=(13,14)
 else:
  import course as core
 return core

def sync(destination):
 root=Path(destination).resolve()
 def git(*args):return subprocess.check_output(['git',*args],cwd=root)
 if Path(git('rev-parse','--show-toplevel').decode().strip()).resolve()!=root:raise ValueError('Use the existing student repository root')
 # Existing course-release remote must already be verified by the student.
 ref=git('rev-parse','course-release/main').decode().strip()
 info=json.loads(git('show',ref+':docs/LESSONS13_14_FILES.json'))
 compatible_updaters=info.get('compatible_existing_updater_sha256',[])
 if not isinstance(compatible_updaters,list) or any(not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h) for h in compatible_updaters):raise ValueError('Invalid compatible updater hashes')
 pending=[]
 for name,sha in info['files'].items():
  p=Path(name)
  if p.is_absolute() or '..' in p.parts:raise ValueError('Invalid release path')
  target=root/p
  if any(q.is_symlink() for q in [target,*target.parents] if q!=root and root in q.parents):raise ValueError('Symlink destination: '+name)
  if any(q.exists() and not q.is_dir() for q in target.parents if q!=root and root in q.parents):raise ValueError('Destination parent is not a directory: '+name)
  # Skip a whole existing lesson so personal text/results never get patched.
  if p.parts[0] in ['lesson-13','lesson-14'] and (root/p.parts[0]).exists():continue
  b=git('show',ref+':'+name)
  if hashlib.sha256(b).hexdigest()!=sha:raise ValueError('Release identity mismatch: '+name)
  if target.exists():
   existing=target.read_bytes()
   # The documented temporary helper can preserve this exact earlier updater.
   compatible=name=='scripts/course_l1314.py' and hashlib.sha256(existing).hexdigest() in compatible_updaters
   if existing!=b and not compatible:raise ValueError('Existing shared file differs; preserve and resolve before updating: '+name)
  else:pending.append((target,b))
 for name,expected in info['required_existing'].items():
  accepted=expected if name=='scripts/course.py' and isinstance(expected,list) else [expected]
  if not accepted or any(not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h) for h in accepted):raise ValueError('Invalid prerequisite hashes: '+name)
  p=root/name
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() not in accepted:raise ValueError('Prerequisite differs or missing: '+name)
 # Validate and prepare registration before writing any missing course files.
 active=root/'active_lessons.json';active_bytes=None
 if active.is_symlink() or (active.exists() and not active.is_file()):raise ValueError('active_lessons.json must be a regular file')
 if active.exists():
  d=json.loads(active.read_text())
  a=d.get('active_student_lessons') if isinstance(d,dict) else None
  if not isinstance(a,list) or not a or any(not isinstance(n,str) or not re.fullmatch(r'lesson-(0[1-9]|[12][0-9]|3[0-2])',n) for n in a) or len(a)!=len(set(a)):raise ValueError('Invalid active_student_lessons')
  added=False
  for n in [13,14]:
   name=f'lesson-{n}'
   if ((root/name).is_dir() or any(p.parts[len(root.parts)]==name for p,b in pending)) and name not in a:a.append(name);added=True
  if added:active_bytes=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
 for p,b in pending:
  p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(b)
 if active_bytes is not None:active.write_bytes(active_bytes)
 print(f'Added {len(pending)} missing files. Existing lessons/reports and workflows unchanged. See docs/LESSONS13_14_UPDATE.md for tag routing.')

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['start','run','check','ci','sync']);p.add_argument('lesson',nargs='?');p.add_argument('--destination',type=Path);a=p.parse_args()
 if a.action=='sync':sync(a.destination or ROOT);return
 core=implementation();name=None
 if a.lesson is not None:
  name=core.lesson_name(a.lesson)
  if name not in ['lesson-13','lesson-14']:raise ValueError('Use the original entry for other lessons')
 if a.action=='ci':
  if name:core.check(ROOT,name);core.reproduce(ROOT,name)
  else:core.ci(ROOT,os.environ.get('GITHUB_REF',''))
 elif name is None:p.error('Provide lesson 13 or 14')
 else:getattr(core,a.action)(ROOT,name)
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,subprocess.CalledProcessError) as e:print(str(e),file=sys.stderr);sys.exit(1)
