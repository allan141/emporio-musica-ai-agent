
"""Automated multilingual policy retrieval tests."""

import pytest

from app.services.policies import retrieve_policy


@pytest.mark.parametrize(
    "question, expected_page",
    [
        # Store opening hours
        ("Qual é o horário de funcionamento?", 2),
        ("What are your opening hours?", 2),
        ("¿Cuál es el horario de atención?", 2),

        # Online withdrawal policy
        ("Posso devolver uma compra online?", 4),
        ("Can I return an online purchase?", 4),
        ("¿Puedo devolver una compra en línea?", 4),

        # Promotions and PIX payment rules
        ("¿El descuento PIX se acumula con promociones?", 6),
    ],
)
def test_multilingual_policy_retrieval(question, expected_page):
    result = retrieve_policy(question)

    assert "excerpts" in result, (
        f"No policy excerpts returned for: {question}"
    )

    pages = [
        excerpt["pdf_page"]
        for excerpt in result["excerpts"]
    ]

    assert expected_page in pages, (
        f"Expected PDF page {expected_page}, "
        f"but retrieved {pages} for: {question}"
    )


def test_policy_source_is_provided():
    result = retrieve_policy("What are your opening hours?")

    assert "source" in result
    assert result["source"]
