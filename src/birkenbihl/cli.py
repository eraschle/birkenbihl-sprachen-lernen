"""Birkenbihl CLI - Command-line interface for the Birkenbihl language learning app."""

from pathlib import Path
from uuid import UUID

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from birkenbihl.app import DEFAULT_PROVIDER, get_service
from birkenbihl.models.translation import Translation

console = Console()


def display_translation(translation: Translation) -> None:
    """Display a translation with rich formatting."""
    # Header
    title = translation.title or f"Translation {str(translation.id)[:8]}"
    header = f"[bold cyan]{title}[/bold cyan]"
    lang_info = f"[dim]{translation.source_language} → {translation.target_language}[/dim]"
    console.print(Panel(f"{header}\n{lang_info}", border_style="cyan"))

    # Sentences
    for idx, sentence in enumerate(translation.sentences, 1):
        console.print(f"\n[bold yellow]Sentence {idx}:[/bold yellow]")
        console.print(f"  [dim]Original:[/dim]  {sentence.source_text}")
        console.print(f"  [dim]Natural:[/dim]   {sentence.natural_translation}")
        console.print(f"  [dim]Word-by-Word:[/dim] {sentence.word_alignments}")

        if sentence.word_alignments:
            console.print("\n  [bold]Alignments:[/bold]")
            table = Table(show_header=True, box=None, padding=(0, 1))
            table.add_column("Source", style="green")
            table.add_column("Target", style="blue")

            for alignment in sentence.word_alignments:
                table.add_row(alignment.source_word, alignment.target_word)

            console.print(table)

    console.print()


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
    type=click.Choice(["openai", "anthropic"]),
    default=DEFAULT_PROVIDER,
    help=f"AI provider to use (default: {DEFAULT_PROVIDER})",
)
@click.option(
    "--model",
    "-m",
    help="Model to use (e.g., openai:gpt-4o, anthropic:claude-3-5-sonnet-20241022)",
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
    title: str | None,
    provider: str,
    model: str | None,
    storage: Path | None,
):
    """Translate text using the Birkenbihl method.

    Examples:
        birkenbihl translate "Hello world" -s en -t de
        birkenbihl translate "Yo te extrañaré" --title "Missing you"
        birkenbihl translate "Hello" -p anthropic -m claude-3-5-sonnet-20241022
    """
    try:
        with console.status("[bold green]Translating...", spinner="dots"):
            service = get_service(provider, model, storage)

            if source:
                result = service.translate_and_save(text, source, target, title)
            else:
                result = service.auto_detect_and_translate(text, target, title)

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
        service = get_service(storage_path=storage)
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

        for t in translations:
            title = t.title or "[dim]Untitled[/dim]"
            langs = f"{t.source_language} → {t.target_language}"
            updated = t.updated_at.strftime("%Y-%m-%d %H:%M")
            table.add_row(
                str(t.id)[:8] + "...",
                title,
                langs,
                str(len(t.sentences)),
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
        service = get_service(storage_path=storage)

        # Try to find by partial ID if not full UUID
        if len(translation_id) < 36:
            translations = service.list_all_translations()
            matches = [t for t in translations if str(t.id).startswith(translation_id)]

            if not matches:
                console.print(
                    f"[bold red]Error:[/bold red] No translation found with ID starting with {translation_id}"
                )
                raise click.Abort()
            if len(matches) > 1:
                console.print("[bold red]Error:[/bold red] Ambiguous ID. Multiple matches found:")
                for t in matches:
                    console.print(f"  - {t.id}")
                raise click.Abort()

            translation_id = str(matches[0].id)

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
        service = get_service(storage_path=storage)

        # Try to find by partial ID if not full UUID
        if len(translation_id) < 36:
            translations = service.list_all_translations()
            matches = [t for t in translations if str(t.id).startswith(translation_id)]

            if not matches:
                console.print(
                    f"[bold red]Error:[/bold red] No translation found with ID starting with {translation_id}"
                )
                raise click.Abort()
            if len(matches) > 1:
                console.print("[bold red]Error:[/bold red] Ambiguous ID. Multiple matches found:")
                for t in matches:
                    console.print(f"  - {t.id}")
                raise click.Abort()

            translation_id = str(matches[0].id)

        success = service.delete_translation(UUID(translation_id))

        if success:
            console.print(
                f"[bold green]✓[/bold green] Translation deleted: {translation_id[:8]}..."
            )
        else:
            console.print(f"[bold red]Error:[/bold red] Translation not found: {translation_id}")
            raise click.Abort()

    except ValueError as exc:
        console.print(f"[bold red]Error:[/bold red] Invalid UUID: {exc}")
        raise click.Abort() from exc
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise click.Abort() from exc
