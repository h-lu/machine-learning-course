"""Apply only reviewed text edits; never import or execute course code."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path.cwd().resolve()
BASE_TREE = '669e6a10c7fd8b796a8e608c5d4def9e4ba81cf8'
FINAL_TREE = 'e81fd2b0fd9a8035011b05ca030bc39241c46059'
PARTS = [
    '78e75ac195353627bd609be8640c674a65115b75',
    'dbbf0180217a59d8e1579018d130975b4e135c85',
    '53dc7a62503bc68efca3983c7bd8128740b88b8d',
    'ad8e392b8309a862b9017718bea233ba5790b24c',
]

def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()

if git('rev-parse', 'HEAD^' + '^{tree}') != BASE_TREE:
    raise SystemExit('Unexpected baseline; stop without publishing.')
if git('status', '--porcelain'):
    raise SystemExit('Expected a clean checkout.')

paths = []
for index, expected in enumerate(PARTS):
    part = ROOT / '.review-transfer' / f'part-{index}.json'
    data = part.read_bytes()
    digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if digest != expected:
        raise SystemExit(f'Instruction checksum mismatch: {index}')
    for item in json.loads(data):
        relative = item['path']
        target = ROOT / relative
        if target.is_symlink() or not target.resolve().is_relative_to(ROOT):
            raise SystemExit('Unsafe path')
        if relative in paths or relative.startswith(('.git/', '.review-transfer/')):
            raise SystemExit('Unexpected target')
        if 'content' in item:
            text = item['content']
        else:
            text = target.read_text(encoding='utf-8')
            for replacement in item['replacements']:
                old = replacement['old']
                if text.count(old) != 1:
                    raise SystemExit(f'Unexpected original text: {relative}')
                text = text.replace(old, replacement['new'], 1)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        paths.append(relative)

# Rebuild the sole changed bank object without executing repository scripts.
bank_path = ROOT / 'ml-check/app/question_bank/lessons.json'
bank = json.loads(bank_path.read_text(encoding='utf-8'))
source = json.loads((ROOT / 'course-instructor/lessons/S07/questions.json').read_text(encoding='utf-8'))
assert [row['lesson_id'] for row in bank['lessons']].count('S07') == 1
bank['version'] = 'ml-v9-guided-review-2026-09-19'
for index, row in enumerate(bank['lessons']):
    if row['lesson_id'] == 'S07':
        bank['lessons'][index] = {**source, 'module': row['module']}
bank_path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
paths.append('ml-check/app/question_bank/lessons.json')
assert len(paths) == 24
subprocess.run(['git', 'add', '--', *paths], check=True)
subprocess.run(['git', 'rm', '-r', '--', '.review-transfer', '.github/workflows/prepare-premerge.yml'], check=True)
if git('write-tree') != FINAL_TREE:
    raise SystemExit('Result differs from reviewed source; nothing will be pushed.')
subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
print('Reviewed source tree verified:', FINAL_TREE)
