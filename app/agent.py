
"""Customer service agent using Google Gemini function calling.

Separates LLM orchestration from deterministic business rules
and records the names of tools invoked during each response.
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
        project_root = Path(__file__).resolve().parents[1]
        load_dotenv(dotenv_path=project_root / ".env")

        api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        if not api_key or api_key in {
            "put_your_key_here",
            "your_actual_api_key_here",
            "your_api_key_here",
        }:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "See .env.example and README.md."
            )

        initialize_database()

        self.client = genai.Client(api_key=api_key)

        self.model = (
            os.environ.get(
                "GEMINI_MODEL",
                "gemini-3.5-flash-lite",
            ).strip()
            or "gemini-3.5-flash-lite"
        )

        self.last_tool_calls = []

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            tools=[
                search_products,
                get_product,
                get_active_promotions,
                get_order_status,
                get_store_policy,
                calculate_payment,
            ],
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(
                    maximum_remote_calls=6,
                )
            ),
        )

        self.chat = self.client.chats.create(
            model=self.model,
            config=config,
        )

    
    def send(self, text: str) -> str:
        """Send a message and track tools executed in this turn."""

        self.last_tool_calls = []

        if not isinstance(text, str):
            raise TypeError("Customer message must be a string.")

        if not text.strip():
            return "Me conta como posso ajudar com seu instrumento!"

        # Remember where the current turn starts.
        history_start = len(
            self.chat.get_history(curated=True)
        )

        response = self.chat.send_message(text)

        # Examine only the history added by this message.
        new_history = self.chat.get_history(
            curated=True
        )[history_start:]

        for turn in new_history:
            for part in getattr(turn, "parts", None) or []:
                function_response = getattr(
                    part,
                    "function_response",
                    None,
                )

                if function_response and function_response.name:
                    self.last_tool_calls.append(
                        function_response.name
                    )

        if response.text and response.text.strip():
            return response.text.strip()

        return (
            "Não consegui elaborar uma resposta. "
            "Você pode reformular sua pergunta?"
        )
