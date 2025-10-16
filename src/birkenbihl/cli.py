"""Birkenbihl CLI - Command-line interface for the Birkenbihl language learning app."""

from pathlib import Path
from uuid import UUID

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from birkenbihl.app import get_translator
from birkenbihl.models.requests import TranslationRequest
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.presenters.models import SentencePresentation, TranslationPresentation
from birkenbihl.presenters.translation_presenter import TranslationPresenter
from birkenbihl.services import language_service as ls
from birkenbihl.services import path_service as ps
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService

console = Console()


def display_translation(translation: Translation) -> None:
    """Display translation with rich formatting using Presenter.

    Args:
        translation: Translation domain object to display
    """
    presenter = TranslationPresenter()
    data = presenter.present(translation)

    _display_header(data)
    for sentence in data.sentences:
        _display_sentence(sentence)
    console.print()


def _display_header(data: TranslationPresentation) -> None:
    """Display translation header with title and languages.

    Args:
        data: Translation presentation data
    """
    header = f"[bold cyan]{data.title}[/bold cyan]"
    lang_info = f"[dim]{data.source_language_name} → {data.target_language_name}[/dim]"
    console.print(Panel(f"{header}\n{lang_info}", border_style="cyan"))


def _display_sentence(sentence: SentencePresentation) -> None:
    """Display single sentence with translations and alignments.

    Args:
        sentence: Sentence presentation data
    """
    console.print(f"\n[bold yellow]Sentence {sentence.index}:[/bold yellow]")
    console.print(f"  [dim]Original:[/dim]  {sentence.source_text}")
    console.print(f"  [dim]Natural:[/dim]   {sentence.natural_translation}")

    if sentence.has_alignments:
        _display_alignments(sentence.alignments)


def _display_alignments(alignments: list[tuple[str, str]]) -> None:
    """Display word-by-word alignments in a table.

    Args:
        alignments: List of (source_word, target_word) tuples
    """
    console.print("\n  [bold]Alignments:[/bold]")
    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("Source", style="green")
    table.add_column("Target", style="blue")

    for source, target in alignments:
        table.add_row(source, target)

    console.print(table)


@click.group()
@click.version_option(version="0.1.0", prog_name="birkenbihl")
def cli():
    """Birkenbihl - Language learning using the Birkenbihl method.

    Provides dual translations (natural + word-by-word) to help you
    understand foreign language structure.
    """
    pass


def _load_settings_service() -> SettingsService:
    """Load and initialize settings service.

    Returns:
        Initialized SettingsService

    Raises:
        Exception: If settings cannot be loaded
    """
    settings_service = SettingsService(ps.get_setting_path())
    settings_service.load_settings()
    return settings_service


def _select_provider(settings_service: SettingsService, provider_name: str | None) -> ProviderConfig:
    """Select provider from settings or CLI argument.

    Args:
        settings_service: Initialized settings service
        provider_name: Provider name from CLI (None for default)

    Returns:
        Selected ProviderConfig

    Raises:
        click.Abort: If provider not found or not configured
    """
    if provider_name:
        settings = settings_service.get_settings()
        matching = [p for p in settings.providers if p.name == provider_name]
        if not matching:
            console.print(f"[bold red]Error:[/bold red] Provider '{provider_name}' not found")
            console.print("\nAvailable providers:")
            for p in settings.providers:
                console.print(f"  - {p.name}")
            raise click.Abort()
        return matching[0]

    provider = settings_service.get_default_provider()
    if provider is None:
        console.print("[bold red]Error:[/bold red] No provider configured in settings.yaml")
        raise click.Abort()
    return provider


def _create_translation_service(provider_config: ProviderConfig, storage_path: Path | None) -> TranslationService:
    """Create translation service with provider and storage.

    Args:
        provider_config: Provider configuration
        storage_path: Custom storage path (None for default)

    Returns:
        Initialized TranslationService
    """
    from birkenbihl.storage import JsonStorageProvider

    translator = get_translator(provider_config)
    storage_provider = JsonStorageProvider(storage_path)
    return TranslationService(translator, storage_provider)


def _execute_translation(
    service: TranslationService, text: str, source: str | None, target: str, title: str
) -> Translation:
    """Execute translation with auto-detect or explicit source language.

    Args:
        service: TranslationService instance
        text: Text to translate
        source: Source language code (None for auto-detect)
        target: Target language code
        title: Translation title

    Returns:
        Translation result
    """
    target_language = ls.get_language_by(target)

    if source:
        source_language = ls.get_language_by(source)
        request = TranslationRequest(
            text=text, source_lang=source_language, target_lang=target_language, title=title
        )
        translation = service.translate(request)
        return service.save_translation(translation)

    return service.auto_detect_and_translate(text, target_language, title)


@cli.command()
@click.argument("text")
@click.option(
    "--source",
    "-s",
    help="Source language (en, es, de). Auto-detected if not specified.",
)
@click.option(
    "--target",
    "-t",
    default="de",
    help="Target language (default: de)",
)
@click.option(
    "--title",
    help="Optional title for this translation",
)
@click.option(
    "--provider",
    "-p",
    help="Provider name from settings.yaml (uses default if not specified)",
)
@click.option(
    "--storage",
    type=click.Path(path_type=Path),
    help="Custom storage file path",
)
def translate(
    text: str,
    source: str | None,
    target: str,
    title: str,
    provider: str | None,
    storage: Path | None,
) -> None:
    """Translate text using the Birkenbihl method.

    Examples:
        birkenbihl translate "Hello world" -s en -t de
        birkenbihl translate "Yo te extrañaré" --title "Missing you"
        birkenbihl translate "Hello" -p "Claude Sonnet"
    """
    try:
        settings_service = _load_settings_service()
        provider_config = _select_provider(settings_service, provider)
        service = _create_translation_service(provider_config, storage)

        with console.status("[bold green]Translating...", spinner="dots"):
            result = _execute_translation(service, text, source, target, title)

        console.print("[bold green]✓[/bold green] Translation completed!")
        display_translation(result)

    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise click.Abort() from exc


@cli.command()
@click.option(
    "--storage",
    type=click.Path(path_type=Path),
    help="Custom storage file path",
)
def list(storage: Path | None):
    """List all saved translations."""
    try:
        from birkenbihl.services.translation_service import TranslationService
        from birkenbihl.storage import JsonStorageProvider

        storage_provider = JsonStorageProvider(storage)
        service = TranslationService(None, storage_provider)
        translations = service.list_all_translations()

        if not translations:
            console.print("[yellow]No translations found.[/yellow]")
            return

        table = Table(title="Saved Translations", show_header=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="green")
        table.add_column("Languages", style="blue")
        table.add_column("Sentences", justify="right")
        table.add_column("Updated", style="dim")

        for trans in translations:
            title = trans.title or "[dim]Untitled[/dim]"
            langs = f"{trans.source_language} → {trans.target_language}"
            updated = trans.updated_at.strftime("%Y-%m-%d %H:%M")
            table.add_row(
                str(trans.uuid)[:8] + "...",
                title,
                langs,
                str(len(trans.sentences)),
                updated,
            )

        console.print(table)

    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise click.Abort() from exc


@cli.command()
@click.argument("translation_id")
@click.option(
    "--storage",
    type=click.Path(path_type=Path),
    help="Custom storage file path",
)
def show(translation_id: str, storage: Path | None):
    """Show details of a specific translation.

    TRANSLATION_ID can be the full UUID or just the first 8 characters.
    """
    try:
        from birkenbihl.services.translation_service import TranslationService
        from birkenbihl.storage import JsonStorageProvider

        storage_provider = JsonStorageProvider(storage)
        service = TranslationService(None, storage_provider)

        # Try to find by partial ID if not full UUID
        if len(translation_id) < 36:
            translations = service.list_all_translations()
            matches = [trans for trans in translations if str(trans.uuid).startswith(translation_id)]

            if not matches:
                console.print(
                    f"[bold red]Error:[/bold red] No translation found with ID starting with {translation_id}"
                )
                raise click.Abort()
            if len(matches) > 1:
                console.print("[bold red]Error:[/bold red] Ambiguous ID. Multiple matches found:")
                for trans in matches:
                    console.print(f"  - {trans.uuid}")
                raise click.Abort()

            translation_id = str(matches[0].uuid)

        result = service.get_translation(UUID(translation_id))

        if result is None:
            console.print(f"[bold red]Error:[/bold red] Translation not found: {translation_id}")
            raise click.Abort()

        display_translation(result)

    except ValueError as exc:
        console.print(f"[bold red]Error:[/bold red] Invalid UUID: {exc}")
        raise click.Abort() from exc
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise click.Abort() from exc


@cli.command()
@click.argument("translation_id")
@click.option(
    "--storage",
    type=click.Path(path_type=Path),
    help="Custom storage file path",
)
@click.confirmation_option(prompt="Are you sure you want to delete this translation?")
def delete(translation_id: str, storage: Path | None):
    """Delete a translation.

    TRANSLATION_ID can be the full UUID or just the first 8 characters.
    """
    try:
        from birkenbihl.services.translation_service import TranslationService
        from birkenbihl.storage import JsonStorageProvider

        storage_provider = JsonStorageProvider(storage)
        service = TranslationService(None, storage_provider)

        # Try to find by partial ID if not full UUID
        if len(translation_id) < 36:
            translations = service.list_all_translations()
            matches = [trans for trans in translations if str(trans.uuid).startswith(translation_id)]

            if not matches:
                console.print(
                    f"[bold red]Error:[/bold red] No translation found with ID starting with {translation_id}"
                )
                raise click.Abort()
            if len(matches) > 1:
                console.print("[bold red]Error:[/bold red] Ambiguous ID. Multiple matches found:")
                for trans in matches:
                    console.print(f"  - {trans.uuid}")
                raise click.Abort()

            translation_id = str(matches[0].uuid)

        success = service.delete_translation(UUID(translation_id))

        if success:
            console.print(f"[bold green]✓[/bold green] Translation deleted: {translation_id[:8]}...")
        else:
            console.print(f"[bold red]Error:[/bold red] Translation not found: {translation_id}")
            raise click.Abort()

    except ValueError as exc:
        console.print(f"[bold red]Error:[/bold red] Invalid UUID: {exc}")
        raise click.Abort() from exc
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise click.Abort() from exc
