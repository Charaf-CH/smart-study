import json
import os
import httpx
from models import Flashcard, QuizQuestion

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("Error: GROQ_API_KEY not set. Add it to your .env file.")

    response = httpx.post(
        GROQ_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def generate_flashcards(text: str, count: int = 5) -> list[dict]:
    system = """You are a study assistant. Generate flashcard Q&A pairs from the given text.
Return ONLY valid JSON: an array of objects with "question" and "answer" keys.
Make questions clear and answers concise. No markdown, no extra text."""

    user = f"Generate exactly {count} flashcards from this material:\n\n{text}"

    raw = _call_llm(system, user)
    # Strip markdown code fences if the model adds them
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


def generate_quiz(text: str, count: int = 5) -> list[QuizQuestion]:
    system = """You are a study assistant. Generate multiple choice quiz questions from the given text.
Return ONLY valid JSON: an array of objects with keys:
- "question": the question text
- "options": array of exactly 4 answer choices
- "correct": index of correct answer (0-3)
- "explanation": brief explanation of why the answer is correct
No markdown, no extra text."""

    user = f"Generate exactly {count} quiz questions from this material:\n\n{text}"

    raw = _call_llm(system, user)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    items = json.loads(cleaned)
    return [
        QuizQuestion(
            question=q["question"],
            options=q["options"],
            correct_answer=q["correct"],
            explanation=q.get("explanation", ""),
        )
        for q in items
    ]


def generate_summary(text: str, detail: str = "medium") -> str:
    detail_guide = {
        "brief": "a brief 2-3 sentence overview",
        "medium": "a concise summary with key points in 1-2 paragraphs",
        "detailed": "a detailed summary covering all major concepts and details",
    }

    system = "You are a study assistant. Summarize the given text clearly and accurately."
    user = f"Provide {detail_guide.get(detail, detail_guide['medium'])} of this material:\n\n{text}"

    return _call_llm(system, user)
