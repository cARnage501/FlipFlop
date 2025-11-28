from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from flipflop_engine.core import FlipFlopError, run_flipflop


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


app = FastAPI(title="FlipFlop Engine API")


@app.post("/flipflop", response_model=FlipFlopResponse)
def flipflop(payload: FlipFlopRequest) -> FlipFlopResponse:
    try:
        paragraph, truncated, image_prompt, image_url = run_flipflop(
            payload.noun1,
            payload.noun2,
            enforce_length=payload.enforce_length,
            request_image=payload.request_image,
            image_style_tail=payload.image_style_tail,
        )
    except FlipFlopError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return FlipFlopResponse(
        paragraph=paragraph,
        truncated=truncated,
        image_prompt=image_prompt,
        image_url=image_url,
    )


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
