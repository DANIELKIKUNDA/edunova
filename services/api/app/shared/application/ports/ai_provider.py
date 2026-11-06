from typing import Protocol


class AiProvider(Protocol):
    async def explain(self, *, prompt: str, context: str) -> str: ...

    async def summarize(self, *, content: str, mode: str) -> str: ...
