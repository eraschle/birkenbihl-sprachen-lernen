"""Turn word pairs (as AI models produce them) into position-based word alignments.

AI models answer with text pairs such as ("extrañaré", "vermissen-werde"). Matching that text
back to the sentence is done here, deterministically. Whatever cannot be matched is not guessed:
the affected alignment is FLAGGED and unmatched target words stay unassigned for the user.
"""

from birkenbihl.models.translation import TARGET_JOINER, AlignmentStatus, Sentence, WordAlignment
from birkenbihl.utils.text_extractor import tokenize_clean

WordPair = tuple[str, str]


def align_word_pairs(source_text: str, natural_translation: str, pairs: list[WordPair]) -> Sentence:
    """Build a sentence whose alignments reference token positions.

    Repeated words are matched in order: the second "der" in the pairs is the second "der" in the
    sentence. A source word given twice in a row ("extrañaré"→"vermissen", "extrañaré"→"werde")
    collects both targets.
    """
    sentence = Sentence(source_text=source_text, natural_translation=natural_translation, word_alignments=[])
    matcher = _PairMatcher(sentence.source_tokens, sentence.target_tokens)
    for source_word, target_word in pairs:
        matcher.add(source_word, target_word)
    sentence.word_alignments = matcher.alignments()
    return sentence


def _normalize(word: str) -> str:
    return " ".join(tokenize_clean(word)).lower()


class _PairMatcher:
    def __init__(self, source_tokens: list[str], target_tokens: list[str]):
        self._source = [_normalize(token) for token in source_tokens]
        self._target = [_normalize(token) for token in target_tokens]
        self._targets_by_source: dict[int, list[int]] = {}
        self._flagged_sources: set[int] = set()
        self._used_targets: set[int] = set()
        self._last_source = -1

    def add(self, source_word: str, target_word: str) -> None:
        source_index = self._find_source(_normalize(source_word))
        if source_index is None:
            return
        self._last_source = source_index
        targets = self._targets_by_source.setdefault(source_index, [])
        for part in self._target_parts(target_word):
            target_index = self._find_target(part)
            if target_index is None:
                self._flagged_sources.add(source_index)
            else:
                targets.append(target_index)
                self._used_targets.add(target_index)

    def alignments(self) -> list[WordAlignment]:
        return [self._alignment(index) for index in range(len(self._source))]

    def _alignment(self, source_index: int) -> WordAlignment:
        targets = self._targets_by_source.get(source_index, [])
        flagged = not targets or source_index in self._flagged_sources
        status = AlignmentStatus.FLAGGED if flagged else AlignmentStatus.SUGGESTED
        return WordAlignment(source_index=source_index, target_indices=targets, status=status)

    def _find_source(self, word: str) -> int | None:
        unused = [i for i, token in enumerate(self._source) if token == word and i not in self._targets_by_source]
        following = [i for i in unused if i > self._last_source]
        if following or unused:
            return (following or unused)[0]
        if self._last_source >= 0 and self._source[self._last_source] == word:
            return self._last_source
        return None

    def _target_parts(self, target_word: str) -> list[str]:
        whole = _normalize(target_word)
        if whole in self._target:
            return [whole]
        return [part for part in (_normalize(p) for p in target_word.split(TARGET_JOINER)) if part]

    def _find_target(self, word: str) -> int | None:
        for index, token in enumerate(self._target):
            if token == word and index not in self._used_targets:
                return index
        return None
