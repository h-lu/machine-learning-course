"""Verify and restore exact archived teaching bytes from this repository's history."""
from pathlib import Path
import argparse,hashlib,json,subprocess
ARCHIVE=Path(__file__).resolve().parent
REPO=ARCHIVE.parents[1]
def relative(s):
 p=Path(s)
 if not s or p.is_absolute() or '..' in p.parts:raise ValueError('unsafe archive path')
 return p
def contents(row):
 if 'payload_relative_path' in row:return (ARCHIVE/relative(row['payload_relative_path'])).read_bytes()
 ref=row['git_commit']
 if len(ref)!=40 or any(c not in '0123456789abcdef' for c in ref):raise ValueError('invalid immutable snapshot')
 return subprocess.check_output(['git','show',ref+':'+str(relative(row['git_path']))],cwd=REPO)
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);a=parser.parse_args()
 manifest=json.loads((ARCHIVE/'manifest.json').read_text());seen=set();data=[]
 for row in manifest['files']:
  name=str(relative(row['original_relative_path']))
  if name in seen:raise ValueError('duplicate path')
  seen.add(name);b=contents(row)
  if len(b)!=row['bytes'] or hashlib.sha256(b).hexdigest()!=row['sha256']:raise ValueError('archive bytes differ: '+name)
  data.append((row,b))
 if a.output:
  out=a.output.resolve()
  if out==REPO or out.is_relative_to(REPO):raise ValueError('restore outside the active repository')
  if a.output.is_symlink() or out.exists() and (not out.is_dir() or any(out.iterdir())):raise ValueError('restore into a new empty directory')
  out.mkdir(parents=True,exist_ok=True)
  for d in manifest['directories']:(out/relative(d['original_relative_path'])).mkdir(parents=True,exist_ok=True)
  for row,b in data:
   p=out/relative(row['original_relative_path']);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);p.chmod(row['mode'])
  for d in reversed(manifest['directories']):(out/relative(d['original_relative_path'])).chmod(d['mode'])
  assert {str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}==seen
  assert {str(p.relative_to(out)) for p in out.rglob('*') if p.is_dir()}=={d['original_relative_path'] for d in manifest['directories']}
  for row,b in data:
   p=out/row['original_relative_path'];assert p.read_bytes()==b and p.stat().st_mode&0o777==row['mode']
 print(json.dumps({'verified':True,'files':len(data),'bytes':sum(len(b) for r,b in data),'restored':bool(a.output),'source':'immutable Git history and exact payload bytes'},ensure_ascii=False))
if __name__=='__main__':main()
