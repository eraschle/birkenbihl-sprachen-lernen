"""Tests for alignment post-processing hooks."""

from birkenbihl.gui.hooks.alignment_hooks import (
    AlignmentHookManager,
    HyphenateMultiWordsHook,
)


class TestHyphenateMultiWordsHook:
    """Test suite for HyphenateMultiWordsHook."""

    def test_single_target_word(self) -> None:
        """Test source word with single target word."""
        hook = HyphenateMultiWordsHook()
        mappings = {"Yo": ["Ich"]}
        result = hook.process(mappings, ["Ich", "werde", "dich", "vermissen"])

        assert len(result) == 1
        assert result[0].source_word == "Yo"
        assert result[0].target_word == "Ich"  # No hyphen
        assert result[0].position == 0

    def test_multiple_target_words_with_hyphen(self) -> None:
        """Test source word with multiple target words gets hyphenated."""
        hook = HyphenateMultiWordsHook()
        mappings = {"extrañaré": ["werde", "vermissen"]}
        result = hook.process(mappings, ["Ich", "werde", "dich", "vermissen"])

        assert len(result) == 1
        assert result[0].source_word == "extrañaré"
        assert result[0].target_word == "werde-vermissen"  # With hyphen!
        assert result[0].position == 0

    def test_empty_target_words_skipped(self) -> None:
        """Test source word with no target words is skipped."""
        hook = HyphenateMultiWordsHook()
        mappings = {"word": []}
        result = hook.process(mappings, ["target"])

        assert len(result) == 0  # Empty list

    def test_multiple_source_words(self) -> None:
        """Test complete sentence with multiple source words."""
        hook = HyphenateMultiWordsHook()
        mappings = {"Yo": ["Ich"], "te": ["dich"], "extrañaré": ["werde", "vermissen"]}
        result = hook.process(mappings, ["Ich", "werde", "dich", "vermissen"])

        assert len(result) == 3

        # Check positions are sequential
        assert result[0].position == 0
        assert result[1].position == 1
        assert result[2].position == 2

        # Check hyphenation
        assert result[0].target_word == "Ich"
        assert result[1].target_word == "dich"
        assert result[2].target_word == "werde-vermissen"

    def test_preserves_order(self) -> None:
        """Test that order of source words is preserved."""
        # Python 3.7+ dicts preserve insertion order
        hook = HyphenateMultiWordsHook()
        mappings = {
            "first": ["a"],
            "second": ["b", "c"],
            "third": ["d"],
        }
        result = hook.process(mappings, ["a", "b", "c", "d"])

        assert result[0].source_word == "first"
        assert result[1].source_word == "second"
        assert result[2].source_word == "third"

    def test_three_target_words_with_hyphens(self) -> None:
        """Test source word with three target words gets hyphenated correctly."""
        hook = HyphenateMultiWordsHook()
        mappings = {"compound": ["word", "one", "two"]}
        result = hook.process(mappings, ["word", "one", "two"])

        assert len(result) == 1
        assert result[0].source_word == "compound"
        assert result[0].target_word == "word-one-two"
        assert result[0].position == 0

    def test_mixed_empty_and_filled_mappings(self) -> None:
        """Test that empty mappings are skipped while filled ones are processed."""
        hook = HyphenateMultiWordsHook()
        mappings = {
            "word1": ["target1"],
            "word2": [],  # Empty, should be skipped
            "word3": ["target2", "target3"],
        }
        result = hook.process(mappings, ["target1", "target2", "target3"])

        assert len(result) == 2  # word2 skipped
        assert result[0].source_word == "word1"
        assert result[0].target_word == "target1"
        assert result[0].position == 0

        assert result[1].source_word == "word3"
        assert result[1].target_word == "target2-target3"
        assert result[1].position == 1  # Position increments only for non-empty

    def test_empty_mappings_dict(self) -> None:
        """Test with completely empty mappings dict."""
        hook = HyphenateMultiWordsHook()
        mappings: dict[str, list[str]] = {}
        result = hook.process(mappings, ["some", "words"])

        assert len(result) == 0


class TestAlignmentHookManager:
    """Test suite for AlignmentHookManager."""

    def test_manager_default_hook_registered(self) -> None:
        """Test manager registers default hook."""
        manager = AlignmentHookManager()
        # Should have HyphenateMultiWordsHook registered
        assert len(manager._hooks) == 1
        assert isinstance(manager._hooks[0], HyphenateMultiWordsHook)

    def test_manager_process(self) -> None:
        """Test manager processes through hook."""
        manager = AlignmentHookManager()
        mappings = {"Yo": ["Ich"], "te": ["dich"]}
        result = manager.process(mappings, ["Ich", "dich"])

        assert len(result) == 2
        assert result[0].target_word == "Ich"
        assert result[1].target_word == "dich"

    def test_manager_custom_hook(self) -> None:
        """Test manager can register custom hooks."""

        class CustomHook:
            def process(
                self,
                source_mappings: dict[str, list[str]],
                target_words: list[str],
            ) -> list:
                # Just return empty list for testing
                return []

        manager = AlignmentHookManager()
        manager.register(CustomHook())

        assert len(manager._hooks) == 2  # Default + Custom

    def test_manager_with_multiple_hooks_uses_last(self) -> None:
        """Test that manager uses the last registered hook."""

        class FirstHook:
            def process(
                self,
                source_mappings: dict[str, list[str]],
                target_words: list[str],
            ) -> list:
                # This should NOT be used
                return []

        class SecondHook:
            def process(
                self,
                source_mappings: dict[str, list[str]],
                target_words: list[str],
            ) -> list:
                # This SHOULD be used
                from birkenbihl.models.translation import WordAlignment

                return [WordAlignment(source_word="test", target_word="result", position=0)]

        manager = AlignmentHookManager()
        manager.register(FirstHook())
        manager.register(SecondHook())

        mappings = {"source": ["target"]}
        result = manager.process(mappings, ["target"])

        # Should use SecondHook (last registered)
        assert len(result) == 1
        assert result[0].source_word == "test"
        assert result[0].target_word == "result"

    def test_manager_hyphenates_multiple_words(self) -> None:
        """Test manager correctly hyphenates multiple target words."""
        manager = AlignmentHookManager()
        mappings = {"extrañaré": ["werde", "vermissen"]}
        result = manager.process(mappings, ["Ich", "werde", "dich", "vermissen"])

        assert len(result) == 1
        assert result[0].source_word == "extrañaré"
        assert result[0].target_word == "werde-vermissen"
        assert result[0].position == 0

    def test_manager_with_empty_hooks_list(self) -> None:
        """Test manager with no hooks returns empty list."""
        manager = AlignmentHookManager()
        manager._hooks = []  # Remove default hooks

        mappings = {"word": ["target"]}
        result = manager.process(mappings, ["target"])

        assert len(result) == 0
