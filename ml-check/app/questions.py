from __future__ import annotations
import json
import re
from pathlib import Path
from dataclasses import dataclass


LEGACY_DURATIONS = {"attempt_a": 600, "learn": 900, "attempt_b": 600}

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
        if not re.fullmatch(r"[CS]\d{2}", self.lesson_id):
            raise ValueError("lesson_id must use C01/S01 form")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError(f"{self.lesson_id} title must be non-empty")
        if not isinstance(self.module, str):
            raise ValueError(f"{self.lesson_id} module must be text")
        if not isinstance(self.questions, list):
            raise ValueError(f"{self.lesson_id} questions must be a list")
        if not isinstance(self.concepts, list):
            raise ValueError(f"{self.lesson_id} concepts must be a list")
        if not isinstance(self.durations, dict):
            raise ValueError(f"{self.lesson_id} durations must be an object")
        for key in ("attempt_a", "learn", "attempt_b"):
            value = self.durations.get(key)
            if type(value) is not int or not 1 <= value <= 3600:
                raise ValueError(f"{self.lesson_id} invalid phase duration: {key}")
        normalized = []
        for q in self.questions:
            if not isinstance(q, dict):
                raise ValueError(f"{self.lesson_id} question must be an object")
            row = dict(q)
            raw = str(row.get("id", ""))
            match = re.fullmatch(r"([CS]\d{2})-([AB])-?(\d{1,2})", raw, re.I)
            if not match or match.group(1).upper() != self.lesson_id:
                raise ValueError(f"{self.lesson_id} invalid question id: {raw}")
            row["id"] = f"{match.group(1).upper()}-{match.group(2).upper()}-{int(match.group(3)):02d}"
            for key in ("concept_id", "phase", "prompt", "explanation"):
                if not isinstance(row.get(key), str) or not row[key].strip():
                    raise ValueError(f"{self.lesson_id} question {row['id']} invalid {key}")
            if row["phase"].upper() != match.group(2).upper():
                raise ValueError(f"{self.lesson_id} question {row['id']} phase disagrees with id")
            row["phase"] = row["phase"].upper()
            options = row.get("options")
            if (
                not isinstance(options, list)
                or len(options) != 4
                or any(not isinstance(option, str) or not option.strip() for option in options)
                or len(set(options)) != 4
            ):
                raise ValueError(f"{self.lesson_id} question {row['id']} needs four distinct options")
            answer = row.get("answer")
            if isinstance(answer, bool):
                raise ValueError(f"{self.lesson_id} question {row['id']} invalid answer")
            try:
                answer_index = int(answer)
            except (TypeError, ValueError) as error:
                raise ValueError(f"{self.lesson_id} question {row['id']} invalid answer") from error
            if str(answer_index) != str(answer) or answer_index not in range(4):
                raise ValueError(f"{self.lesson_id} question {row['id']} invalid answer")
            normalized.append(row)
        self.questions = normalized

        question_ids = [str(question["id"]) for question in self.questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError(f"{self.lesson_id} contains duplicate question ids")

        if len(self.concepts) != 5:
            raise ValueError(f"{self.lesson_id} must define five concepts")
        if any(not isinstance(item, dict) for item in self.concepts):
            raise ValueError(f"{self.lesson_id} concept must be an object")
        concept_ids = [str(item.get("concept_id", "")) for item in self.concepts]
        if len(concept_ids) != len(set(concept_ids)):
            raise ValueError(f"{self.lesson_id} contains duplicate concept ids")
        for item in self.concepts:
            if not all(
                isinstance(item.get(key), str) and item[key].strip()
                for key in ("concept_id", "title", "tutor_context")
            ):
                raise ValueError(f"{self.lesson_id} contains empty concept text")
            if not re.fullmatch(rf"{self.lesson_id}-\d{{2}}", str(item["concept_id"])):
                raise ValueError(f"{self.lesson_id} invalid concept id")
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
        rows = [
            question
            for question in self.questions
            if question["concept_id"] == concept_id
            and question["phase"].casefold() == str(phase).casefold()
        ]
        if len(rows) != 1:
            raise LookupError(concept_id)
        q = rows[0]
        return {'id': q['id'], 'concept_id': concept_id,
                'options':[{'id':str(i), 'text':x} for i,x in enumerate(q['options'])],
                'answer':str(q['answer']), 'explanation':q['explanation'],
                'prompt': q['prompt']}


def bank_snapshot(bank: LessonBank) -> str:
    """Serialize the exact lesson used when a classroom session is created."""
    return json.dumps(
        {
            "lesson_id": bank.lesson_id,
            "title": bank.title,
            "module": bank.module,
            "questions": bank.questions,
            "concepts": bank.concepts,
            "durations": bank.durations,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def bank_from_snapshot(value: str) -> LessonBank:
    raw = json.loads(value)
    if not isinstance(raw, dict):
        raise ValueError("session question snapshot must be an object")
    for key in ("lesson_id", "title"):
        if not isinstance(raw.get(key), str):
            raise ValueError(f"session question snapshot has invalid {key}")
    if "module" in raw and not isinstance(raw["module"], str):
        raise ValueError("session question snapshot has invalid module")
    if not isinstance(raw.get("questions"), list):
        raise ValueError("session question snapshot has invalid questions")
    if not isinstance(raw.get("concepts"), list):
        raise ValueError("session question snapshot has invalid concepts")
    durations = raw.get("durations", LEGACY_DURATIONS)
    if not isinstance(durations, dict):
        raise ValueError("session question snapshot has invalid durations")
    return LessonBank(
        raw["lesson_id"],
        raw["title"],
        raw.get("module", ""),
        list(raw["questions"]),
        list(raw["concepts"]),
        dict(durations),
    )

ROOT = Path(__file__).parent / 'question_bank/lessons.json'
# Read once so a deployment cannot pair a version read from one file revision
# with lesson content read from another revision during process startup.
_RAW_BANK = json.loads(ROOT.read_text(encoding='utf-8'))
if (
    not isinstance(_RAW_BANK, dict)
    or not isinstance(_RAW_BANK.get('version'), str)
    or not _RAW_BANK['version'].strip()
):
    raise ValueError('question bank must define a non-empty version')
BANK_VERSION = _RAW_BANK['version']
def _load():
    raw = _RAW_BANK
    banks=[]
    for l in raw['lessons']:
        banks.append(LessonBank(l['lesson_id'],l['title'],l.get('module',''),l['questions'],l['concepts'], l.get('durations', LEGACY_DURATIONS)))
    return banks
CURRENT_BANKS = _load(); DEFAULT_BANK=CURRENT_BANKS[0]
def bank_for_lesson(lesson_id):
    for b in CURRENT_BANKS:
        if b.lesson_id.casefold()==str(lesson_id).casefold(): return b
    raise LookupError(lesson_id)
