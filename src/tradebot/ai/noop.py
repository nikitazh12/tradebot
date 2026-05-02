from tradebot.ai.analyzer import AIAnalysis
from tradebot.signals.models import SignalCandidate


class NoopAIAnalyzer:
    """Заглушка — всегда апрувит без вызова API."""

    async def analyze(self, candidate: SignalCandidate) -> AIAnalysis:
        return AIAnalysis.approved(comment="noop", confidence=1.0)
