from __future__ import annotations

from typing import Dict, Any


def render_prop_report(bundle: Dict[str, Any]) -> str:
    if not bundle.get("ok"):
        return f"Error: {bundle.get('error')}"

    player = bundle["player"]["name"]
    game = bundle["game"]
    recent = bundle["recent_form"]

    lines = []
    lines.append(f"{player.upper()} — {game['date']}")
    lines.append(f"{game['home']} vs {game['away']}")
    lines.append("")

    if recent and recent["n"] > 0:
        avg = recent["avg"]
        lines.append(f"Recent Form (Last {recent['n']})")
        lines.append(
            f"PTS: {avg['points']} | REB: {avg['rebounds']} | AST: {avg['assists']}"
        )
        lines.append("")

    for p in bundle["props"]:
        lines.append(f"{p['prop_type'].title()} {p['line']} @ {p['price']}")
        lines.append(
            f"Edge: {p['edge']} | Bias: {str(p['bias']).upper()} | Confidence: {str(p['confidence']).upper()}"
        )
        lines.append("")

    return "\n".join(lines)
