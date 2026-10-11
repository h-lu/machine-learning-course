"""Teacher, before lesson 10. Deterministic label-blind duplicate grouping/split.
Run offline after placing the official ZIP in course-instructor/resources/sms/uci-sms.zip.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv, hashlib, json, re, unicodedata, zipfile
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'course-student-template/data/sms'
VAULT=ROOT/'course-instructor/resources/sms'
def sha(b): return hashlib.sha256(b).hexdigest()
def normal(t):
    t=unicodedata.normalize('NFKC',t).lower()
    t=re.sub(r'https?://\S+|www\.\S+', ' url ', t)
    t=re.sub(r'\d+', ' number ',t)
    return ' '.join(re.findall(r'[a-z]+',t))
def group_texts(texts):
    # Connected components of normalized equality OR char-trigram Jaccard >= .85.
    # Label independent. Short strings (<12 chars) use equality only.
    parent=list(range(len(texts))); normalized={}; grams=[]; index=defaultdict(list); edges=[]
    def find(i):
        while parent[i]!=i: parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(i,j,kind,score):
        parent[find(i)]=find(j);edges.append((i,j,kind,round(score,6)))
    for i,text in enumerate(texts):
        t=normal(text); g={t[k:k+3] for k in range(len(t)-2)}
        if t in normalized: union(i,normalized[t],'normalized_equal',1.)
        elif len(t)>=12:
            counts=Counter(j for gram in g for j in index[gram])
            for j,intersection in counts.items():
                score=intersection/(len(g)+len(grams[j])-intersection)
                if score>=.85: union(i,j,'char3_jaccard',score)
            for gram in g: index[gram].append(i)
        normalized.setdefault(t,i);grams.append(g)
    return [find(i) for i in range(len(texts))],edges

def write_csv(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    VAULT.mkdir(parents=True,exist_ok=True)
    archive=VAULT/'uci-sms.zip'
    with zipfile.ZipFile(archive) as z:
        raw=z.read('SMSSpamCollection');readme=z.read('readme')
    (VAULT/'SMSSpamCollection').write_bytes(raw);(VAULT/'original-readme.txt').write_bytes(readme)
    lines=raw.decode('utf-8').splitlines(); rows=[]
    for i,line in enumerate(lines):
        label,text=line.split('\t',1)
        if label not in ('ham','spam') or not text.strip(): raise ValueError(f'Bad source row {i+1}')
        rows.append(dict(id=f'sms-{i+1:05d}',label=label,text=text,text_sha256=sha(text.encode())))
    groups,edges=group_texts([r['text'] for r in rows]);members=defaultdict(list)
    for i,g in enumerate(groups): members[g].append(i)
    for members_i in members.values():
        gid=sha(min(rows[i]['text_sha256'] for i in members_i).encode())[:20]
        value=int(sha(('sms-v1-seed-20261011:'+gid).encode())[:12],16)/16**12
        split='train' if value<.70 else 'dev' if value<.85 else 'finalholdout'
        for i in members_i: rows[i].update(group_id=gid,split=split)
    for split in ('train','dev','finalholdout'):
        write_csv((VAULT if split=='finalholdout' else DATA)/f'{split}.csv',[r for r in rows if r['split']==split])
    manifest=[{k:r[k] for k in ('id','text_sha256','group_id','split')} for r in rows]
    write_csv(DATA/'split_manifest.csv',manifest)
    write_csv(VAULT/'group_edges.csv',[dict(left=rows[i]['id'],right=rows[j]['id'],rule=k,score=s) for i,j,k,s in edges])
    summary={'source_url':'https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip','doi':'10.24432/C5CC84','license':'CC BY 4.0 (UCI catalog); original readme retained', 'fetched':'2026-10-11','zip_sha256':sha(archive.read_bytes()),'raw_sha256':sha(raw),'rows':len(rows),'labels':dict(Counter(r['label'] for r in rows)),'groups':len(members),'edges':len(edges),'split_counts':dict(Counter(r['split'] for r in rows)),'seed':20261011,'rule':'NFKC/lower/URL and digits normalized; equality or char3 Jaccard>=0.85 (length>=12); transitive closure before group-hash 70/15/15 split; no labels used','limitations':'Heuristic near-duplicate rule is not semantic identity. No temporal order. Public research protocol, not access security.', 'file_sha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [DATA/'train.csv',DATA/'dev.csv',VAULT/'finalholdout.csv',DATA/'split_manifest.csv']}}
    (DATA/'provenance.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
