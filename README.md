
# Empório da Música — AI Customer Service Agent

Python-based customer service agent developed for the **Artefact AI Engineer technical challenge**.

> **Status:** Functional prototype tested locally with the Google Gemini API.
>
> The application integrates read-only customer service tools, deterministic business rules, multilingual responses, **20 passing automated tests**, and **four recorded conversation examples**.
>
> Product availability, orders, and promotions come from the challenge's **historical dataset**, not live store systems.

## Problem and Scope

Empório da Música is a fictional musical instrument store in Campo Grande, MS, Brazil. The goal is to reduce repetitive requests handled by its customer service team while keeping responses accurate, transparent, and consistent with store policies.

The assistant, **Melodia**, supports:

- Product searches by name, category, budget, and recorded stock availability.
- Product prices and promotions marked active in the provided dataset.
- Order status inquiries after matching an order ID with its associated customer email.
- Store policies, including opening hours, payments, shipping, exchanges, returns, and warranty.
- Follow-up questions within the same chat session.
- Replies in the customer's language, with Brazilian Portuguese as the fallback.

It politely redirects unrelated requests and **does not** place orders, issue refunds, cancel purchases, or update store records.

The dataset contains six CSV files: **9 categories, 50 customers, 65 products, 20 orders, 22 order items, and 25 promotions**.

The accompanying document is the **Store Policy Manual, version 2.1 (June 2025)**.

All operational records are treated as a historical snapshot.

## Technical Approach and Decisions

| Component | Choice | Rationale |
| --- | --- | --- |
| Primary language | Python 3.12 (recommended) | Meets the challenge's Python requirement and supports the project dependencies. |
| LLM | Google Gemini through `google-genai` | Supports tool calling and a free-tier option, subject to account eligibility and quotas. |
| Orchestration | Single LLM agent with Python function calling | Keeps decisions and tool execution easy to inspect without unnecessary multi-agent complexity. |
| Structured data | SQLite | Imports the supplied CSV files into a lightweight, reproducible local database. |
| Policy retrieval | PyMuPDF and keyword/topic-based page selection | The supplied manual is short; a vector database is not necessary for this prototype. |
| User interface | Streamlit | Provides a simple local chat for demonstrations and manual testing. |
| Conversation context | Session-scoped Gemini chat and Streamlit state | Supports follow-up questions without introducing a separate persistence service. |
| Business calculations | Python `Decimal` | Makes discount and installment calculations deterministic rather than relying on the LLM to do arithmetic. |
| Validation | Pytest and recorded conversations | Separates offline business-rule tests from manual Gemini integration testing. |

### Request Flow

```text
Customer message
       |
       v
Streamlit chat interface
       |
       v
Melodia (Gemini + system instructions)
       |
       +--> Product / promotion tools ---> SQLite snapshot
       |
       +--> Order-status tool -----------> SQLite snapshot + email match
       |
       +--> Policy retrieval tool -------> Store policy PDF
       |
       +--> Payment calculation tool ----> Deterministic Python rules
       |
       v
Customer-facing response
```

The Gemini model chooses from explicitly provided Python functions.

The tools are responsible for data retrieval, basic lookup checks, and monetary calculations; the model is responsible for interpreting requests and composing the response.

Tool results and retrieved documents are treated as **data, not instructions**.

### Prompt Strategy

The system prompt defines Melodia's friendly, professional persona and the store's product scope.

It also requires tool use for factual claims, makes uncertainty explicit, discourages unsupported promises, and keeps customer-facing responses in the customer's language.

Additional rules distinguish **online withdrawal rights** from separate **exchange policies**, prohibit stacking the **5% PIX discount** with promotional prices, and prohibit disclosure of order details when the supplied email does not match the order record.

### Retrieval Strategy

The application extracts text from the provided PDF and selects relevant pages using topics, keywords, and fallback text matching.

The tool returns excerpts with their **PDF page numbers**.

This is a deliberately simple, inspectable retrieval approach—not an embeddings-based or vector-database RAG pipeline.

The assistant should use the retrieved evidence without inventing additional policies.

## Project Structure

```text
app/
  agent.py                 Gemini chat and tool orchestration
  main.py                  Streamlit interface
  prompts.py               Persona, language, and tool-use rules
  services/
    database.py            CSV-to-SQLite initialization and connections
    policies.py            PDF text retrieval
  tools/
    store.py               Products, promotions, orders, and payment tools

data/
  raw/                     Six supplied CSV files
  politicas_da_loja.pdf    Supplied store policy manual

examples/                  Recorded customer-agent conversations
scripts/
  generate_examples.py     Conversation capture script
tests/                     Offline automated tests

.env.example               Environment variable template
.gitignore                 Ignored secrets and generated files
requirements.txt           Python dependencies
pytest.ini                 Test configuration
README.md                  Project documentation
```

## Setup and Execution — Windows PowerShell

### 1. Requirements

- Python 3.12 (recommended).
- Git and VS Code (optional but convenient).
- A Gemini API key with access to the configured model.

### 2. Create a Virtual Environment

Open a terminal at the repository root and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use the following command in the current terminal session and activate the environment again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Configure the Gemini API Key

Create an API key using [Google AI Studio](https://aistudio.google.com/apikey).

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Edit `.env` locally:

```dotenv
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

**Never commit your `.env` file or share the actual API key.**

The free tier is subject to availability, rate limits, and the provider's terms.

Do not enable paid billing unless you intend to use a paid account.

### 4. Initialize the Local Database

```powershell
python -c "from app.services.database import initialize_database; print(initialize_database())"
```

This creates `data/store.db` from the supplied CSV files if the database does not already exist.

The generated SQLite database is ignored by Git.

### 5. Run the Automated Tests

```powershell
python -m pytest -q
```

### 6. Start the Chat Interface

```powershell
python -m streamlit run app/main.py
```

Streamlit usually opens at `http://localhost:8501`.

Example questions:

- `Quais violões disponíveis custam até R$ 1.000?`
- `Quanto custa o Yamaha C40?`
- `Comprei online e quero devolver. Qual é a política?`
- `Quais promoções estão marcadas como ativas nos dados?`
- `Qual o status do pedido 8?` (requires matching order email)
- `Hello! Do you have acoustic guitars under BRL 1,000?`


## Recorded Conversation Examples

The `examples/` directory contains four customer service conversations captured through actual interactions with the Gemini API.

These examples demonstrate how Melodia handles structured data, policy retrieval, conversational context, business rules, and basic customer privacy checks.

| File | Scenario | Demonstrated Capability |
| --- | --- | --- |
| `catalog.md` | Product search and follow-up questions | Catalog retrieval, price filtering, and conversational context |
| `policies.md` | Online purchase withdrawal | Policy retrieval, interpretation, and return shipping rules |
| `promotions.md` | Promotional pricing and PIX payment | Promotion lookup, discount calculations, and non-stacking rules |
| `privacy.md` | Order status with correct and incorrect customer email | Order lookup, email matching, and controlled information disclosure |

The conversations were conducted in English while retrieving information from Portuguese source documents.

Product names, monetary values, and order identifiers were preserved.

### Generating Conversation Examples

With a configured Gemini API key, run:

```powershell
python -m scripts.generate_examples
```

To generate an individual scenario:

```powershell
python -m scripts.generate_examples privacy
```

Available scenarios:

- `catalog`
- `policies`
- `promotions`
- `privacy`

The script captures the actual model responses and saves them as Markdown files.

It also implements retry handling for temporary API rate-limit errors.

The captured responses should be reviewed for accuracy, business-rule compliance, privacy, and language consistency before submission.

## Business Rules and Reliability

The application separates language-model reasoning from deterministic business logic.

### Product Availability

Product prices, stock quantities, and availability information must come from the supplied database.

The assistant must not invent product information or claim that historical inventory represents live stock.

If a product is unavailable, the assistant should consult the catalog before suggesting alternatives.

### Promotions and Payment

The payment tools apply store rules using deterministic Python calculations.

Important conditions include:

- A 5% PIX discount on eligible regular-priced products.
- Promotional discounts cannot be combined with the PIX discount.
- Credit card installments must respect the minimum payment amount for the selected installment range.
- Promotions marked active in the historical dataset are not guaranteed to remain valid today.

The model is instructed to use the payment calculation tool instead of independently inventing financial calculations.

### Online Returns and Exchanges

The assistant retrieves relevant information from the provided policy manual.

The online purchase withdrawal policy allows customers to request a return within seven calendar days after receiving the product, according to Section 4.1 of the manual.

The assistant distinguishes this right from the separate product exchange rules.

Ambiguous or conflicting situations should be referred to the store's customer service team instead of being resolved through unsupported assumptions.

### Order Verification

Order information is retrieved only when the supplied order ID and customer email match the corresponding database record.

If the verification fails, the assistant provides a generic response without exposing order details.

This is a basic prototype-level lookup check, not a substitute for production authentication.

## Testing Strategy

The project includes automated tests using `pytest`, covering the deterministic components of the application.

Run the complete test suite:

```powershell
python -m pytest -q
```


### Multilingual Policy Retrieval Tests

Eight additional automated tests validate policy retrieval
across Portuguese, English, and Spanish.

The tests cover:

- Store opening hours in Portuguese, English, and Spanish.
- Online purchase withdrawal policies in all three languages.
- Promotional discount rules involving PIX in Spanish.
- Source identification in retrieved policy responses.

All tests run locally without requiring Gemini API calls.

**Total automated tests: 20 passed, 0 failed.**


### Automated Test Results

The test suite was executed locally using:

- Python 3.12.10
- Pytest 9.2.0
- Windows environment

**Result: 20 passed, 0 failed.**

The test suite covers:

1. CSV data imports and expected record counts.
2. Product catalog searches and price filtering.
3. Product availability and missing products.
4. Promotion information retrieved from the dataset.
5. Order lookup with an incorrect customer email.
6. Order lookup with matching customer information.
7. PIX discount calculations.
8. Prevention of cumulative promotional and PIX discounts.
9. Credit card installment restrictions.
10. Policy retrieval from the provided PDF.
11. Payment policy retrieval.
12. Handling questions without matching policy information.

### Manual Integration Testing

Additional manual tests were performed through the Streamlit interface and actual Gemini API interactions.

The evaluated scenarios included:

- Product searches and follow-up questions.
- Payment methods and installment rules.
- Online returns and shipping policies.
- Order inquiries with matching and mismatching email addresses.
- Requests for products outside the store's catalog.
- Multilingual customer interactions in Portuguese, English, and Spanish.

These tests demonstrate the behavior of the implemented prototype.

However, they do not represent exhaustive coverage or a production-level security assessment.

## Security and Privacy

The application follows basic security and privacy practices appropriate for an educational prototype.

### API Credentials

API credentials are stored in a local `.env` file.

The `.gitignore` prevents the `.env`, virtual environment, and generated SQLite database from being added to Git.

The public repository includes only `.env.example`, containing placeholder configuration values.

### Customer Information

Order lookups require an order ID and a matching email address.

The assistant must not reveal order details when the supplied email does not match the associated customer record.

The application does not intentionally expose customer directories, passwords, or database write operations through its tools.

### Read-Only Operations

The application uses read-only customer service tools for product information, order inquiries, promotions, and store policies.

It cannot:

- Place orders.
- Cancel purchases.
- Process refunds.
- Modify customer records.
- Update product inventory.

### Prompt Injection and Retrieved Content

Retrieved documents and tool outputs are treated as data rather than instructions.

The system prompt instructs the model not to follow instructions embedded in external content that conflict with the application's rules.

These protections are basic safeguards and have not been independently validated against comprehensive prompt-injection attacks.

### Production Considerations

A production deployment would require additional protections, including:

- Verified customer authentication.
- Role-based authorization where applicable.
- Secure audit logs.
- Request rate limiting.
- Stronger handling of sensitive customer information.
- Monitoring and structured error reporting.
- Appropriate data protection and retention policies.

## Known Limitations

The implementation prioritizes simplicity, reproducibility, and clear technical decisions.

The following limitations remain:

### 1. Historical Data

The supplied CSV files represent a historical snapshot.

Product stock, prices, order statuses, estimated delivery dates, and promotional campaigns are not updated in real time.

The assistant must communicate this limitation when relevant.

### 2. Simplified Document Retrieval

Policy retrieval uses PDF text extraction and keyword/topic-based selection.

This approach is appropriate for the short policy manual but may fail on complex paraphrases or ambiguous questions.

Semantic search, embeddings, and retrieval evaluation could improve document coverage in a larger system.

### 3. Session-Based Conversation Memory

Conversation context is maintained within the running chat session.

The application does not provide durable conversation history across server restarts or independent sessions.

### 4. Limited Customer Authentication

Matching an order ID with a registered email address provides a basic lookup restriction.

It does not establish strong customer identity verification.

A production system would require authentication or an additional verification mechanism.

### 5. Gemini API Quotas

The application depends on the Gemini API.

Free-tier access is subject to model availability, request limits, regional eligibility, and provider policies.

During development, a temporary HTTP 429 rate-limit error was observed.

The conversation generation script includes retry handling for temporary quota limitations.

### 6. Model Response Variability

LLM-generated answers are not fully deterministic.

Although the application uses system instructions, retrieved data, and Python tools, the model may occasionally produce formatting inconsistencies, language changes, or incomplete explanations.

Additional automated integration evaluations and structured response validation would improve reliability.

### 7. Business Rule Ambiguities

Some policy statements may require interpretation.

For example, the manual contains general installment information and more specific installment thresholds.

The implementation prioritizes the more specific bracketed rules and documents its assumptions.

Unclear cases should be escalated to store staff rather than resolved through unsupported claims.

### 8. No Real Transaction Processing

The assistant is an informational prototype.

It does not execute payments, refunds, cancellations, or inventory changes.

## Future Improvements

With additional development time, the following improvements would be considered:

1. Add automated integration tests for Gemini tool calls and multilingual response consistency.
2. Implement structured tracing of tool execution and retrieval decisions.
3. Introduce persistent conversation storage.
4. Add secure customer authentication and authorization.
5. Evaluate semantic retrieval for larger policy collections.
6. Integrate authorized real-time inventory and order management APIs.
7. Add structured output validation and response quality evaluation.
8. Introduce monitoring, error reporting, and automated deployment checks.
9. Improve accessibility and the overall user experience of the chat interface.

These improvements are not required for the current prototype, but they would be relevant to a production-ready application.

## AI-Assisted Development

ChatGPT was used as a supporting tool during development, assisting with the evaluation of technical approaches, selection of Python libraries, implementation suggestions, and identification and resolution of bugs.

It was also used to review technical decisions, improve prompts, analyze business rules, and support project documentation.

The implementation was iteratively tested and refined through automated tests, analysis of the provided datasets, and real interactions with the Gemini API.

## Repository

The project is publicly available at:

https://github.com/allan141/emporio-musica-ai-agent

The repository contains the Python application, source data, automated tests, documentation, and recorded conversation examples.

Development progress is recorded through incremental Git commits.

## Delivery Checklist

- [x] Implement the Python customer service agent.
- [x] Configure and test the Gemini API.
- [x] Integrate catalog, order, promotion, payment, and policy tools.
- [x] Execute the automated test suite successfully (20 passed).
- [x] Validate multilingual customer interactions.
- [x] Generate and review four real conversation examples.
- [x] Maintain incremental development commits.
- [x] Publish the project in a public GitHub repository.
- [ ] Complete the final documentation and code review.
- [ ] Perform the final repository security audit.
- [ ] Confirm the required submission channel with recruiting.
- [ ] Submit the repository before the established deadline.
- [ ] Avoid modifying the repository after the final submission timestamp.

---

**Empório da Música — Sua música começa aqui.**

Developed for the Artefact AI Engineer technical challenge.
