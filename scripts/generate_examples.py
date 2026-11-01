
"""Generate real customer service conversations using Gemini.

Usage:
    python -m scripts.generate_examples
    python -m scripts.generate_examples privacy
"""

import math
import re
import sys
import time
from pathlib import Path

from google.genai.errors import ClientError

from app.agent import StoreAgent


EXAMPLES = [
    (
        "catalog",
        [
            "Which acoustic guitars are available for under BRL 1,000?",
            "Which one is the cheapest?",
        ],
    ),
    (
        "policies",
        [
            "I bought an instrument online and changed my mind. Can I return it?",
            "Who pays for the return shipping?",
        ],
    ),
    (
        "promotions",
        [
            "Which instruments are marked as having active promotions in the provided dataset?",
            "Can I combine the promotional price with the 5% PIX discount?",
        ],
    ),
    (
        "privacy",
        [
            "What is the status of order 8?",
            "My email is email-nao-cadastrado@exemplo.com",
            "Actually, my registered email is anacarol.ferreira@coldmail.com",
        ],
    ),
]


def send_with_retry(agent, question, max_attempts=6):
    """Retry Gemini requests when the free-tier rate limit is hit."""

    for attempt in range(1, max_attempts + 1):
        try:
            return agent.send(question)

        except ClientError as error:
            message = str(error)

            if "429" not in message and "RESOURCE_EXHAUSTED" not in message:
                raise

            if attempt == max_attempts:
                raise

            match = re.search(
                r"Please retry in\s+([\d.]+)s",
                message,
            )

            if match:
                delay = math.ceil(float(match.group(1))) + 3
            else:
                delay = min(20 * attempt, 60)

            delay = max(delay, 10)

            print(
                f"Rate limit reached. "
                f"Retrying in {delay} seconds "
                f"(attempt {attempt}/{max_attempts})..."
            )

            time.sleep(delay)


def main():
    folder = Path(__file__).resolve().parents[1] / "examples"
    folder.mkdir(exist_ok=True)

    selected = sys.argv[1] if len(sys.argv) > 1 else None

    valid_names = {name for name, _ in EXAMPLES}

    if selected and selected not in valid_names:
        raise ValueError(
            f"Unknown scenario: {selected}. "
            f"Choose one of: {', '.join(sorted(valid_names))}"
        )

    for name, questions in EXAMPLES:
        if selected and name != selected:
            continue

        print(f"Generating conversation: {name}")

        agent = StoreAgent()

        transcript = [
            f"# Conversation: {name}",
            "",
            "Captured through the configured Gemini API.",
            "",
        ]

        for index, question in enumerate(questions):
            print(f"Processing question {index + 1}/{len(questions)}")

            reply = send_with_retry(agent, question)

            transcript.extend([
                f"**Customer:** {question}",
                "",
                f"**Assistant:** {reply}",
                "",
            ])

            if index < len(questions) - 1:
                time.sleep(10)

        output = folder / f"{name}.md"

        output.write_text(
            "\n".join(transcript),
            encoding="utf-8",
        )

        print(f"Saved examples/{name}.md")


if __name__ == "__main__":
    main()
