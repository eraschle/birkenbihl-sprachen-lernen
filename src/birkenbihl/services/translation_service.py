"""Translation service with Birkenbihl method support."""

from datetime import datetime
from uuid import uuid4

from sqlmodel import Session

from birkenbihl.models.translation import Language, Translation
from birkenbihl.protocols.translation import TranslationProvider


class TranslationService:
    """Service for handling translations with Birkenbihl method."""

    def __init__(self, provider: TranslationProvider, db_session: Session) -> None:
        self.provider = provider
        self.db_session = db_session

    async def translate_natural(self, text: str, source_lang: str, target_lang: str) -> str:
        """Natural translation for passive understanding."""
        return await self.provider.translate_natural(text, source_lang, target_lang)

    async def translate_word_by_word(self, text: str, source_lang: str, target_lang: str) -> str:
        """Word-by-word translation with Birkenbihl formatting."""
        word_translation = await self.provider.translate_word_by_word(text, source_lang, target_lang)
        return self._format_birkenbihl_style(text, word_translation)

    def _format_birkenbihl_style(self, original: str, translation: str) -> str:
        """Format text according to Birkenbihl method with proper spacing."""
        orig_words = original.split()
        trans_words = translation.split()

        # Pad lists to same length
        max_len = max(len(orig_words), len(trans_words))
        while len(orig_words) < max_len:
            orig_words.append("")
        while len(trans_words) < max_len:
            trans_words.append("")

        # Calculate max width for each word pair
        formatted_orig = []
        formatted_trans = []

        for orig, trans in zip(orig_words, trans_words, strict=True):
            max_width = max(len(orig), len(trans))
            formatted_orig.append(orig.ljust(max_width))
            formatted_trans.append(trans.ljust(max_width))

        # Join with 2 spaces between words as per Birkenbihl method
        orig_line = "  ".join(formatted_orig)
        trans_line = "  ".join(formatted_trans)

        return f"{orig_line}\n{trans_line}"

    async def save_translation(
        self, text: str, source_lang: str, target_lang: str, natural: str, word_by_word: str
    ) -> Translation:
        """Save translation to database."""
        # Get or create languages
        source = self._get_or_create_language(source_lang)
        target = self._get_or_create_language(target_lang)

        translation = Translation(
            id=uuid4(),
            original_text=text,
            source_language_id=source.id,
            target_language_id=target.id,
            natural_translation=natural,
            word_by_word_translation=word_by_word,
            created_at=datetime.now(),
        )

        self.db_session.add(translation)
        self.db_session.commit()
        return translation

    def _get_or_create_language(self, code: str) -> Language:
        """Get existing language or create new one."""
        lang = self.db_session.query(Language).filter(Language.code == code).first()
        if not lang:
            lang_names = {"de": "Deutsch", "es": "Español", "en": "English"}
            lang = Language(id=uuid4(), code=code, name=lang_names.get(code, code.upper()), created_at=datetime.now())
            self.db_session.add(lang)
            self.db_session.commit()
        return lang
