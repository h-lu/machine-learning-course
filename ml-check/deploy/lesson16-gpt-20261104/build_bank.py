"""在hblu-5090生成只替换S14的累计快照和教师审阅稿。"""
import hashlib
import json
from pathlib import Path

release = Path(__file__).resolve().parent
root = release.parents[2]
base_path = release.parent / 'lessons27-32-20261104/lessons.json'
bank = json.loads(base_path.read_text())
source = release / 'source/s14.json'
lesson = json.loads(source.read_text())
base_version = bank['version']
bank['version'] = lesson['content_version']
bank['lessons'] = [lesson if item['lesson_id'] == 'S14' else item for item in bank['lessons']]
(release / 'lessons.json').write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n')

lines = ['# 第16课教师审阅稿', '', '五个概念、五对A/B题。学生作答前的接口仅返回题干与选项。', '']
for concept in lesson['concepts']:
    lines += ['## ' + concept['title'], '', 'AI学习提示：' + concept['tutor_context'], '']
    for question in lesson['questions']:
        if question['concept_id'] != concept['concept_id']:
            continue
        lines += ['### ' + question['id'], '', question['prompt'], '']
        lines += [f'{letter}. {option}' for letter, option in zip('ABCD', question['options'])]
        lines += ['', '答案：' + 'ABCD'[question['answer']], '', question['explanation'], '']
(release / 'REVIEW.md').write_text('\n'.join(lines))
paths = [release / 'lessons.json', source]
manifest = {
    'version': bank['version'], 'base_version': base_version,
    'base_sha256': hashlib.sha256(base_path.read_bytes()).hexdigest(),
    'changed_lessons': ['S14'], 'concept_count': 5, 'question_count': 10,
    'files': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
}
(release / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print('Built 32-lesson bank; updated S14 only')
