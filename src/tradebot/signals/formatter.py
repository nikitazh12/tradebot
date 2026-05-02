"""SignalFormatter — форматирует SignalCandidate в Telegram HTML."""
from __future__ import annotations

from tradebot.ai.analyzer import AIAnalysis
from tradebot.core.enums import Direction, Horizon, RiskLevel, SetupType
from tradebot.signals.models import SignalCandidate

_DIRECTION_EMOJI = {
    Direction.BUY: "🟢",
    Direction.SELL: "🔴",
}

_SETUP_LABEL = {
    SetupType.BREAKOUT: "Пробой",
    SetupType.BOUNCE: "Отскок",
    SetupType.PULLBACK: "Откат в тренде",
    SetupType.BREAKDOWN: "Пробой вниз",
    SetupType.ROCKET: "Ракета",
}

_HORIZON_LABEL = {
    Horizon.INTRADAY: "Интрадей",
    Horizon.SHORT_1_3D: "1–3 дня",
    Horizon.SHORT_2_5D: "2–5 дней",
}

_RISK_LABEL = {
    RiskLevel.LOW: "Низкий",
    RiskLevel.MEDIUM: "Средний",
    RiskLevel.HIGH: "Высокий",
}


class SignalFormatter:
    def format(self, candidate: SignalCandidate, ai: AIAnalysis | None = None) -> str:
        direction_emoji = _DIRECTION_EMOJI.get(candidate.direction, "⚪")
        setup_label = _SETUP_LABEL.get(candidate.setup, candidate.setup)
        horizon_label = _HORIZON_LABEL.get(candidate.horizon, candidate.horizon)
        risk_label = _RISK_LABEL.get(candidate.risk_level, candidate.risk_level)

        stop_dist = abs(candidate.take - candidate.entry)
        rr_dist = abs(candidate.entry - candidate.stop)
        rr = float(stop_dist / rr_dist) if rr_dist else 0.0

        lines = [
            f"{direction_emoji} <b>{candidate.ticker}</b> — {setup_label} [{candidate.tf}]",
            "",
            f"Вход:  <code>{candidate.entry}</code>",
            f"Стоп:  <code>{candidate.stop}</code>",
            f"Тейк:  <code>{candidate.take}</code>",
            f"R/R:   <b>{rr:.1f}</b>",
            "",
            f"Горизонт: {horizon_label}",
            f"Риск:     {risk_label}",
            "",
            f"📋 {candidate.reasoning}",
        ]

        if ai is not None and ai.comment and ai.comment not in ("noop", ""):
            conf_pct = int(ai.confidence * 100)
            lines.append(f"\n🤖 AI ({conf_pct}%): {ai.comment}")

        return "\n".join(lines)
