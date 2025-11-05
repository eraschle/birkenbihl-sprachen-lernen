"""Demo application for Word Alignment Editor.

Demonstrates the complete workflow:
1. Create sample translation
2. Load into alignment editor
3. Edit alignments via drag-and-drop
4. Save changes back to storage
5. Reload to verify persistence

Usage:
    python demo_alignment_editor.py
"""

import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.gui.viewmodels.alignment_editor_vm import AlignmentEditorViewModel
from birkenbihl.gui.views.alignment_editor_view import InterleavedAlignmentEditor
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.services.language_service import SUPPORTED_LANGUAGES
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


class DemoWindow(QMainWindow):
    """Demo window showing alignment editor."""

    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "demo.json"

        storage = JsonStorageProvider(str(self.storage_path))
        self.service = TranslationService(translator=None, storage=storage)

        self.translation_id = None
        self.sentence_uuid = None

        self.viewmodel = AlignmentEditorViewModel()
        self.editor = InterleavedAlignmentEditor(self.viewmodel)

        self._setup_ui()
        self._bind_signals()
        self._load_demo_data()

    def _setup_ui(self):
        """Build UI layout."""
        self.setWindowTitle("Birkenbihl Word Alignment Editor - Demo")
        self.resize(1400, 700)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("<h1>Word Alignment Editor Demo</h1>")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            (
                "<p><b>Instructions:</b></p><ul>"
                "<li>Drag target words (German) between columns to change alignment</li>"
                "<li>Each column represents one source word (English/Spanish)</li>"
                "<li>Multiple target words in one column will be joined with hyphens</li>"
                "<li>All target words must be assigned (no words in unassigned pool)</li>"
                "<li>Save button enables when alignment is valid</li></ul>"
            )
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Example selector
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        btn1 = QPushButton("Example 1: Simple (EN→DE)")
        btn1.clicked.connect(lambda: self._load_example(1))
        button_row.addWidget(btn1)

        btn2 = QPushButton("Example 2: Word Order (EN→DE)")
        btn2.clicked.connect(lambda: self._load_example(2))
        button_row.addWidget(btn2)

        btn3 = QPushButton("Example 3: Hyphenated (ES→DE)")
        btn3.clicked.connect(lambda: self._load_example(3))
        button_row.addWidget(btn3)

        button_row.addStretch()
        layout.addLayout(button_row)

        # Editor
        layout.addWidget(self.editor, stretch=1)

        self.setCentralWidget(central)

    def _bind_signals(self):
        """Connect editor signals."""
        self.editor.save_requested.connect(self._on_save)
        self.editor.cancel_requested.connect(self.close)
        self.editor.regenerate_requested.connect(self._on_regenerate)

    def _load_demo_data(self):
        """Load initial demo data."""
        self._load_example(1)

    def _load_example(self, example_num: int):
        """Load example translation.

        Args:
            example_num: Example number (1, 2, or 3)
        """
        if example_num == 1:
            translation = self._create_simple_example()
        elif example_num == 2:
            translation = self._create_word_order_example()
        elif example_num == 3:
            translation = self._create_hyphenated_example()
        else:
            return

        # Save translation
        saved = self.service.save_translation(translation)
        self.translation_id = saved.uuid
        sentence = saved.sentences[0]
        self.sentence_uuid = sentence.uuid

        # Load into editor
        self.editor.load_sentence(sentence)

    def _create_simple_example(self) -> Translation:
        """Create simple alignment example."""
        return Translation(
            uuid=uuid4(),
            title="Example 1: Simple Alignment",
            source_language=SUPPORTED_LANGUAGES["en"],
            target_language=SUPPORTED_LANGUAGES["de"],
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="The cat sat on the mat",
                    natural_translation="Die Katze saß auf der Matte",
                    word_alignments=[
                        WordAlignment(source_word="The", target_word="Die", position=0),
                        WordAlignment(source_word="cat", target_word="Katze", position=1),
                        WordAlignment(source_word="sat", target_word="saß", position=2),
                        WordAlignment(source_word="on", target_word="auf", position=3),
                        WordAlignment(source_word="the", target_word="der", position=4),
                        WordAlignment(source_word="mat", target_word="Matte", position=5),
                    ],
                )
            ],
        )

    def _create_word_order_example(self) -> Translation:
        """Create example with word order changes."""
        return Translation(
            uuid=uuid4(),
            title="Example 2: Word Order Changes",
            source_language=SUPPORTED_LANGUAGES["en"],
            target_language=SUPPORTED_LANGUAGES["de"],
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="I will miss you",
                    natural_translation="Ich werde dich vermissen",
                    word_alignments=[
                        WordAlignment(source_word="I", target_word="Ich", position=0),
                        WordAlignment(source_word="will", target_word="werde", position=1),
                        WordAlignment(source_word="miss", target_word="vermissen", position=2),
                        WordAlignment(source_word="you", target_word="dich", position=3),
                    ],
                )
            ],
        )

    def _create_hyphenated_example(self) -> Translation:
        """Create example with hyphenated alignment."""
        return Translation(
            uuid=uuid4(),
            title="Example 3: Hyphenated Words",
            source_language=SUPPORTED_LANGUAGES["es"],
            target_language=SUPPORTED_LANGUAGES["de"],
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="Yo te extrañaré",
                    natural_translation="Ich werde dich vermissen",
                    word_alignments=[
                        WordAlignment(source_word="Yo", target_word="Ich", position=0),
                        WordAlignment(source_word="te", target_word="dich", position=1),
                        WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
                    ],
                )
            ],
        )

    def _on_save(self, alignments: list):
        """Handle save request.

        Args:
            alignments: List of WordAlignment objects
        """
        if not self.translation_id or not self.sentence_uuid:
            QMessageBox.warning(self, "Error", "No translation loaded")
            return

        try:
            self.service.update_sentence_alignment(
                translation_id=self.translation_id, sentence_uuid=self.sentence_uuid, alignments=alignments
            )

            QMessageBox.information(
                self,
                "Success",
                (
                    f"Alignment saved successfully!\n\n"
                    f"Updated {len(alignments)} word mappings.\n"
                    f"Storage: {self.storage_path}"
                ),
            )

            # Reload to show persistence
            reloaded = self.service.get_translation(self.translation_id)
            if reloaded:
                sentence = next((s for s in reloaded.sentences if s.uuid == self.sentence_uuid), None)
                if sentence:
                    self.editor.load_sentence(sentence)

        except ValueError as e:
            QMessageBox.critical(self, "Validation Error", f"Invalid alignment:\n\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed:\n\n{e}")

    def _on_regenerate(self, sentence):
        """Handle regenerate request.

        Args:
            sentence: Sentence to regenerate
        """
        QMessageBox.information(
            self,
            "Regenerate",
            (
                "Regeneration requires an AI provider.\n\n"
                "This demo uses static examples without AI integration.\n\n"
                "In production, this would call TranslationService.update_sentence_natural()\n"
                "with a configured AI provider."
            ),
        )

    def closeEvent(self, event):  # noqa: N802
        """Clean up on close."""
        # Clean up temp directory
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
        event.accept()


def main():
    """Run demo application."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Birkenbihl Alignment Editor Demo")
    app.setOrganizationName("Birkenbihl")

    window = DemoWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
