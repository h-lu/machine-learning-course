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
    concepts: list[dict]
    durations: dict

    def __post_init__(self):
        """Normalize the question identifiers used by both old and new banks.

        Early ML banks used ``S15-A01`` and one-digit suffixes.  The public
        contract is now ``S15-A-01`` (or ``C01-A-01``): the lesson, phase and
        two-digit question number are all explicit.  Normalizing at load time
        keeps old local copies readable while the API and pages expose the
        canonical identifiers.
        """
        if not isinstance(self.durations, dict):
            raise ValueError(f"{self.lesson_id} durations must be an object")
        for key in ("attempt_a", "learn", "attempt_b"):
            value = self.durations.get(key)
            if type(value) is not int or not 1 <= value <= 3600:
                raise ValueError(f"{self.lesson_id} invalid phase duration: {key}")
        normalized = []
        for q in self.questions:
            row = dict(q)
            raw = str(row.get("id", ""))
            match = re.fullmatch(r"([CS]\d{2})-([AB])-?(\d{1,2})", raw, re.I)
            if match:
                row["id"] = f"{match.group(1).upper()}-{match.group(2).upper()}-{int(match.group(3)):02d}"
            normalized.append(row)
        self.questions = normalized

        if len(self.concepts) != 5:
            raise ValueError(f"{self.lesson_id} must define five concepts")
        concept_ids = [str(item.get("concept_id", "")) for item in self.concepts]
        if len(concept_ids) != len(set(concept_ids)):
            raise ValueError(f"{self.lesson_id} contains duplicate concept ids")
        for item in self.concepts:
            if not all(str(item.get(key, "")).strip() for key in ("concept_id", "title", "tutor_context")):
                raise ValueError(f"{self.lesson_id} contains empty concept text")
        question_concepts = {
            str(question.get("concept_id", "")) for question in self.questions
        }
        if question_concepts != set(concept_ids):
            raise ValueError(f"{self.lesson_id} questions do not match its concepts")
        for concept_id in concept_ids:
            phases = [
                str(question.get("phase", "")).upper()
                for question in self.questions
                if str(question.get("concept_id", "")) == concept_id
            ]
            if sorted(phases) != ["A", "B"]:
                raise ValueError(f"{self.lesson_id} concept {concept_id} needs one A and one B question")

    def _by_phase(self, phase: str) -> list[dict]:
        rows = [q for q in self.questions if str(q.get("phase", "")).upper() == phase.upper()]
        def number(q):
            m = re.search(r"-(\d+)$", str(q.get("id", "")))
            return int(m.group(1)) if m else 999
        return sorted(rows, key=number)

    @property
    def concept_ids(self):
        return [str(item["concept_id"]) for item in self.concepts]
    @property
    def items(self):
        questions = {
            (str(question["concept_id"]), str(question["phase"]).lower()): question
            for question in self.questions
        }
        return [
            {
                **item,
                "pair": {
                    phase: questions[(str(item["concept_id"]), phase)]
                    for phase in ("a", "b")
                },
            }
            for item in self.concepts
        ]
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

ROOT = Path(__file__).parent / 'question_bank/lessons.json'
BANK_VERSION = json.loads(ROOT.read_text(encoding='utf-8'))['version']
def _load():
    raw=json.loads(ROOT.read_text(encoding='utf-8'))
    banks=[]
    for l in raw['lessons']:
        banks.append(LessonBank(l['lesson_id'],l['title'],l.get('module',''),l['questions'],l['concepts'], l.get('durations', {'attempt_a':600,'learn':900,'attempt_b':600})))
    return banks
CURRENT_BANKS = _load(); DEFAULT_BANK=CURRENT_BANKS[0]
def bank_for_lesson(lesson_id):
    for b in CURRENT_BANKS:
        if b.lesson_id.casefold()==str(lesson_id).casefold(): return b
    raise LookupError(lesson_id)
