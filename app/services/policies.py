
"""Multilingual policy retrieval from the provided store manual."""

from pathlib import Path
import re
import unicodedata

import pymupdf


POLICY_PDF = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "politicas_da_loja.pdf"
)

# Page numbers below are zero-based PDF indexes.
# Keywords support Portuguese, English, and Spanish.

TOPICS = {
    "store": (
        1,
        (
            "loja", "endereco", "contato", "telefone",
            "localizacao", "cnpj",
            "store address", "address", "location", "contact",
            "tienda", "direccion", "ubicacion", "contacto",
            "telefono",
        ),
    ),

    "hours": (
        1,
        (
            "horario", "funcionamento", "aberto", "fecha",
            "domingo", "sabado", "feriado",
            "opening hours", "business hours", "opening",
            "closing", "sunday", "holiday",
            "horario de atencion", "horarios", "abierto",
            "cerrado", "sabado", "domingo", "festivo",
        ),
    ),

    "payments": (
        2,
        (
            "pagamento", "pix", "parcelamento",
            "parcela", "credito", "debito", "boleto",
            "payment", "installment", "credit card",
            "debit card", "payment method",
            "pago", "pagos", "cuotas", "tarjeta",
            "credito", "debito", "metodos de pago",
        ),
    ),

    "returns": (
        3,
        (
            "troca", "devolucao", "devolver",
            "arrependimento", "reembolso", "cancelar compra",
            "return", "refund", "withdrawal",
            "exchange", "bought online", "online purchase",
            "devolucion", "devolver", "reembolso",
            "arrepentimiento", "cambio", "compra online",
            "compra en linea",
        ),
    ),

    "delivery": (
        4,
        (
            "entrega", "frete", "transportadora",
            "sedex", "pac", "rastreio", "rastrear",
            "delivery", "shipping", "shipment",
            "tracking", "carrier",
            "entrega", "envio", "envios",
            "transporte", "seguimiento",
            "rastreo", "numero de seguimiento",
        ),
    ),

    "promotions": (
        5,
        (
            "promocao", "promocoes", "desconto",
            "liquidacao", "oferta", "black friday",
            "promotion", "promotional", "discount",
            "clearance", "special offer",
            "promocion", "promociones", "descuento",
            "descuentos", "oferta", "rebaja",
        ),
    ),

    "support": (
        5,
        (
            "atendimento", "whatsapp", "reclamacao",
            "falar com pessoa", "customer service",
            "complaint", "human support",
            "atencion al cliente", "reclamacion",
            "queja", "hablar con una persona",
        ),
    ),

    "warranty": (
        6,
        (
            "garantia", "fabricante", "assistencia",
            "defeito de fabricacao",
            "warranty", "manufacturer",
            "manufacturing defect",
            "garantia", "fabricante", "defecto",
            "servicio tecnico",
        ),
    ),

    "privacy": (
        6,
        (
            "privacidade", "lgpd", "dados pessoais",
            "excluir dados", "consentimento",
            "privacy", "personal data",
            "data deletion", "consent",
            "privacidad", "datos personales",
            "eliminar datos", "consentimiento",
            "proteccion de datos",
        ),
    ),
}


def normalize(value: str) -> str:
    """Lowercase text and remove accents for multilingual matching."""
    value = unicodedata.normalize("NFKD", str(value).lower())

    return "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )


def retrieve_policy(topic: str) -> dict:
    """Retrieve relevant PDF pages for PT, EN, and ES questions."""

    if not POLICY_PDF.exists():
        return {"error": "Policy PDF unavailable"}

    query = normalize(topic)
    terms = set(re.findall(r"[a-z]{3,}", query))

    matches = []

    for key, (page, keywords) in TOPICS.items():
        score = sum(
            3 for keyword in keywords
            if normalize(keyword) in query
        )

        score += sum(
            1 for token in terms
            if token in key
        )

        if score > 0:
            matches.append((score, key, page))

    matches.sort(reverse=True)

    with pymupdf.open(POLICY_PDF) as doc:

        if not matches:
            scored = []

            for number, page in enumerate(doc):
                text = normalize(page.get_text())

                score = sum(
                    text.count(token)
                    for token in terms
                    if len(token) >= 4
                )

                scored.append((score, number))

            scored.sort(reverse=True)

            pages = [
                number
                for score, number in scored[:2]
                if score > 0
            ]

        else:
            pages = list(
                dict.fromkeys(
                    page
                    for _, _, page in matches[:3]
                )
            )

            # Shipping rules span PDF pages 4 and 5.
            delivery_terms = (
                "frete", "entrega", "rastre", "transport",
                "shipping", "delivery", "tracking",
                "envio", "seguimiento", "rastreo",
            )

            if 4 in pages and any(
                term in query for term in delivery_terms
            ):
                pages.append(3)

            # Privacy rules continue onto PDF page 8.
            privacy_terms = (
                "privacidade", "privacy", "privacidad",
                "datos personales", "personal data",
                "lgpd",
            )

            if 6 in pages and any(
                term in query for term in privacy_terms
            ):
                pages.append(7)

        pages = list(dict.fromkeys(pages))

        excerpts = [
            {
                "pdf_page": page + 1,
                "text": doc[page].get_text()[:6500],
            }
            for page in pages[:4]
        ]

    if not excerpts:
        return {
            "message": (
                "No matching passage; ask for clarification "
                "or refer the customer to the store."
            )
        }

    return {
        "source": (
            "Emporio da Musica Policy Manual "
            "v2.1 (June 2025)"
        ),
        "excerpts": excerpts,
    }
