"""Single supervisor agent using Google Gemini's automatic Python function calling.

The agent's tools are independent deterministic functions, following the separation
between orchestration and business rules used in the previous multi-agent project.
"""
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from app.prompts import SYSTEM_PROMPT
from app.services.database import initialize_database
from app.tools.store import (
    search_products, get_product, get_active_promotions,
    get_order_status, get_store_policy, calculate_payment,
)


class StoreAgent:
    """A session-scoped chat with read-only, dynamically chosen tools."""

    def __init__(self):
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key or api_key == "put_your_key_here":
            raise RuntimeError("Set GEMINI_API_KEY in .env. See README.md")
        initialize_database()
        self.client = genai.Client(api_key=api_key)
        self.model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            tools=[
                search_products, get_product, get_active_promotions,
                get_order_status, get_store_policy, calculate_payment,
            ],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=6),
        )
        self.chat = self.client.chats.create(model=self.model, config=config)

    def send(self, text: str) -> str:
        if not text.strip():
            return "Me conta como posso ajudar com seu instrumento!"
        response = self.chat.send_message(text)
        return response.text or "Não consegui elaborar uma resposta. Você pode reformular sua pergunta?"
