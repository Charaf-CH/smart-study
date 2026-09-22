# Smart Study

AI-powered study companion CLI. Paste your notes, generate flashcards, take quizzes, and review with spaced repetition.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your free Groq API key from https://console.groq.com/keys
```

## Usage

```bash
# Create a deck
python main.py create-deck "Algorithms"

# Generate flashcards from a file
python main.py generate 1 --file notes.txt --count 10

# Generate flashcards by pasting text
python main.py generate 1

# Review due flashcards
python main.py review

# Take a quiz
python main.py quiz --file notes.txt

# Get a summary
python main.py summary --file notes.txt --detail brief

# View stats
python main.py stats

# List your decks
python main.py list-decks
```

## How Spaced Repetition Works

Uses the SM-2 algorithm: cards you find easy are shown less often, cards you struggle with come back sooner. Each card tracks:
- **ease_factor** — how easy the card is (starts at 2.5)
- **interval** — days until next review
- **repetitions** — consecutive correct answers
