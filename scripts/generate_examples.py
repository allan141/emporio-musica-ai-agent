"""Capture genuine model conversations after API key configuration.

Run from project root: python -m scripts.generate_examples
"""
from pathlib import Path
from app.agent import StoreAgent

EXAMPLES = [
    ("catalog", ["Quais violões disponíveis custam até R$ 1000?", "Qual deles é o mais barato?"]),
    ("policies", ["Comprei online e me arrependi. Posso devolver?", "O frete de devolução é por minha conta?"]),
    ("promotions", ["Quais instrumentos estão com promoção na base de dados?", "Posso somar o desconto com o PIX?"]),
    ("privacy", ["Qual o status do pedido 8?", "Meu email é email-nao-cadastrado@exemplo.com"]),
]


def main():
    folder = Path(__file__).resolve().parents[1] / "examples"
    folder.mkdir(exist_ok=True)
    for name, questions in EXAMPLES:
        agent = StoreAgent()  # separate session for each example
        transcript = [f"# Conversation: {name}", "", "Captured through the configured Gemini API.", ""]
        for question in questions:
            reply = agent.send(question)
            transcript.extend([f"**Customer:** {question}", "", f"**Assistant:** {reply}", ""])
        (folder / f"{name}.md").write_text("\n".join(transcript), encoding="utf-8")
        print(f"Saved examples/{name}.md")


if __name__ == "__main__":
    main()
