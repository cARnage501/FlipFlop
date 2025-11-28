from __future__ import annotations

import os
from typing import Dict, Any, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from openai import OpenAI, AzureOpenAI
except ImportError:
    OpenAI = None
    AzureOpenAI = None


FLIPFLOP_SYSTEM_PROMPT = """# FLIPFLOP_ENGINE SPECIFICATION

from typing import Dict, Any

def infer_traits(noun: str) -> Dict[str, Any]:
    \"\"\"
    Internal-only.

    Input:
        noun: a single noun or noun phrase in natural language.

    Output (internal structure, not visible text):
        traits: a representation capturing:
            - forms / shapes
            - materials
            - surface qualities
            - colors / patterns
            - structural components
            - functional behavior / typical uses
    \"\"\"
    raise NotImplementedError

def merge_traits(traits1: Dict[str, Any], traits2: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"
    Internal-only.

    Input:
        traits1: inferred from noun1
        traits2: inferred from noun2

    Output:
        traits3: a single fused trait structure that integrates contributions
                 from BOTH traits1 and traits2 across all dimensions.
    \"\"\"
    raise NotImplementedError

def describe_from_traits(traits3: Dict[str, Any]) -> str:
    \"\"\"
    Visible output.

    Input:
        traits3: fused trait structure for noun3

    Output:
        paragraph: ONE paragraph (3–5 sentences) of plain prose describing noun3.

    Content constraints:
        - Must describe ONE integrated form whose properties clearly reflect BOTH input nouns.
        - Must mention form, materials, surfaces, structural features, and behavior/operation.
        - Must NOT mention "noun1", "noun2", "noun3", "traits", "prompt", "user",
          or any implementation details.
        - Must NOT include lists, headings, labels, or code.

    HARD CHARACTER LIMIT:
        - The returned paragraph MUST be between 450 and 500 characters inclusive.
        - NEVER exceed 500 characters.
        - Avoid outputs shorter than 450 characters unless absolutely unavoidable.
    \"\"\"
    raise NotImplementedError

def flipflop(noun1: str, noun2: str) -> str:
    \"\"\"
    Top-level pipeline:

        t1 = infer_traits(noun1)
        t2 = infer_traits(noun2)
        t3 = merge_traits(t1, t2)
        paragraph = describe_from_traits(t3)
        return paragraph
    \"\"\"
    t1 = infer_traits(noun1)
    t2 = infer_traits(noun2)
    t3 = merge_traits(t1, t2)
    return describe_from_traits(t3)


# INTERACTION PROTOCOL (FOR THE MODEL):

# - Valid input format:
#       A: <noun1>
#       B: <noun2>
#
# - On valid input:
#       - Extract noun1, noun2
#       - Conceptually run: flipflop(noun1, noun2)
#       - Return ONLY the paragraph from describe_from_traits(traits3)
#
# - No external reference tables, no prior examples, no hidden domains.
#   All inferences MUST be derived from noun1 and noun2 alone.
#
# - On any input that is NOT in the "A: ... / B: ..." format:
#       Respond with exactly:
#           READY FOR NOUNS
#   and nothing else."""


class FlipFlopRequest(BaseModel):
    noun1: str = Field(..., min_length=1, max_length=500)
    noun2: str = Field(..., min_length=1, max_length=500)
    enforce_length: bool = True
    request_image: bool = False
    image_style_tail: Optional[str] = Field(None, max_length=200)


class FlipFlopResponse(BaseModel):
    paragraph: str
    truncated: bool = False
    image_prompt: Optional[str] = None
    image_url: Optional[str] = None


def _build_llm_client():
    api_key = (
        os.getenv("AZURE_OPENAI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_APIKEY")
    )
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY or AZURE_OPENAI_API_KEY.")

    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_version = os.getenv("AZURE_OPENAI_API_VERSION")
    api_base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")

    if azure_endpoint:
        if AzureOpenAI is None:
            raise RuntimeError("openai package not installed.")
        return AzureOpenAI(
            api_version=azure_version or "2024-05-01-preview",
            azure_endpoint=azure_endpoint,
            api_key=api_key,
        )

    if OpenAI is None:
        raise RuntimeError("openai package not installed.")

    return OpenAI(api_key=api_key, base_url=api_base)  # base_url may be None


def _call_flipflop_llm(noun1: str, noun2: str) -> str:
    client = _build_llm_client()
    model = os.getenv("OPENAI_MODEL") or os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-4o-mini"
    messages = [
        {"role": "system", "content": FLIPFLOP_SYSTEM_PROMPT},
        {"role": "user", "content": f"A: {noun1}\nB: {noun2}"},
    ]
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
    except Exception as exc:  # pragma: no cover - passthrough for runtime errors
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}") from exc

    if not completion.choices:
        raise HTTPException(status_code=502, detail="LLM returned no choices.")

    content = completion.choices[0].message.content or ""
    paragraph = content.strip()
    if not paragraph:
        raise HTTPException(status_code=502, detail="LLM returned empty content.")
    return paragraph


def _enforce_length(paragraph: str, enforce: bool) -> tuple[str, bool]:
    if not enforce:
        return paragraph, False

    truncated = False
    if len(paragraph) > 500:
        paragraph = paragraph[:500]
        truncated = True
    if len(paragraph) < 450:
        raise HTTPException(
            status_code=502,
            detail="Model returned text shorter than 450 characters.",
        )
    return paragraph, truncated


def _maybe_build_image_prompt(paragraph: str, tail: Optional[str]) -> str:
    if tail:
        return f"{paragraph} {tail.strip()}"
    return paragraph


def _maybe_generate_image(prompt: str) -> Optional[str]:
    image_api_url = os.getenv("IMAGE_API_URL")
    if not image_api_url:
        return None

    try:
        response = httpx.post(image_api_url, json={"prompt": prompt}, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("url") or data.get("image_url")
    except Exception as exc:  # pragma: no cover - passthrough for runtime errors
        raise HTTPException(status_code=502, detail=f"Image backend error: {exc}") from exc


app = FastAPI(title="FlipFlop Engine")


@app.post("/flipflop", response_model=FlipFlopResponse)
def flipflop(payload: FlipFlopRequest) -> FlipFlopResponse:
    paragraph = _call_flipflop_llm(payload.noun1.strip(), payload.noun2.strip())
    paragraph, truncated = _enforce_length(paragraph, payload.enforce_length)

    image_prompt = None
    image_url = None
    if payload.request_image:
        image_prompt = _maybe_build_image_prompt(paragraph, payload.image_style_tail)
        image_url = _maybe_generate_image(image_prompt)

    return FlipFlopResponse(
        paragraph=paragraph,
        truncated=truncated,
        image_prompt=image_prompt,
        image_url=image_url,
    )


@app.get("/healthz")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}
