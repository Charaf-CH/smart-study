from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Flashcard:
    id: int
    deck_id: int
    question: str
    answer: str
    ease_factor: float = 2.5
    interval: int = 0
    repetitions: int = 0
    next_review: str = ""
    created_at: str = ""
    last_reviewed: str = ""


@dataclass
class QuizQuestion:
    question: str
    options: list[str] = field(default_factory=list)
    correct_answer: int = 0
    explanation: str = ""


@dataclass
class Deck:
    id: int
    name: str
    description: str = ""
    created_at: str = ""
