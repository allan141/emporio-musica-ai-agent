# Example conversations

The required 3–5 genuine conversations must be captured **after** running the agent
with a valid API key. From the project root, run:

```bash
python -m scripts.generate_examples
```

This generates four real transcripts (`catalog.md`, `policies.md`, `promotions.md`,
`privacy.md`). The example generator is intentionally not run without the owner's
API key; do not represent synthetic outputs as observed conversations.

Review each transcript for factual accuracy and privacy before publishing it.
