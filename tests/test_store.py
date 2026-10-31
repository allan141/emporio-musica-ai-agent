from app.services.database import initialize_database, connect
from app.tools.store import (
    search_products, get_product, get_active_promotions,
    get_order_status, calculate_payment,
)


def test_imported_counts():
    initialize_database()
    expected = {"categories": 9, "customers": 50, "products": 65, "orders": 20, "order_items": 22, "promotions": 25}
    with connect() as db:
        for table, count in expected.items():
            assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == count


def test_available_guitars_budget():
    result = search_products("violão", max_price=1000)
    assert result["total_matches"] > 0
    assert all(p["available"] for p in result["matches"])
    # Results are price-sorted and limited; a specific brand requires a separate query.
    yamaha = search_products("Yamaha", max_price=1000, limit=10)
    assert any("Yamaha" in p["name"] for p in yamaha["matches"])


def test_product_not_found():
    assert get_product("NotARealModel123")["found"] is False


def test_active_promotions_are_from_csv():
    result = get_active_promotions()
    assert len(result["promotions"]) == 4


def test_no_order_without_matching_email():
    assert get_order_status(1, "wrong@example.com")["found"] is False
    assert get_order_status(1, "")["found"] is False


def test_verified_order():
    result = get_order_status(1, "pedro.oliveira@jmail.com")
    assert result["found"] is True
    assert result["order"]["status"] == "delivered"
    assert "email" not in result["order"]


def test_pix_without_promotion_discount():
    result = calculate_payment(81, "pix")
    assert result["total"] == "R$ 569,91"
    assert result["pix_discount_applied"] is True


def test_pix_does_not_stack_with_promotion():
    result = calculate_payment(94, "pix")
    assert result["pix_discount_applied"] is False


def test_minimum_card_installment():
    result = calculate_payment(81, "credit", 12)
    assert "error" in result
