from app.services.policies import retrieve_policy


def test_returns_policy_is_grounded_in_pdf():
    result = retrieve_policy("posso devolver compra online por arrependimento?")
    assert result["excerpts"]
    assert any("7 (sete) dias" in e["text"] or "7 dias" in e["text"] for e in result["excerpts"])


def test_payment_policy_is_grounded_in_pdf():
    result = retrieve_policy("pagamento pix")
    assert any("PIX" in e["text"] for e in result["excerpts"])


def test_no_policy_match_returns_uncertainty():
    result = retrieve_policy("astronauta marciano ultravioleta")
    assert "message" in result
