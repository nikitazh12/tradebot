from __future__ import annotations

from typing import Protocol

from tradebot.ai.analyzer import AIAnalysis
from tradebot.signals.models import SignalCandidate


class AIAnalyzerProtocol(Protocol):
    async def analyze(self, candidate: SignalCandidate) -> AIAnalysis: ...
