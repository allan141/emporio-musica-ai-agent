"""Small deterministic document retrieval over the supplied store policy PDF."""
from pathlib import Path
import fitz
import re
import unicodedata

POLICY_PDF = Path(__file__).resolve().parents[2] / "data" / "politicas_da_loja.pdf"

TOPICS = {
    "store": (1, ("loja", "endereco", "contato", "telefone", "cnpj", "localizacao")),
    "hours": (1, ("horario", "aberto", "fecha", "funcionamento", "domingo", "sabado", "feriado")),
    "payments": (2, ("pagamento", "pix", "parcelamento", "parcela", "credito", "debito", "boleto")),
    "returns": (3, ("troca", "devolucao", "devolver", "arrependimento", "defeito", "reembolso", "cancelar compra")),
    "delivery": (4, ("entrega", "frete", "transportadora", "sedex", "pac", "rastreio", "rastrear")),
    "promotions": (5, ("promocao", "desconto", "liquidacao", "oferta", "black friday")),
    "support": (5, ("atendimento", "whatsapp", "reclamacao", "falar com pessoa")),
    "warranty": (6, ("garantia", "fabricante", "defeito", "assistencia")),
    "privacy": (6, ("privacidade", "lgpd", "dados pessoais", "excluir dados", "consentimento")),
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value).lower())
    return "".join(char for char in value if not unicodedata.combining(char))


def retrieve_policy(topic: str) -> dict:
    """Return relevant source-page excerpts with PDF page numbers, not invented policies."""
    if not POLICY_PDF.exists():
        return {"error": "Policy PDF unavailable"}
    query = normalize(topic)
    terms = set(re.findall(r"[a-z]{3,}", query))
    matches = []
    for key, (page, keywords) in TOPICS.items():
        score = sum(3 if keyword in query else 0 for keyword in keywords)
        score += sum(1 for token in terms if token in key)
        if score > 0:
            matches.append((score, key, page))
    matches.sort(reverse=True)
    # Fall back to relevant keyword similarity across pages, rather than invent an answer.
    with fitz.open(POLICY_PDF) as doc:
        if not matches:
            scored = []
            for number, page in enumerate(doc):
                text = normalize(page.get_text())
                score = sum(text.count(token) for token in terms if len(token) >= 4)
                scored.append((score, number))
            scored.sort(reverse=True)
            pages = [n for score, n in scored[:2] if score > 0]
        else:
            pages = list(dict.fromkeys(page for _, _, page in matches[:3]))
            # Delivery spans two pages; customer service and privacy span two as well.
            if 4 in pages and any(s in query for s in ("frete", "entrega", "rastre", "transport")):
                pages.append(3)
            if 6 in pages and "privacidade" in query:
                pages.append(7)
        excerpts = [{"pdf_page": page + 1, "text": doc[page].get_text()[:6500]} for page in pages[:4]]
    if not excerpts:
        return {"message": "No matching passage; ask for clarification or refer to the store."}
    return {"source": "Emporio da Musica Policy Manual v2.1 (June 2025)", "excerpts": excerpts}
