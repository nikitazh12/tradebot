"""AIAnalyzer — NVIDIA-совместимый (OpenAI-интерфейс) анализ сигналов."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from tradebot.signals.models import SignalCandidate

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a trading signal validator. "
    "Given a trading signal candidate, reply with JSON: "
    "{\"approve\": true/false, \"confidence\": 0.0-1.0, \"comment\": \"...\"}. "
    "Approve only if the setup is technically sound. "
    "NEVER override risk/reward — that is handled separately."
)


@dataclass(frozen=True)
class AIAnalysis:
    approve: bool
    confidence: float
    comment: str

    @classmethod
    def approved(cls, comment: str = "", confidence: float = 1.0) -> AIAnalysis:
        return cls(approve=True, confidence=confidence, comment=comment)

    @classmethod
    def rejected(cls, comment: str = "", confidence: float = 1.0) -> AIAnalysis:
        return cls(approve=False, confidence=confidence, comment=comment)


class AIAnalyzer:
    def __init__(self, api_key: str, base_url: str, model: str = "meta/llama-3.1-8b-instruct") -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def analyze(self, candidate: SignalCandidate) -> AIAnalysis:
        prompt = (
            f"Ticker: {candidate.ticker}\n"
            f"Direction: {candidate.direction}\n"
            f"Setup: {candidate.setup}\n"
            f"Entry: {candidate.entry}, Stop: {candidate.stop}, Take: {candidate.take}\n"
            f"Horizon: {candidate.horizon}\n"
            f"Reasoning: {candidate.reasoning}"
        )
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=256,
            )
            import json
            content = resp.choices[0].message.content or ""
            # Вырезаем JSON из ответа (может быть обёрнут в markdown)
            start = content.find("{")
            end = content.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError(f"No JSON in response: {content!r}")
            data = json.loads(content[start:end])
            return AIAnalysis(
                approve=bool(data.get("approve", False)),
                confidence=float(data.get("confidence", 0.5)),
                comment=str(data.get("comment", "")),
            )
        except Exception as e:
            logger.warning("AIAnalyzer failed, falling back to approve: %s", e)
            return AIAnalysis.approved(comment=f"fallback: {e}", confidence=0.0)
