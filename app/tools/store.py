"""Read-only tools. Money/eligibility rules stay deterministic in Python."""
from decimal import Decimal, ROUND_HALF_UP
from app.services.database import connect
from app.services.policies import normalize, retrieve_policy


def money(amount: Decimal) -> str:
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"R$ {rounded:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _amount(value) -> Decimal:
    return Decimal(str(value))


def _catalog():
    with connect() as db:
        return [dict(row) for row in db.execute("""
            SELECT p.product_id, p.name, p.description, p.price_brl, p.stock_quantity,
                   p.status, c.name AS category, pr.discount_percent, pr.description AS promotion
            FROM products p
            JOIN categories c ON c.category_id = p.category_id
            LEFT JOIN promotions pr ON pr.product_id = p.product_id AND pr.is_active = 1
        """).fetchall()]


def _present_product(row: dict) -> dict:
    original = _amount(row["price_brl"])
    percent = _amount(row["discount_percent"] or 0)
    final_price = original * (Decimal("1") - percent / Decimal("100"))
    return {
        "product_id": row["product_id"], "name": row["name"], "category": row["category"],
        "status": row["status"], "stock_quantity": row["stock_quantity"],
        "available": row["status"] == "active" and row["stock_quantity"] > 0,
        "original_price": money(original), "promotion_percent": str(percent) if percent else "0",
        "current_price": money(final_price), "promotion_name": row["promotion"] if percent else None,
        "note": "CSV snapshot, not a live inventory or promotion feed",
    }


def search_products(term: str, max_price: float = 0.0, in_stock_only: bool = True, limit: int = 5) -> dict:
    """Search instruments by model/brand/category, with optional maximum BRL price.

    Args:
        term: Product, brand or category. Use e.g. violão, Yamaha, teclado.
        max_price: Upper BRL price limit; 0 means no limit.
        in_stock_only: Only show active products with stock > 0.
        limit: Maximum number of matches (1..10).
    """
    if max_price < 0:
        return {"error": "max_price must not be negative"}
    tokens = normalize(term).split()
    found = []
    for row in _catalog():
        haystack = normalize(" ".join(str(row[k]) for k in ("name", "category", "description")))
        if tokens and not all(token in haystack for token in tokens):
            continue
        item = _present_product(row)
        if in_stock_only and not item["available"]:
            continue
        original = _amount(row["price_brl"])
        percent = _amount(row["discount_percent"] or 0)
        current = original * (1 - percent / 100)
        if max_price > 0 and current > _amount(max_price):
            continue
        found.append((current, item))
    found.sort(key=lambda pair: pair[0])
    return {"query": term, "matches": [item for _, item in found[:max(1, min(limit, 10))]], "total_matches": len(found), "snapshot": True}


def get_product(product_name: str) -> dict:
    """Get the catalog price and verified stock for a named instrument.

    Args:
        product_name: Instrument brand and/or model to look up.
    """
    candidates = [row for row in _catalog() if normalize(product_name) in normalize(row["name"])]
    if not candidates:
        return {"found": False, "message": "Product not found in current CSV snapshot"}
    return {"found": True, "products": [_present_product(row) for row in candidates[:8]]}


def get_active_promotions(limit: int = 10) -> dict:
    """Return products with the active promotion flag in the provided CSV.

    Args:
        limit: Maximum number of promotions (1..10).
    """
    found = [_present_product(row) for row in _catalog() if row["discount_percent"] and row["status"] == "active"]
    return {"promotions": found[:max(1, min(limit, 10))], "note": "No date-range fields exist; active means the dataset flag, not independently verified today"}


def get_order_status(order_id: int, customer_email: str) -> dict:
    """Get the status of an order after matching order ID to customer's email.

    Args:
        order_id: Numerical identifier of the order.
        customer_email: Email address associated with that order. Required for privacy.
    """
    if order_id < 1 or not customer_email.strip():
        return {"found": False, "message": "Order ID and customer email are required."}
    with connect() as db:
        row = db.execute("""
            SELECT o.order_id, o.order_date, o.status, o.total_brl,
                   o.tracking_code, o.estimated_delivery, o.payment_method
            FROM orders o JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = ? AND lower(c.email) = lower(?)
        """, (order_id, customer_email.strip())).fetchone()
    if row is None:
        return {"found": False, "message": "Order not found or credentials do not match. Do not reveal if the order ID exists."}
    result = dict(row)
    result["total_brl"] = money(_amount(result["total_brl"]))
    result["notice"] = "Historical order CSV snapshot. Status, shipment and ETA are not updated in real time; estimated dates may be past."
    return {"found": True, "order": result}


def get_store_policy(topic: str) -> dict:
    """Retrieve relevant sections from the official store policy PDF.

    Args:
        topic: Topic or question about address, hours, PIX, returns, delivery, promotions, warranty or privacy.
    """
    return retrieve_policy(topic)


def calculate_payment(product_id: int, method: str, installments: int = 1) -> dict:
    """Calculate PIX or credit-card payment applying the documented discount rules.

    Args:
        product_id: Numerical product identifier found in the catalog.
        method: Payment method: pix or credit.
        installments: Credit-card installments between 1 and 12; otherwise 1.
    """
    candidates = [r for r in _catalog() if r["product_id"] == product_id]
    if not candidates:
        return {"error": "Unknown product ID"}
    row = candidates[0]
    if row["status"] != "active" or row["stock_quantity"] <= 0:
        return {"error": "Product currently unavailable in the CSV snapshot"}
    original = _amount(row["price_brl"])
    discount = _amount(row["discount_percent"] or 0)
    price = (original * (1 - discount / 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    method = normalize(method)
    if method == "pix":
        if discount == 0:
            price = (original * Decimal("0.95")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {"product": row["name"], "payment_method": "pix", "total": money(price),
                "pix_discount_applied": discount == 0,
                "note": "PIX discount cannot be combined with an active product promotion"}
    if method != "credit":
        return {"error": "Only pix and credit estimates are implemented"}
    if installments < 1 or installments > 12:
        return {"error": "Choose between 1 and 12 installments"}
    installment = (price / installments).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    min_installment = Decimal("50") if installments <= 3 else Decimal("80") if installments <= 6 else Decimal("100")
    if installment < min_installment:
        return {"error": "Installment below the store policy minimum", "minimum_per_installment": money(min_installment)}
    return {"product": row["name"], "payment_method": "credit", "installments": installments,
            "approximate_installment": money(installment), "total": money(price),
            "note": "Installments are rounded for display; final card processing may adjust cents."}
