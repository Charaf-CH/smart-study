from datetime import date, timedelta
from models import Flashcard


def review_card(card: Flashcard, quality: int) -> Flashcard:
    """
    Update a flashcard using the SM-2 spaced repetition algorithm.

    quality: 0-5 rating
      0 - complete failure
      1 - wrong, but recognized the answer
      2 - wrong, answer seemed easy to recall
      3 - correct with serious difficulty
      4 - correct with some hesitation
      5 - perfect recall
    """
    today = date.today()
    card.last_reviewed = today.isoformat()

    if quality >= 3:
        if card.repetitions == 0:
            card.interval = 1
        elif card.repetitions == 1:
            card.interval = 6
        else:
            card.interval = round(card.interval * card.ease_factor)

        card.repetitions += 1
        card.ease_factor = max(
            1.3,
            card.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02),
        )
    else:
        card.repetitions = 0
        card.interval = 1

    card.next_review = (today + timedelta(days=card.interval)).isoformat()
    return card
