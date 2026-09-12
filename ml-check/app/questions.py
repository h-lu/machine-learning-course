from __future__ import annotations
import json
import re
from pathlib import Path
from dataclasses import dataclass

@dataclass
class LessonBank:
    lesson_id: str
    title: str
    module: str
    questions: list[dict]
    durations: dict

    def __post_init__(self):
        """Normalize the question identifiers used by both old and new banks.

        Early ML banks used ``S15-A01`` and one-digit suffixes.  The public
        contract is now ``S15-A-01`` (or ``C01-A-01``): the lesson, phase and
        two-digit question number are all explicit.  Normalizing at load time
        keeps old local copies readable while the API and pages expose the
        canonical identifiers.
        """
        normalized = []
        for q in self.questions:
            row = dict(q)
            raw = str(row.get("id", ""))
            match = re.fullmatch(r"([CS]\d{2})-([AB])-?(\d{1,2})", raw, re.I)
            if match:
                row["id"] = f"{match.group(1).upper()}-{match.group(2).upper()}-{int(match.group(3)):02d}"
            normalized.append(row)
        self.questions = normalized

    def _by_phase(self, phase: str) -> list[dict]:
        rows = [q for q in self.questions if str(q.get("phase", "")).upper() == phase.upper()]
        def number(q):
            m = re.search(r"-(\d+)$", str(q.get("id", "")))
            return int(m.group(1)) if m else 999
        return sorted(rows, key=number)

    @property
    def concept_ids(self):
        # One concept is represented by one A/B pair.  Use the explicit
        # question numbers so five-question banks do not depend on suffix
        # matching or list order.
        return [f"{self.lesson_id}-{i:02d}" for i, _ in enumerate(self._by_phase("A"), 1)]
    @property
    def items(self):
        rows = []
        a_rows, b_rows = self._by_phase("A"), self._by_phase("B")
        for i, cid in enumerate(self.concept_ids, 1):
            if i > len(a_rows) or i > len(b_rows):
                continue
            a, b = a_rows[i - 1], b_rows[i - 1]
            rows.append({'concept_id': cid,
                         'title': f'{a["id"]} · {_short_topic(a["prompt"])}',
                         # The learning phase intentionally exposes only the
                         # A-version context.  The paired B question remains
                         # private until the teacher opens the B phase.
                         'tutor_context': f'A 版问题：{a["prompt"]}',
                         'pair': {'a': a, 'b': b}})
        return rows
    def item(self, concept_id):
        return next(item for item in self.items if item["concept_id"] == concept_id)

    def question(self, concept_id, phase):
        i = int(str(concept_id).rsplit('-',1)[-1])
        rows = self._by_phase(phase)
        if i < 1 or i > len(rows):
            raise LookupError(concept_id)
        q = rows[i - 1]
        return {'id': q['id'], 'concept_id': concept_id,
                'options':[{'id':str(i), 'text':x} for i,x in enumerate(q['options'])],
                'answer':str(q['answer']), 'explanation':q['explanation'],
                'prompt': q['prompt']}

def _short_topic(prompt: str) -> str:
    """Create a readable topic label from the actual question text."""
    text = re.sub(r"^在[“\"「]|[？?。！!]$", "", str(prompt)).strip()
    return text if len(text) <= 28 else text[:28] + "…"

ROOT = Path(__file__).parent / 'question_bank/lessons.json'
BANK_VERSION = 'ml-v3-2026-09-12'
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
