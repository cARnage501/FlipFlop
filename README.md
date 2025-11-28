# FlipFlop Engine API

Tiny FastAPI wrapper around the FlipFlop spec. It locks the full specification into the system message, takes two nouns, and returns a 450–500 character hybrid paragraph (optionally piped to a text-to-image service).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
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

If `enforce_length` is true, responses longer than 500 characters are truncated server side; responses shorter than 450 characters trigger a 502. The spec inside the system prompt already states the same limits.

## Container

Build and run:

```bash
docker build -t flipflop .
docker run -p 8000:8000 --env OPENAI_API_KEY=... flipflop
```

## Notes

- The system prompt in `main.py` is the unedited FlipFlop spec and is injected on every call.
- The optional image hop is backend-agnostic; plug in any HTTP T2I endpoint via `IMAGE_API_URL`.
