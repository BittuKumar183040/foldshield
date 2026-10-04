from ui.components.cards import badge, card_grid, section, stat_card
from ui.config import signal_for
from ui.html import esc, fmt, render
from ui.theme import score_color


def signal_cards(per_signal: dict, scores: dict, weights: dict) -> None:
    cards = []
    for name in per_signal:
        sig = signal_for(name)
        cards.append(stat_card(
            sig.display, fmt(scores.get(sig.key)), score_color(scores.get(sig.key)),
            badge_text=sig.phase, sub=f"weight {fmt(weights.get(sig.key, 0.0), '.2f')}"))
    card_grid(cards)


def signal_table(per_signal: dict, scores: dict, weights: dict) -> None:
    rows = ""
    for name, interpretation in per_signal.items():
        sig = signal_for(name)
        val = scores.get(sig.key)
        rows += (
            f'<tr><td class="nowrap">{esc(sig.display)}{badge(sig.phase)}</td>'
            f'<td class="num" style="color:{score_color(val)}">{fmt(val)}</td>'
            f'<td>{esc(interpretation)}</td>'
            f'<td class="mid">{fmt(weights.get(sig.key, 0.0), ".2f")}</td></tr>'
        )
    render(
        '<div class="fs-tablewrap"><table class="fs-table"><thead><tr>'
        '<th>Signal</th><th style="text-align:center">Score</th>'
        '<th>Interpretation</th><th style="text-align:center">Weight</th>'
        f'</tr></thead><tbody>{rows}</tbody></table></div>'
    )


def signals_panel(fusion: dict) -> None:
    section("FoldShield++ signals")
    per_signal = fusion.get("per_signal") or {}
    scores = fusion.get("signal_scores") or {}
    weights = fusion.get("weights_used") or {}
    signal_cards(per_signal, scores, weights)
    signal_table(per_signal, scores, weights)
