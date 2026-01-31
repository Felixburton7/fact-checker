# checker_of_facts

Fact checking with an OpenAI Agents SDK debate. The CLI runs a moderator‑led, 5‑juror debate and produces a structured verdict.

## What this is

Use `checker_of_facts` when you want a **structured** debate and verdict. The system:

- decomposes text into atomic claims
- runs a deterministic juror debate
- issues a moderator verdict based on the debate

## How it works (pipeline)

1) **Claim agent** splits the input into atomic claims.
2) **Jurors** debate in a fixed, deterministic order (each turn considers prior turns).
3) **Moderator** delivers the final verdict.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env
# edit .env with your keys

factcheck "The Moon is made of cheese."
```

## Configuration

Required:
- `OPENAI_API_KEY`

Optional:
- `OPENAI_MODEL` (default `gpt-4.1-mini`)
- `WORKSPACE_DIR` (default `.workspace`)

## Tests

```bash
.venv/bin/python -m pytest -q
```

## Notes and limitations

- Verdicts are based on internal model knowledge and can be incorrect or outdated.
- “Current” claims can change rapidly; treat results as best‑effort.
