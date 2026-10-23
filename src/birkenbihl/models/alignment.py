"""Turn AI answers into position-based word alignments, deterministically.

Language models answer with text pairs such as ("extrañaré", "vermissen-werde"), matched back to the
sentence by align_word_pairs(). Jev answers with a probability per source/target word pair, distributed by
align_by_probability(). Several source words can share target words ("estación de tren" → "Bahnhof").
Whatever is uncertain is not guessed: the affected alignment is FLAGGED and unassigned target words stay in
the pool for the user.
"""

from birkenbihl.models.translation import SOURCE_JOINER, TARGET_JOINER, AlignmentStatus, Sentence, WordAlignment
from birkenbihl.utils.text_extractor import tokenize_clean

WordPair = tuple[str, str]


def align_word_pairs(source_text: str, natural_translation: str, pairs: list[WordPair]) -> Sentence:
    """Build a sentence whose alignments reference token positions.

    A pair's source side may name several consecutive source words that share the target words
    ("estación de tren" → "Bahnhof"). Repeated words are matched in order: the second "der" in the pairs is
    the second "der" in the sentence. The same source given twice in a row ("extrañaré"→"vermissen",
    "extrañaré"→"werde") collects both targets. Source words no pair names get their own empty, FLAGGED column.
    """
    sentence = Sentence(source_text=source_text, natural_translation=natural_translation, word_alignments=[])
    matcher = _PairMatcher(sentence.source_tokens, sentence.target_tokens)
    for source_words, target_words in pairs:
        matcher.add(source_words, target_words)
    sentence.word_alignments = matcher.alignments()
    return sentence


def _normalize(word: str) -> str:
    return " ".join(tokenize_clean(word)).lower()


class _Column:
    def __init__(self, sources: list[int]):
        self.sources = sources
        self.targets: list[int] = []
        self.flagged = False

    def to_alignment(self) -> WordAlignment:
        flagged = self.flagged or not self.targets
        status = AlignmentStatus.FLAGGED if flagged else AlignmentStatus.SUGGESTED
        return WordAlignment(source_indices=self.sources, target_indices=self.targets, status=status)


class _PairMatcher:
    def __init__(self, source_tokens: list[str], target_tokens: list[str]):
        self._source = [_normalize(token) for token in source_tokens]
        self._target = [_normalize(token) for token in target_tokens]
        self._columns: list[_Column] = []
        self._used_sources: set[int] = set()
        self._used_targets: set[int] = set()

    def add(self, source_words: str, target_words: str) -> None:
        column = self._column_for(self._source_parts(source_words))
        if column is None:
            return
        for part in self._target_parts(target_words):
            target_index = self._find_target(part)
            if target_index is None:
                column.flagged = True
            else:
                column.targets.append(target_index)
                self._used_targets.add(target_index)

    def alignments(self) -> list[WordAlignment]:
        missing = [_Column([index]) for index in range(len(self._source)) if index not in self._used_sources]
        columns = sorted(self._columns + missing, key=lambda column: column.sources[0])
        return [column.to_alignment() for column in columns]

    def _column_for(self, words: list[str]) -> "_Column | None":
        start = self._find_sequence(words)
        if start is None:
            last = self._columns[-1] if self._columns else None
            return last if last and [self._source[i] for i in last.sources] == words else None
        column = _Column(list(range(start, start + len(words))))
        self._columns.append(column)
        self._used_sources.update(column.sources)
        return column

    def _find_sequence(self, words: list[str]) -> int | None:
        """Start of the first unused run of source tokens equal to words, preferring runs after the last column."""
        if not words:
            return None
        last_end = max((max(c.sources) for c in self._columns), default=-1)
        starts = [
            start
            for start in range(len(self._source) - len(words) + 1)
            if self._source[start : start + len(words)] == words
            and not self._used_sources.intersection(range(start, start + len(words)))
        ]
        following = [start for start in starts if start > last_end]
        return (following or starts or [None])[0]

    def _source_parts(self, source_words: str) -> list[str]:
        whole = _normalize(source_words)
        if whole in self._source:
            return [whole]
        return [part for part in (_normalize(p) for p in source_words.replace(SOURCE_JOINER, " ").split()) if part]

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


# A target word is only trusted when its column is likely enough and clearly ahead of the runner-up column
MIN_PROBABILITY = 0.5
MIN_MARGIN = 0.15

ProbabilityMatrix = list[list[float]]  # [source][target]: probability that the target word translates the source word


def align_by_probability(source_text: str, natural_translation: str, probabilities: ProbabilityMatrix) -> Sentence:
    """Build a sentence by giving every target word to the source word most likely to mean it.

    Every target word is used exactly once by construction. Uncertain words are not guessed: their column is
    FLAGGED. A source word no target word went to joins the column before it (or after it, at the start) and
    that column is FLAGGED, so the user checks whether the words really share their translation
    ("estación de tren" → "Bahnhof"). Target words keep the order of the natural translation within a column.
    """
    sentence = Sentence(source_text=source_text, natural_translation=natural_translation, word_alignments=[])
    source_count, target_count = len(sentence.source_tokens), len(sentence.target_tokens)
    if len(probabilities) != source_count or any(len(row) != target_count for row in probabilities):
        raise ValueError(f"Probabilities must be a {source_count}x{target_count} matrix (source x target)")

    columns = [[row[target] for row in probabilities] for target in range(target_count)]
    owners = [column.index(max(column)) for column in columns]
    uncertain = {owner for owner, column in zip(owners, columns, strict=True) if _is_uncertain(column)}
    groups = [_Column([source]) for source in range(source_count)]
    for group in groups:
        group.targets = [target for target, owner in enumerate(owners) if owner == group.sources[0]]
        group.flagged = group.sources[0] in uncertain
    sentence.word_alignments = [group.to_alignment() for group in _join_empty_groups(groups)]
    return sentence


def _join_empty_groups(groups: list[_Column]) -> list[_Column]:
    """Merge source words without a target word into a neighbouring column (FLAGGED for review)."""
    if not any(group.targets for group in groups):
        return groups  # nothing to share: leave every word in its own empty column
    joined: list[_Column] = []
    pending: list[int] = []  # empty source words before the first column with targets
    for group in groups:
        if group.targets:
            group.sources = pending + group.sources
            group.flagged = group.flagged or bool(pending)
            pending = []
            joined.append(group)
        elif joined:
            joined[-1].sources += group.sources
            joined[-1].flagged = True
        else:
            pending += group.sources
    return joined


def _is_uncertain(column: list[float]) -> bool:
    best, runner_up = (sorted(column, reverse=True) + [0.0])[:2]
    return best < MIN_PROBABILITY or best - runner_up < MIN_MARGIN
