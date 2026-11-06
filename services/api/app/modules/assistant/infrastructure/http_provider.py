from __future__ import annotations

import httpx

from app.modules.assistant.domain.model import ProviderResult


class OpenAICompatibleProvider:
    """Generic adapter for providers exposing the OpenAI chat-completions contract.

    Endpoint/model/pricing are configuration, never hard-coded business rules.
    """
    def __init__(self, *, name: str, model: str, base_url: str, api_key: str, timeout_seconds: float = 45.0) -> None:
        self.name=name; self.model=model; self.base_url=base_url.rstrip('/'); self.api_key=api_key; self.timeout_seconds=timeout_seconds
    def generate(self, *, system_prompt: str, user_prompt: str, max_output_tokens: int) -> ProviderResult:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            r = client.post(f"{self.base_url}/chat/completions",headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"},json={"model":self.model,"messages":[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],"max_tokens":max_output_tokens,"temperature":0.2})
            r.raise_for_status(); data=r.json()
        usage=data.get("usage") or {}; choice=(data.get("choices") or [{}])[0]
        content=((choice.get("message") or {}).get("content") or "").strip()
        return ProviderResult(text=content,input_tokens=int(usage.get("prompt_tokens") or 0),output_tokens=int(usage.get("completion_tokens") or 0),provider_request_id=r.headers.get("x-request-id"))
