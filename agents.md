# FlipFlop Agents

This repo wraps the FlipFlop spec in a FastAPI service that acts like a tiny agent: it accepts two nouns, fuses their traits in the model’s system prompt, and returns a single 450–500 character paragraph (plus an optional text-to-image hop).

## How to think about it
- Inputs: `noun1`, `noun2`; optional `request_image` and `image_style_tail`.
- Core action: run the fixed FlipFlop system prompt, produce one fused-form paragraph; truncate above 500 chars, error below 450 when `enforce_length` is true.
- Optional image: if `IMAGE_API_URL` is set and `request_image` is true, the paragraph (plus optional style tail) is POSTed as `{ "prompt": "<text>" }`; `image_url` is echoed back.

## Calling from an orchestrator
- HTTP: POST `/flipflop` with the JSON body from `README.md`; parse `paragraph`, `truncated`, `image_prompt`, `image_url`.
- Direct model call: reuse `FLIPFLOP_SYSTEM_PROMPT` (see `main.py`) and send a chat turn with `A: <noun1>\nB: <noun2>`; keep `temperature=0` for determinism.
- Health: GET `/healthz` returns `{ "status": "ok" }`.

## Running the agent locally
- Start with `uvicorn main:app --reload` after creating a venv and installing `requirements.txt`.
- Set `OPENAI_API_KEY` (or Azure equivalents); optionally set `OPENAI_MODEL`, `IMAGE_API_URL`, and `image_style_tail` in requests.

## When to use FlipFlop
- You need a deterministic fusion of two concepts into one coherent object description.
- You need strict length-bounded prose for downstream image generation or UI slots.
- You want a drop-in microservice you can call from larger agent graphs without re-authoring the prompt.
