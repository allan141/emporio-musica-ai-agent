
"""Customer service agent using Google Gemini function calling.

The architecture separates LLM orchestration, data retrieval,
and deterministic business rules through independent Python tools.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.prompts import SYSTEM_PROMPT
from app.services.database import initialize_database
from app.tools.store import (
    search_products,
    get_product,
    get_active_promotions,
    get_order_status,
    get_store_policy,
    calculate_payment,
)


class StoreAgent:
    """Session-scoped customer service agent with read-only tools."""

    def __init__(self):
        # Load configuration from the project root.
        project_root = Path(__file__).resolve().parents[1]
        env_path = project_root / ".env"

        load_dotenv(dotenv_path=env_path)

        api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        if not api_key or api_key in {
            "put_your_key_here",
            "your_actual_api_key_here",
            "your_api_key_here",
        }:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Create a .env file using .env.example."
            )

        # Initialize the local database from the challenge CSV files.
        initialize_database()

        # Configure Gemini.
        self.client = genai.Client(api_key=api_key)

        self.model = (
            os.environ.get(
                "GEMINI_MODEL",
                "gemini-3.5-flash-lite",
            ).strip()
            or "gemini-3.5-flash-lite"
        )

        # Available read-only business tools.
        tools = [
            search_products,
            get_product,
            get_active_promotions,
            get_order_status,
            get_store_policy,
            calculate_payment,
        ]

        # Configure the model and automatic function calling.
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            tools=tools,
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(
                    maximum_remote_calls=6,
                )
            ),
        )

        # Create a session-scoped conversation.
        self.chat = self.client.chats.create(
            model=self.model,
            config=config,
        )

    def send(self, text: str) -> str:
        """Send a customer message and return the model response."""

        if not isinstance(text, str):
            raise TypeError("Customer message must be a string.")

        if not text.strip():
            return (
                "Me conta como posso ajudar "
                "com seu instrumento!"
            )

        # API exceptions intentionally propagate to the caller.
        # Streamlit handles user-facing errors, while the example
        # generator handles temporary rate limits and retries.
        response = self.chat.send_message(text)

        if response.text and response.text.strip():
            return response.text.strip()

        return (
            "Não consegui elaborar uma resposta. "
            "Você pode reformular sua pergunta?"
        )
