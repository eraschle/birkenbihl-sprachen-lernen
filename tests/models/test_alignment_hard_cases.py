"""The gold alignments in tests/fixtures/alignment_hard_cases.json must obey the Birkenbihl rules themselves."""

import json
from pathlib import Path
from typing import Any

import pytest

from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.translation import AlignmentStatus
from birkenbihl.models.validation import validate_alignment_complete
from birkenbihl.utils.text_extractor import tokenize_clean

FIXTURE = Path(__file__).parent.parent / "fixtures" / "alignment_hard_cases.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


@pytest.mark.unit
@pytest.mark.parametrize("case", CASES, ids=[case["source_text"][:40] for case in CASES])
def test_gold_alignment_is_valid(case: dict[str, Any]) -> None:
    source_text, natural, columns = case["source_text"], case["natural_translation"], case["columns"]

    sentence = align_word_pairs(source_text, natural, list(zip(tokenize_clean(source_text), columns, strict=True)))

    assert validate_alignment_complete(sentence) == (True, None)
    assert {a.status for a in sentence.word_alignments} == {AlignmentStatus.SUGGESTED}
