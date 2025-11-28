# FlipFlop Engine

FlipFlop is the engine: given two nouns, it infers their traits, fuses them, and emits one 450–500 character paragraph describing a single integrated form. This repo centers on the engine spec and implementation; the HTTP app is just one way to call it.

## What it does
- Input: `noun1`, `noun2`
- Process: infer traits for each noun, merge them into one coherent object
- Output: exactly one paragraph (3–5 sentences), 450–500 characters, reflecting both nouns across form, materials, surfaces, structure, and behavior
- Optional: send the paragraph to a text-to-image backend if `IMAGE_API_URL` is configured

## Repo map
- `flipflop_engine/` – the FlipFlop spec, system prompt, LLM call, length enforcement, optional image hop.
- `fastapi_app/` – a FastAPI interface to the engine (`/flipflop`, `/healthz`). Keep or replace with any interface you like.

## Use the engine directly (Python)

```python
from flipflop_engine.core import run_flipflop

paragraph, truncated, image_prompt, image_url = run_flipflop(
    "flip-flop",
    "ChatGPT",
    enforce_length=True,
    request_image=False,
)
print(paragraph)
```

## HTTP interface (optional FastAPI)

If you want an HTTP endpoint, the FastAPI app in `fastapi_app/main.py` exposes the engine. Example dev run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn fastapi_app.main:app --reload
```

POST `http://localhost:8000/flipflop`

```json
{
  "noun1": "flip-flop",
  "noun2": "ChatGPT",
  "request_image": false,
  "enforce_length": true
}
```

Response:

```json
{
  "paragraph": "<450–500 chars of prose>",
  "truncated": false,
  "image_prompt": null,
  "image_url": null
}
```

Health check: `GET /healthz`.

## Environment

- `OPENAI_API_KEY` (or `AZURE_OPENAI_API_KEY`) – required.
- `OPENAI_MODEL` (default `gpt-4o-mini`) or `AZURE_OPENAI_DEPLOYMENT`.
- `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_VERSION` for Azure usage.
- `OPENAI_BASE_URL` (or `OPENAI_API_BASE`) to point at non-default endpoints.
- `IMAGE_API_URL` (optional) – if set and `request_image` is true, the paragraph (plus optional `image_style_tail`) is sent to this URL via POST `{ "prompt": "<text>" }`.

## Length contract

If `enforce_length` is true, responses longer than 500 characters are truncated server side; responses shorter than 450 characters raise an error. The spec inside `flipflop_engine/core.py` also states the limits.

## Container

Build and run:

```bash
docker build -t flipflop .
docker run -p 8000:8000 --env OPENAI_API_KEY=... flipflop
```

## Notes

- The system prompt in `flipflop_engine/core.py` is the unedited FlipFlop spec and is injected on every call.
- The optional image hop is backend-agnostic; plug in any HTTP T2I endpoint via `IMAGE_API_URL`.
