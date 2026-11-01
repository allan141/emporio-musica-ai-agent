# Empório da Música — AI Customer Service Agent

Python prototype for the Artefact AI Engineer technical challenge.

> **Status:** runnable starter implementation. Actual Gemini API calls and example transcripts
> must be executed with the developer's own API key before the final submission.

## Problem and scope

The assistant answers questions about musical instruments, catalog availability,
prices, active promotions in the provided snapshot, order tracking (after an
order ID + email match), and store policies extracted from the supplied PDF.
It politely refuses unrelated requests and does not perform purchases or refunds.

The fictional store source data includes six CSV files (9 categories, 50 customers,
65 products, 20 orders, 22 order items, 25 promotions) and Policy Manual v2.1,
June 2025. The CSV records are historical snapshots rather than live integrations.

## Tech stack and decisions

- **Python 3.11–3.13** as required by the challenge.
- **Google gemini-3.5-flash-lite** through `google-genai` for a free-tier option
  (subject to availability, quotas and policy changes).
- **Single LLM supervisor + Python function calling**, instead of importing the
  large LangGraph supervisor from the Triggo.ai reimbursement project. That project
  inspired separation of state, decision logic and deterministic business rules.
  The smaller architecture is easier to inspect, run, explain and test.
- **SQLite** to query the CSVs with parameterized joins; reproducible local
  import, no external database or hosting cost.
- **PDF retrieval** with PyMuPDF and a simple intent/page selection strategy.
  The manual is short (8 pages), so embeddings and a vector store are unnecessary
  initially. Policies are cited by PDF page in tool outputs.
- **Streamlit** session-local chat history, preserving follow-up context inside
  a session without adding an additional persistence service.
- **Read-only tools and deterministic Decimal calculations** for prices, PIX,
  promotions and credit installment constraints.

## Project layout

```text
app/
  agent.py            Gemini chat and tool orchestration
  main.py             Streamlit UI
  prompts.py          Persona and mandatory tool rules
  services/database.py  CSV -> SQLite import
  services/policies.py  PDF section retrieval
  tools/store.py      Products, orders, promotions, payment tools
data/raw/             Challenge CSV source files
data/politicas_da_loja.pdf
scripts/generate_examples.py
examples/             Transcripts after live execution
tests/                Offline deterministic unit tests
```

## Setup on Windows (PowerShell)

1. Install Python 3.12 and open the repository root in VS Code.
2. Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

3. Copy `.env.example` to `.env`, edit `GEMINI_API_KEY`, and optionally set the
   model. Create a key at https://aistudio.google.com/apikey. Never commit `.env`.

```powershell
Copy-Item .env.example .env
```

4. Initialize the SQLite database (automatically runs on first query too):

```powershell
python -c "from app.services.database import initialize_database; print(initialize_database())"
```

5. Run offline tests:

```powershell
python -m pytest -q
```

6. Start the interface:

```powershell
python -m streamlit run app/main.py
```

7. Ask:
- "Quais violões disponíveis custam até R$ 1.000?"
- "Quanto custa o Yamaha C40?"
- "Comprei online e quero devolver. Qual é a política?"
- "Quais são as promoções do catálogo?"
- "Qual o status do pedido 8?" (ID + registered email required)

## Producing required conversation transcripts

With a working API key and enough free-tier quota, execute:

```powershell
python -m scripts.generate_examples
```

Review all four generated files in `examples/` for accuracy and privacy before
submission. The starter does not fabricate a successful model run.

## Security and privacy

- Order lookups require both an exact order ID and the associated email address.
  No password, customer directory, raw PII list or write operation is exposed.
- No secrets are checked in; `.env`, `.venv` and the generated SQLite DB are ignored.
- The provided source data are fictional challenge data. The free-tier model provider
  may use submitted content to improve products; use only approved demo data.
- Tool outputs from the PDF are evidence, never system instructions.
- These are prototype-level checks, not real production authentication. Production
  would require verified login/OTP, authorization, audit logs and rate limits.

## Known limitations / next steps

1. Historical CSV snapshot: no real-time stock, shipment updates, campaign dates,
   refunds or cancellations. The `is_active` promotion flag does not prove a
   campaign remains active on the day of interaction.
2. PDF retrieval is page/keyword based and can miss complex paraphrases. A
   semantic index with evaluation would be a reasonable future improvement.
3. Chat history lasts only in the running Streamlit session and is not durable.
4. The credit installment rule for 1–3 installments is interpreted as a minimum
   R$50 installment based on the manual's exception; ambiguous cases should be
   escalated to store staff. The source manual also mentions a generic R$100
   threshold for up to 12 installments: the specific bracketed rules take priority.
5. Estimated delivery dates in the source data may be in the past; do not infer
   actual fulfillment from those dates alone.
6. Gemini API availability and quotas depend on account/region. The project cannot
   guarantee no costs if a paid billing project is selected; use free tier only.
7. Source policy document is an internal fictional manual provided by the challenge.
   In production, only appropriate customer-facing excerpts should be exposed.

## Testing strategy

`pytest` checks table counts, catalog search, promo flags, email-gated order
lookup, payment math, non-stacking PIX discounts, installment guardrails and
PDF retrieval. Integration tests with the Gemini API must be performed separately.

## AI assistant disclosure

This project was developed with assistance from **OpenAI ChatGPT** for architecture
planning, code scaffolding, review and documentation. The developer must inspect,
run, adapt and understand every change before claiming authorship. Some patterns
were inspired by a previous educational project from the **Triggo.ai AI Engineering
bootcamp**, especially separation of orchestration, retrieval, business rules
and test cases. No credential or private code from that project is required.

## Delivery checklist

- [ ] Configure and test a working API key.
- [ ] Confirm policy answers, catalog answers and adversarial behavior interactively.
- [ ] Generate and review 3–5 **real** example transcripts.
- [ ] Commit progress in multiple meaningful Git commits, then push to a public repo.
- [ ] Add your actual GitHub URL to the submission PDF/email as instructed by recruiting.
- [ ] Confirm whether email or Google Form (or both) is required; their instructions differ.
- [ ] Do not modify the repository after the final submission timestamp.
