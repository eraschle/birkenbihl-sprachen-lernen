"""Birkenbihl CLI - Command-line interface for the Birkenbihl language learning app."""

from pathlib import Path
from uuid import UUID

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from birkenbihl.app import get_translator
from birkenbihl.models.cli_config import TranslationConfig
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.presenters import (
    AlignmentDisplayModel,
    SentenceDisplayModel,
    TranslationPresenter,
)
from birkenbihl.services import language_service as ls
from birkenbihl.services import path_service as ps
from birkenbihl.services.settings_service import SettingsService

console = Console()
presenter = TranslationPresenter()


def display_translation(translation: Translation) -> None:
    """Display a translation with rich formatting using Presenter."""
    display_model = presenter.format_translation(translation)

    _display_header(display_model.title, display_model.language_pair)
    _display_sentences(display_model.sentences)
    console.print()


def _display_header(title: str, language_pair: str) -> None:
    """Display translation header.

    Args:
        title: Translation title
        language_pair: Formatted language pair
    """
    header = f"[bold cyan]{title}[/bold cyan]"
    lang_info = f"[dim]{language_pair}[/dim]"
    console.print(Panel(f"{header}\n{lang_info}", border_style="cyan"))


def _display_sentences(sentences: list[SentenceDisplayModel]) -> None:
    """Display all sentences with alignments.

    Args:
        sentences: List of SentenceDisplayModel
    """
    for sentence in sentences:
        _display_single_sentence(sentence)


def _display_single_sentence(sentence: SentenceDisplayModel) -> None:
    """Display a single sentence.

    Args:
        sentence: SentenceDisplayModel
    """
    console.print(f"\n[bold yellow]Sentence {sentence.index}:[/bold yellow]")
    console.print(f"  [dim]Original:[/dim]  {sentence.source_text}")
    console.print(f"  [dim]Natural:[/dim]   {sentence.natural_translation}")
    console.print(f"  [dim]Word-by-Word:[/dim] {sentence.word_by_word}")

    if sentence.alignments:
        _display_alignments(sentence.alignments)


def _display_alignments(alignments: list[AlignmentDisplayModel]) -> None:
    """Display alignment table.

    Args:
        alignments: List of AlignmentDisplayModel
    """
    console.print("\n  [bold]Alignments:[/bold]")
    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("Source", style="green")
    table.add_column("Target", style="blue")

    for alignment in alignments:
        table.add_row(alignment.source_word, alignment.target_word)

    console.print(table)


def _show_provider_error(provider_name: str, available: list[ProviderConfig]) -> None:
    """Display provider not found error message.

    Args:
        provider_name: Name of provider that was not found
        available: List of available providers
    """
    console.print(f"[bold red]Error:[/bold red] Provider '{provider_name}' not found")
    console.print("\nAvailable providers:")
    for p in available:
        console.print(f"  - {p.name}")


def _get_named_provider(settings_service: SettingsService, name: str) -> ProviderConfig:
    """Get provider by name or abort.

    Args:
        settings_service: SettingsService instance
        name: Provider name to find

    Returns:
        Matching ProviderConfig

    Raises:
        click.Abort: If provider not found
    """
    settings = settings_service.get_settings()
    matching = [p for p in settings.providers if p.name == name]
    if not matching:
        _show_provider_error(name, settings.providers)
        raise click.Abort()
    return matching[0]


def _get_provider_config(service: SettingsService, provider_name: str | None) -> ProviderConfig:
    """Get provider configuration from settings.

    Args:
        service: SettingsService instance
        provider_name: Optional provider name, uses default if None

    Returns:
        ProviderConfig for selected provider

    Raises:
        click.Abort: If provider not found or no default configured
    """
    if provider_name:
        return _get_named_provider(service, provider_name)

    provider = service.get_default_provider()
    if provider is None:
        console.print("[bold red]Error:[/bold red] No provider configured")
        raise click.Abort()
    return provider


def _build_config(
    text: str, source: str | None, target: str, title: str | None, provider: str | None, storage: Path | None
) -> TranslationConfig:
    """Build TranslationConfig from CLI arguments.

    Args:
        text: Text to translate
        source: Optional source language code
        target: Target language code
        title: Optional translation title
        provider: Optional provider name
        storage: Optional storage path

    Returns:
        TranslationConfig instance
    """
    return TranslationConfig(
        text=text,
        source=ls.get_language_by(source) if source else None,
        target=ls.get_language_by(target),
        title=title,
        provider_name=provider,
        storage_path=storage,
    )


def _execute_translation(config: TranslationConfig, provider: ProviderConfig) -> Translation:
    """Execute translation with given configuration.

    Args:
        config: Translation configuration
        provider: Provider configuration

    Returns:
        Saved Translation result
    """
    from birkenbihl.services.translation_service import TranslationService
    from birkenbihl.storage import JsonStorageProvider

    translator = get_translator(provider)
    storage = JsonStorageProvider(config.storage_path)
    service = TranslationService(translator, storage)

    title = config.title or "Translation"

    if config.source:
        translation = service.translate(config.text, config.source, config.target, title)
        return service.save_translation(translation)
    return service.auto_detect_and_translate(config.text, config.target, title)


@click.group()
@click.version_option(version="0.1.0", prog_name="birkenbihl")
def cli():
    """Birkenbihl - Language learning using the Birkenbihl method.

    Provides dual translations (natural + word-by-word) to help you
    understand foreign language structure.
    """
    pass


@cli.command()
@click.argument("text")
@click.option("--source", "-s", help="Source language (en, es, de). Auto-detected if not specified.")
@click.option("--target", "-t", default="de", help="Target language (default: de)")
@click.option("--title", help="Optional title for this translation")
@click.option("--provider", "-p", help="Provider name from settings.yaml (uses default if not specified)")
@click.option("--storage", type=click.Path(path_type=Path), help="Custom storage file path")
def translate(
    text: str, source: str | None, target: str, title: str | None, provider: str | None, storage: Path | None
):
    """Translate text using the Birkenbihl method.

    Examples:
        birkenbihl translate "Hello world" -s en -t de
        birkenbihl translate "Yo te extrañaré" --title "Missing you"
        birkenbihl translate "Hello" -p "Claude Sonnet"
    """
    try:
        settings_service = SettingsService(ps.get_setting_path())
        settings_service.load_settings()
        config = _build_config(text, source, target, title, provider, storage)
        provider_config = _get_provider_config(settings_service, config.provider_name)

        with console.status("[bold green]Translating...", spinner="dots"):
            result = _execute_translation(config, provider_config)

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
