from abc import ABC, abstractmethod

from tradebot.analysis.snapshot import AnalysisSnapshot
from tradebot.signals.models import NoSignalLog, SignalCandidate


class BaseStrategy(ABC):
    name: str

    @abstractmethod
    def evaluate(self, snap: AnalysisSnapshot) -> SignalCandidate | NoSignalLog:
        ...
