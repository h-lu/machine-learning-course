"""Pinned, frozen, offline CPU encoder. No fitting and no network calls."""
from pathlib import Path
import hashlib,json,time
import numpy as np
from mlcourse.sms_course import DATA,digest,save_json
class Encoder:
    def __init__(self):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        self.folder=DATA/'encoder';self.manifest=json.loads((self.folder/'manifest.json').read_text())
        for record in self.manifest['files']:
            if digest(self.folder/record['file'])!=record['sha256']:raise ValueError('Encoder file hash mismatch: '+record['file'])
        self.tokenizer=Tokenizer.from_file(str(self.folder/'tokenizer.json'))
        self.tokenizer.enable_truncation(max_length=128)
        self.tokenizer.enable_padding(pad_id=0,pad_token='[PAD]')
        options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
        self.session=ort.InferenceSession(str(self.folder/self.manifest['backend']),sess_options=options,providers=['CPUExecutionProvider'])
    def encode(self,texts,batch_size=32):
        if not all(isinstance(t,str) for t in texts):raise ValueError('Texts must be strings')
        if batch_size<1:raise ValueError('Positive batch size required')
        if not texts:return np.empty((0,384),dtype=np.float32)
        result=[]
        for start in range(0,len(texts),batch_size):
            batch=self.tokenizer.encode_batch(texts[start:start+batch_size]);mask=np.array([b.attention_mask for b in batch],dtype=np.int64)
            candidates=dict(input_ids=np.array([b.ids for b in batch],dtype=np.int64),attention_mask=mask,token_type_ids=np.array([b.type_ids for b in batch],dtype=np.int64))
            h=self.session.run(None,{p.name:candidates[p.name] for p in self.session.get_inputs()})[0]
            if h.ndim!=3:raise ValueError('Expected token embeddings')
            v=(h*mask[:,:,None]).sum(1)/np.maximum(mask.sum(1,keepdims=True),1)
            v/=np.maximum(np.linalg.norm(v,axis=1,keepdims=True),1e-12);result.append(v.astype(np.float32))
        return np.concatenate(result)
def cache(rows,path,encoder):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);start=time.perf_counter();x=encoder.encode([r['text'] for r in rows]);np.save(path.with_suffix('.npy'),x,allow_pickle=False)
    meta=dict(encoder_manifest_sha256=digest(DATA/'encoder/manifest.json'),model=encoder.manifest['model'],revision=encoder.manifest['revision'],dimension=384,max_length=128,batch_size=32,pooling=encoder.manifest['pooling'],dtype='float32',provider='CPUExecutionProvider',threads=1,seconds=time.perf_counter()-start,split=rows[0]['split'],ids=[r['id'] for r in rows],text_sha256=[r['text_sha256'] for r in rows],vectors_sha256=digest(path.with_suffix('.npy')),fitted_on_sms=False)
    save_json(path.with_suffix('.json'),meta);return meta

def load_cache(rows,path):
    path=Path(path);meta=json.loads(path.with_suffix('.json').read_text())
    if meta['encoder_manifest_sha256']!=digest(DATA/'encoder/manifest.json') or meta['ids']!=[r['id'] for r in rows] or meta['text_sha256']!=[r['text_sha256'] for r in rows] or meta['vectors_sha256']!=digest(path.with_suffix('.npy')) or {r['split'] for r in rows}!={meta['split']}:raise ValueError('Cache identity mismatch; regenerate matching partition')
    manifest=json.loads((DATA/'encoder/manifest.json').read_text())
    if meta['dimension']!=384 or meta['max_length']!=128 or meta['model']!=manifest['model'] or meta['revision']!=manifest['revision'] or meta['pooling']!=manifest['pooling'] or meta['batch_size']!=32 or meta['dtype']!='float32':raise ValueError('Cache generation parameters mismatch')
    if any(hashlib.sha256(r['text'].encode()).hexdigest()!=r['text_sha256'] for r in rows):raise ValueError('Input text no longer matches its hash')
    x=np.load(path.with_suffix('.npy'),allow_pickle=False)
    if x.shape!=(len(rows),384) or x.dtype!=np.float32 or not np.isfinite(x).all():raise ValueError('Invalid cached matrix')
    return x
