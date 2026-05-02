from tradebot.core.enums import Direction, NoSignalReason
from tradebot.signals.models import NoSignalLog, SignalCandidate


class SignalDeduplicator:
    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()

    def check(self, candidate: SignalCandidate) -> SignalCandidate | NoSignalLog:
        key = (candidate.ticker, candidate.direction)
        if key in self._seen:
            return NoSignalLog(
                ticker=candidate.ticker, figi=candidate.figi, tf=candidate.tf,
                reason=NoSignalReason.DUPLICATE_SIGNAL,
                details=f"already sent {candidate.direction} for {candidate.ticker}",
            )
        self._seen.add(key)
        return candidate

    def mark_sent(self, ticker: str, direction: Direction) -> None:
        self._seen.add((ticker, direction))
