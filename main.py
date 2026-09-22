import os
import sys
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from dotenv import load_dotenv

import db
import ai
from review import review_card

load_dotenv()
app = typer.Typer(help="Smart Study - AI-powered study companion")
console = Console()


@app.command()
def create_deck(name: str = typer.Argument(..., help="Name of the deck"),
                description: str = typer.Option("", help="Deck description")):
    """Create a new flashcard deck."""
    db.init_db()
    deck_id = db.add_deck(name, description)
    console.print(f"[green]✓[/green] Created deck '{name}' (id: {deck_id})")


@app.command()
def list_decks():
    """List all decks."""
    db.init_db()
    decks = db.get_decks()
    if not decks:
        console.print("[dim]No decks yet. Create one with: smart-study create-deck <name>[/dim]")
        return
    table = Table(title="Your Decks")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Created")
    for d in decks:
        card_count = len(db.get_all_flashcards(d.id))
        table.add_row(str(d.id), f"{d.name} ({card_count} cards)", d.description, d.created_at[:10])
    console.print(table)


@app.command()
def generate(deck_id: int = typer.Argument(..., help="Deck ID to add cards to"),
             file: str = typer.Option(None, help="Path to a text/markdown file"),
             count: int = typer.Option(5, help="Number of flashcards to generate")):
    """Generate flashcards from text using AI."""
    db.init_db()
    text = _get_text(file)
    if not text:
        return

    with console.status("[bold cyan]Generating flashcards with AI..."):
        try:
            cards = ai.generate_flashcards(text, count)
        except Exception as e:
            console.print(f"[red]AI error:[/red] {e}")
            return

    for card in cards:
        db.add_flashcard(deck_id, card["question"], card["answer"])

    console.print(f"[green]✓[/green] Generated {len(cards)} flashcards in deck {deck_id}")
    _show_cards(cards)


@app.command()
def quiz(deck_id: int = typer.Argument(None, help="Deck ID (optional, for context)"),
         file: str = typer.Option(None, help="Path to a text/markdown file"),
         count: int = typer.Option(5, help="Number of questions")):
    """Take a quiz generated from your material."""
    db.init_db()
    text = _get_text(file)
    if not text:
        return

    with console.status("[bold cyan]Generating quiz with AI..."):
        try:
            questions = ai.generate_quiz(text, count)
        except Exception as e:
            console.print(f"[red]AI error:[/red] {e}")
            return

    score = 0
    for i, q in enumerate(questions, 1):
        console.print(f"\n[bold]Q{i}: {q.question}[/bold]")
        for j, opt in enumerate(q.options):
            console.print(f"  {j + 1}. {opt}")
        answer = IntPrompt.ask("Your answer (1-4)", choices=["1", "2", "3", "4"])
        if answer - 1 == q.correct_answer:
            console.print("[green]✓ Correct![/green]")
            score += 1
        else:
            console.print(f"[red]✗ Wrong.[/red] Answer: {q.options[q.correct_answer]}")
        if q.explanation:
            console.print(f"[dim]{q.explanation}[/dim]")

    console.print(f"\n[bold]Score: {score}/{len(questions)}[/bold]")


@app.command()
def summary(file: str = typer.Option(None, help="Path to a text/markdown file"),
             detail: str = typer.Option("medium", help="brief, medium, or detailed")):
    """Generate a summary of your material."""
    db.init_db()
    text = _get_text(file)
    if not text:
        return

    with console.status("[bold cyan]Generating summary with AI..."):
        try:
            result = ai.generate_summary(text, detail)
        except Exception as e:
            console.print(f"[red]AI error:[/red] {e}")
            return

    console.print(Panel(result, title="Summary", border_style="blue"))


@app.command()
def review(deck_id: int = typer.Option(None, help="Deck ID (review all if omitted)")):
    """Review due flashcards using spaced repetition."""
    db.init_db()
    due = db.get_due_flashcards(deck_id)
    if not due:
        console.print("[green]✓[/green] No cards due for review. You're all caught up!")
        return

    console.print(f"[bold]Reviewing {len(due)} card(s). Rate each 0-5:[/bold]")
    console.print("[dim]0=forgot  1=almost  2=hard  3=okay  4=good  5=easy[/dim]\n")

    for i, card in enumerate(due, 1):
        console.print(f"[bold cyan]Card {i}/{len(due)}[/bold cyan]")
        console.print(f"  Q: {card.question}")
        Prompt.ask("  [dim]Press Enter to reveal answer[/dim]", default="", show_default=False)
        console.print(f"  A: [green]{card.answer}[/green]")
        quality = IntPrompt.ask("  Rate (0-5)", choices=["0", "1", "2", "3", "4", "5"])

        updated = review_card(card, quality)
        db.update_flashcard(updated)
        console.print(f"  [dim]Next review: {updated.next_review}[/dim]\n")

    console.print("[green]✓[/green] Review session complete!")


@app.command()
def stats():
    """Show study statistics."""
    db.init_db()
    s = db.get_stats()
    table = Table(title="Study Stats")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="cyan")
    table.add_row("Total decks", str(s["total_decks"]))
    table.add_row("Total cards", str(s["total_cards"]))
    table.add_row("Cards due", str(s["due_cards"]))
    table.add_row("Cards reviewed", str(s["reviewed_cards"]))
    console.print(table)


def _get_text(file_path: str | None) -> str:
    if file_path:
        if not os.path.exists(file_path):
            console.print(f"[red]File not found:[/red] {file_path}")
            return ""
        with open(file_path, "r") as f:
            return f.read()

    console.print("[bold]Paste your study material (press Ctrl+D when done):[/bold]")
    try:
        return sys.stdin.read()
    except KeyboardInterrupt:
        return ""


def _show_cards(cards: list[dict]):
    table = Table(title=f"{len(cards)} flashcards generated")
    table.add_column("#", style="cyan")
    table.add_column("Question", style="bold")
    for i, c in enumerate(cards, 1):
        table.add_row(str(i), c["question"])
    console.print(table)
    console.print("[dim]Answers saved to deck. Use 'review' to practice them.[/dim]")


if __name__ == "__main__":
    db.init_db()
    app()
