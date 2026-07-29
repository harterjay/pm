import anthropic
from fastapi import HTTPException

MODEL = "claude-sonnet-5"


def ask(prompt: str) -> str:
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
    except (anthropic.AnthropicError, TypeError) as exc:
        # A missing API key/credentials surfaces as a raw TypeError from the
        # SDK's header validation (not an AnthropicError subclass), so it's
        # caught explicitly here alongside the normal SDK error hierarchy.
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}") from exc

    return "".join(block.text for block in response.content if block.type == "text")
