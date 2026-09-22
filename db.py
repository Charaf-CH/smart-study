import sqlite3
from datetime import datetime, date
from models import Flashcard, Deck

DB_PATH = "smart_study.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS decks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deck_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            ease_factor REAL DEFAULT 2.5,
            interval_days INTEGER DEFAULT 0,
            repetitions INTEGER DEFAULT 0,
            next_review TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_reviewed TEXT DEFAULT '',
            FOREIGN KEY (deck_id) REFERENCES decks(id)
        );
    """)
    conn.commit()
    conn.close()


def add_deck(name: str, description: str = "") -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO decks (name, description, created_at) VALUES (?, ?, ?)",
        (name, description, datetime.now().isoformat()),
    )
    deck_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return deck_id


def get_decks() -> list[Deck]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM decks ORDER BY created_at DESC").fetchall()
    conn.close()
    return [Deck(id=r["id"], name=r["name"], description=r["description"], created_at=r["created_at"]) for r in rows]


def add_flashcard(deck_id: int, question: str, answer: str) -> int:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO flashcards (deck_id, question, answer, next_review, created_at) VALUES (?, ?, ?, ?, ?)",
        (deck_id, question, answer, now, now),
    )
    card_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return card_id


def get_due_flashcards(deck_id: int = None) -> list[Flashcard]:
    today = date.today().isoformat()
    conn = get_connection()
    if deck_id:
        rows = conn.execute(
            "SELECT * FROM flashcards WHERE deck_id = ? AND next_review <= ? ORDER BY next_review",
            (deck_id, today),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM flashcards WHERE next_review <= ? ORDER BY next_review",
            (today,),
        ).fetchall()
    conn.close()
    return [_row_to_flashcard(r) for r in rows]


def get_all_flashcards(deck_id: int = None) -> list[Flashcard]:
    conn = get_connection()
    if deck_id:
        rows = conn.execute("SELECT * FROM flashcards WHERE deck_id = ?", (deck_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM flashcards").fetchall()
    conn.close()
    return [_row_to_flashcard(r) for r in rows]


def update_flashcard(card: Flashcard):
    conn = get_connection()
    conn.execute(
        """UPDATE flashcards
           SET ease_factor = ?, interval_days = ?, repetitions = ?,
               next_review = ?, last_reviewed = ?
           WHERE id = ?""",
        (card.ease_factor, card.interval, card.repetitions,
         card.next_review, card.last_reviewed, card.id),
    )
    conn.commit()
    conn.close()


def get_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) as c FROM flashcards").fetchone()["c"]
    today = date.today().isoformat()
    due = conn.execute(
        "SELECT COUNT(*) as c FROM flashcards WHERE next_review <= ?", (today,)
    ).fetchone()["c"]
    decks = conn.execute("SELECT COUNT(*) as c FROM decks").fetchone()["c"]
    reviewed = conn.execute(
        "SELECT COUNT(*) as c FROM flashcards WHERE last_reviewed != ''"
    ).fetchone()["c"]
    conn.close()
    return {"total_cards": total, "due_cards": due, "total_decks": decks, "reviewed_cards": reviewed}


def _row_to_flashcard(row) -> Flashcard:
    return Flashcard(
        id=row["id"],
        deck_id=row["deck_id"],
        question=row["question"],
        answer=row["answer"],
        ease_factor=row["ease_factor"],
        interval=row["interval_days"],
        repetitions=row["repetitions"],
        next_review=row["next_review"],
        created_at=row["created_at"],
        last_reviewed=row["last_reviewed"],
    )
