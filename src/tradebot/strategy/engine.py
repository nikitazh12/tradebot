from tradebot.analysis.snapshot import AnalysisSnapshot
from tradebot.signals.models import NoSignalLog, SignalCandidate
from tradebot.strategy.base import BaseStrategy
from tradebot.strategy.bounce_level import BounceStrategy
from tradebot.strategy.breakdown import BreakdownStrategy
from tradebot.strategy.pullback_in_trend import PullbackStrategy
from tradebot.strategy.trend_breakout import TrendBreakoutStrategy


class StrategyEngine:
    def __init__(self) -> None:
        self._strategies: list[BaseStrategy] = [
            TrendBreakoutStrategy(),
            BounceStrategy(),
            PullbackStrategy(),
            BreakdownStrategy(),
        ]

    def run(self, snap: AnalysisSnapshot) -> list[SignalCandidate | NoSignalLog]:
        return [s.evaluate(snap) for s in self._strategies]
