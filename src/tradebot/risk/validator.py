from decimal import Decimal

from tradebot.core.enums import NoSignalReason
from tradebot.signals.models import NoSignalLog, SignalCandidate


class RiskValidator:
    def __init__(
        self,
        min_rr: Decimal = Decimal("2.0"),
        min_stop_atr: Decimal = Decimal("0.5"),
        max_tp_atr: Decimal = Decimal("6.0"),
        entry_late_atr: Decimal = Decimal("1.0"),
    ) -> None:
        self.min_rr = min_rr
        self.min_stop_atr = min_stop_atr
        self.max_tp_atr = max_tp_atr
        self.entry_late_atr = entry_late_atr

    def validate(self, candidate: SignalCandidate, atr14: Decimal) -> SignalCandidate | NoSignalLog:
        stop_distance = abs(candidate.entry - candidate.stop)
        take_distance = abs(candidate.take - candidate.entry)

        if stop_distance == 0:
            return NoSignalLog(
                ticker=candidate.ticker, figi=candidate.figi, tf=candidate.tf,
                reason=NoSignalReason.STOP_TOO_TIGHT,
                details="stop == entry",
            )
        if atr14 > 0 and stop_distance < self.min_stop_atr * atr14:
            return NoSignalLog(
                ticker=candidate.ticker, figi=candidate.figi, tf=candidate.tf,
                reason=NoSignalReason.STOP_TOO_TIGHT,
                details=f"stop_dist={stop_distance:.4f} < {self.min_stop_atr}*ATR={self.min_stop_atr * atr14:.4f}",
            )
        rr = take_distance / stop_distance if stop_distance > 0 else Decimal(0)
        if rr < self.min_rr:
            return NoSignalLog(
                ticker=candidate.ticker, figi=candidate.figi, tf=candidate.tf,
                reason=NoSignalReason.BAD_RR,
                details=f"RR={rr:.2f} < {self.min_rr}",
            )
        if atr14 > 0 and take_distance > self.max_tp_atr * atr14:
            return NoSignalLog(
                ticker=candidate.ticker, figi=candidate.figi, tf=candidate.tf,
                reason=NoSignalReason.TARGET_UNREALISTIC,
                details=f"take_dist={take_distance:.4f} > {self.max_tp_atr}*ATR={self.max_tp_atr * atr14:.4f}",
            )
        return candidate
