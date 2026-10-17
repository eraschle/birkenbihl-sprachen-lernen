"""Compare word aligners on tests/fixtures/alignment_hard_cases.json (needs API keys, costs a few cents).

Usage:
    uv run python scripts/benchmark_alignment.py --llm claude-sonnet-5-5 --llm claude-haiku-5-5 --jev

LLM aligners use the default provider from settings.yaml with the given model name. Jev uses jev_api_key from
settings.yaml or TYPESAFE_API_KEY. The most important number is "wrong, not flagged": a flagged mistake is
checked by the learner, an unflagged one is learned.
"""

import argparse
import json
import os
import time
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent  # noqa: E402
from pydantic_ai.agent import AgentRunResult  # noqa: E402

from birkenbihl.models.alignment import align_word_pairs  # noqa: E402
from birkenbihl.models.translation import AlignmentStatus, Sentence  # noqa: E402
from birkenbihl.protocols import IWordAligner  # noqa: E402
from birkenbihl.providers.catalog import create_jev_model, create_model  # noqa: E402
from birkenbihl.providers.jev_aligner import JevAligner  # noqa: E402
from birkenbihl.providers.llm_aligner import LLMAligner  # noqa: E402
from birkenbihl.services import path_service as ps  # noqa: E402
from birkenbihl.services.language_service import get_language_by  # noqa: E402
from birkenbihl.services.settings_service import SettingsService  # noqa: E402
from birkenbihl.utils.text_extractor import tokenize_clean  # noqa: E402

FIXTURE = Path(__file__).parent.parent / "tests" / "fixtures" / "alignment_hard_cases.json"

_runs: list[AgentRunResult[Any]] = []
_run_sync = Agent.run_sync


def _recording_run_sync(self: Agent[Any, Any], *args: Any, **kwargs: Any) -> AgentRunResult[Any]:
    result = _run_sync(self, *args, **kwargs)
    _runs.append(result)
    return result


Agent.run_sync = _recording_run_sync  # count cost of every model call


@dataclass
class Score:
    sentences: int = 0
    exact: int = 0
    columns: int = 0
    correct: int = 0
    wrong_flagged: int = 0
    wrong_unflagged: int = 0
    right_flagged: int = 0
    seconds: float = 0.0
    cost: Decimal = Decimal(0)
    mistakes: list[str] = field(default_factory=list[str])

    def add(self, result: Sentence, gold: Sentence) -> None:
        expected = {a.source_index: sorted(a.target_indices) for a in gold.word_alignments}
        all_right = True
        for alignment in result.sorted_alignments():
            right = sorted(alignment.target_indices) == expected[alignment.source_index]
            flagged = alignment.status == AlignmentStatus.FLAGGED
            self.columns += 1
            self.correct += right
            self.wrong_flagged += not right and flagged
            self.wrong_unflagged += not right and not flagged
            self.right_flagged += right and flagged
            all_right &= right
            if not right and not flagged:
                got = result.target_text(alignment) or "(leer)"
                right_text = gold.target_text(gold.word_alignments[alignment.source_index])
                self.mistakes.append(f"{result.source_word(alignment)} -> {got}  (richtig: {right_text})")
        self.sentences += 1
        self.exact += all_right

    def report(self, name: str) -> str:
        return "\n".join(
            [
                name,
                f"  exact sentences:     {self.exact}/{self.sentences}",
                f"  correct columns:     {self.correct}/{self.columns} ({self.correct / self.columns:.0%})",
                f"  wrong, flagged:      {self.wrong_flagged}",
                f"  wrong, NOT flagged:  {self.wrong_unflagged}",
                f"  right but flagged:   {self.right_flagged}",
                f"  time per sentence:   {self.seconds / self.sentences:.2f}s",
                f"  cost per sentence:   ${self.cost / self.sentences:.5f}",
                *(f"    unflagged: {mistake}" for mistake in self.mistakes),
            ]
        )


def _gold(case: dict[str, Any]) -> Sentence:
    pairs = list(zip(tokenize_clean(case["source_text"]), case["columns"], strict=True))
    return align_word_pairs(case["source_text"], case["natural_translation"], pairs)


def _cost(result: AgentRunResult[Any]) -> Decimal:
    try:
        return Decimal(result.response.cost().total_price)
    except LookupError:  # model unknown to genai-prices
        return Decimal(0)


def benchmark(aligner: IWordAligner, cases: list[dict[str, Any]]) -> Score:
    score = Score()
    target_lang = get_language_by("de")
    for case in cases:
        _runs.clear()
        start = time.time()
        result = aligner.align(
            case["source_text"], case["natural_translation"], get_language_by(case["source_language"]), target_lang
        )
        score.seconds += time.time() - start
        score.cost += sum((_cost(run) for run in _runs), Decimal(0))
        score.add(result, _gold(case))
    return score


def _aligners(llm_models: list[str], with_jev: bool) -> dict[str, IWordAligner]:
    settings = SettingsService(ps.get_setting_path()).load_settings()
    aligners: dict[str, IWordAligner] = {}
    provider = settings.get_default_provider()
    for model in llm_models:
        if provider is None:
            raise SystemExit("No provider in settings.yaml for the LLM aligners")
        aligners[f"LLM {model}"] = LLMAligner(create_model(provider.model_copy(update={"model": model})))
    if with_jev:
        aligners["Jev"] = JevAligner(create_jev_model(settings.jev_api_key))
    return aligners


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--llm", action="append", default=[], help="model name of the default provider")
    parser.add_argument("--jev", action="store_true", help="include Jev")
    args = parser.parse_args()
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    print(f"{len(cases)} sentences from {FIXTURE.name}\n")
    for name, aligner in _aligners(args.llm, args.jev).items():
        print(benchmark(aligner, cases).report(name), "\n", flush=True)


if __name__ == "__main__":
    main()
