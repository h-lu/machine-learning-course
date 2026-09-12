from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class LessonBank:
    lesson_id: str
    title: str
    module: str
    questions: list[dict]
    durations: dict
    @property
    def concept_ids(self):
        return [f'{self.lesson_id}-{i}' for i in range(1, 3)]
    @property
    def items(self):
        rows = []
        for i, cid in enumerate(self.concept_ids, 1):
            a = next(q for q in self.questions if q['phase'].upper() == 'A' and q['id'].endswith(f'-{i}'))
            b = next(q for q in self.questions if q['phase'].upper() == 'B' and q['id'].endswith(f'-{i}'))
            rows.append({'concept_id': cid, 'title': f'概念 {i}', 'tutor_context': '结合本课项目，说明这个概念何时有用、何时可能误导。',
                         'pair': {'a': a, 'b': b}})
        return rows
    def item(self, concept_id):
        return next(item for item in self.items if item["concept_id"] == concept_id)

    def question(self, concept_id, phase):
        i = int(str(concept_id).rsplit('-',1)[-1])
        q = next(q for q in self.questions if q['phase'].upper()==phase.upper() and q['id'].endswith(f'-{i}'))
        return {'concept_id': concept_id, 'options':[{'id':str(i), 'text':x} for i,x in enumerate(q['options'])], 'answer':str(q['answer']), 'explanation':q['explanation']}

ROOT = Path(__file__).parent / 'question_bank/lessons.json'
def _load():
    raw=json.loads(ROOT.read_text(encoding='utf-8'))
    banks=[]
    for l in raw['lessons']:
        banks.append(LessonBank(l['lesson_id'],l['title'],l.get('module',''),l['questions'], {'attempt_a':600,'learn':900,'attempt_b':600}))
    return banks
CURRENT_BANKS = _load(); DEFAULT_BANK=CURRENT_BANKS[0]
def bank_for_lesson(lesson_id):
    for b in CURRENT_BANKS:
        if b.lesson_id.casefold()==str(lesson_id).casefold(): return b
    raise LookupError(lesson_id)
