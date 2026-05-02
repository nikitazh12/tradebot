"""Тесты AIAnalysis dataclass."""
from tradebot.ai.analyzer import AIAnalysis


def test_approved_factory() -> None:
    a = AIAnalysis.approved(comment="good", confidence=0.9)
    assert a.approve is True
    assert a.confidence == 0.9
    assert a.comment == "good"


def test_rejected_factory() -> None:
    a = AIAnalysis.rejected(comment="bad setup", confidence=0.8)
    assert a.approve is False
    assert a.confidence == 0.8


def test_approved_defaults() -> None:
    a = AIAnalysis.approved()
    assert a.approve is True
    assert a.confidence == 1.0
    assert a.comment == ""


def test_rejected_defaults() -> None:
    a = AIAnalysis.rejected()
    assert a.approve is False
    assert a.confidence == 1.0
