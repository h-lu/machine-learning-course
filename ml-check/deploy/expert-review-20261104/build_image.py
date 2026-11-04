"""在hblu-5090给现有镜像添加已验证题库层：python build_image.py BASE.tar OUTPUT.tar.gz。"""
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

release = Path(__file__).resolve().parent
bank = (release / 'lessons.json').read_bytes()
metadata = json.loads((release / 'manifest.json').read_text())
version = json.loads(bank)['version']
created = datetime.now(timezone.utc).isoformat()
with io.BytesIO() as buffer:
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        entry = tarfile.TarInfo('app/app/question_bank/lessons.json')
        entry.size, entry.mode, entry.uid, entry.gid = len(bank), 0o644, 10001, 10001
        archive.addfile(entry, io.BytesIO(bank))
    layer = buffer.getvalue()
layer_sha = hashlib.sha256(layer).hexdigest()
with tarfile.open(sys.argv[1], 'r:*') as base:
    manifests = json.load(base.extractfile('manifest.json'))
    assert len(manifests) == 1
    original = manifests[0]
    assert original['RepoTags'] == ['ml-check:' + metadata['base_version']]
    with tarfile.open(fileobj=base.extractfile(original['Layers'][-1]), mode='r:') as prior:
        prior_bank = prior.extractfile('app/app/question_bank/lessons.json').read()
        assert hashlib.sha256(prior_bank).hexdigest() == metadata['base_sha256']
    config = json.load(base.extractfile(original['Config']))
    config['created'] = created
    config['rootfs']['diff_ids'].append('sha256:' + layer_sha)
    config.setdefault('history', []).append({'created': created, 'created_by': 'COPY reviewed 32-lesson question bank'})
    config_bytes = json.dumps(config, separators=(',', ':'), ensure_ascii=False).encode()
    config_sha = hashlib.sha256(config_bytes).hexdigest()
    manifest = {'Config': config_sha + '.json', 'RepoTags': ['ml-check:' + version],
                'Layers': original['Layers'] + [layer_sha + '/layer.tar']}
    with tarfile.open(sys.argv[2], 'w:gz', compresslevel=3) as target:
        for name in original['Layers']:
            entry = copy.copy(base.getmember(name))
            assert entry.isfile()
            target.addfile(entry, base.extractfile(name))
        for name, data in [(config_sha+'.json', config_bytes), (layer_sha+'/layer.tar', layer),
                           ('manifest.json', json.dumps([manifest]).encode())]:
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode = len(data), 0o644
            target.addfile(entry, io.BytesIO(data))
receipt = {'image': 'ml-check:' + version, 'config_digest': 'sha256:' + config_sha,
           'base_image': original['RepoTags'][0], 'bank_sha256': hashlib.sha256(bank).hexdigest(),
           'build_host': 'hblu-5090', 'changed_path': '/app/app/question_bank/lessons.json'}
(release / 'image-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt))
