from __future__ import annotations

from typing import Any, Dict, List, Optional


def _fmt_float(x: Any, nd: int = 2) -> str:
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)


def _group_main_markets(main_odds: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {"moneyline": [], "spread": [], "total": []}
    for row in main_odds or []:
        mt = str(row.get("market_type") or "").lower()
        if mt in grouped:
            grouped[mt].append(row)
    return grouped


def _render_moneyline(rows: List[Dict[str, Any]]) -> List[str]:
    # expects outcomes home/away
    if not rows:
        return []
    # keep stable order: home then away if present
    home = [r for r in rows if str(r.get("outcome")).lower() == "home"]
    away = [r for r in rows if str(r.get("outcome")).lower() == "away"]
    out = []
    for r in (home + away):
        out.append(f"ML {str(r.get('outcome')).upper()}: {_fmt_float(r.get('price'))}")
    return out


def _render_spread(rows: List[Dict[str, Any]]) -> List[str]:
    if not rows:
        return []
    # outcomes home/away with line
    out = []
    # stable: home then away
    home = [r for r in rows if str(r.get("outcome")).lower() == "home"]
    away = [r for r in rows if str(r.get("outcome")).lower() == "away"]
    for r in (home + away):
        line = r.get("line")
        out.append(f"SPREAD {str(r.get('outcome')).upper()} {line}: {_fmt_float(r.get('price'))}")
    return out


def _render_total(rows: List[Dict[str, Any]]) -> List[str]:
    if not rows:
        return []
    # outcomes over/under with line
    over = [r for r in rows if str(r.get("outcome")).lower() == "over"]
    under = [r for r in rows if str(r.get("outcome")).lower() == "under"]
    out = []
    for r in (over + under):
        line = r.get("line")
        out.append(f"TOTAL {str(r.get('outcome')).upper()} {line}: {_fmt_float(r.get('price'))}")
    return out


def render_prop_report(bundle: Dict[str, Any]) -> str:
    """
    Render a simple markdown-ish trader report from the research bundle.

    Sections:
    - Header: PLAYER — DATE, matchup
    - Recent form summary (if present)
    - Main markets (if present)
    - Props list (with any computed edge fields)
    """
    if not bundle or not bundle.get("ok"):
        return str(bundle)

    player = bundle.get("player") or {}
    game = bundle.get("game") or {}

    player_name = str(player.get("name") or "UNKNOWN").upper()
    game_date = str(game.get("date") or "UNKNOWN")
    home = str(game.get("home") or "HOME")
    away = str(game.get("away") or "AWAY")

    lines: List[str] = []
    lines.append(f"{player_name} — {game_date}")
    lines.append(f"{home} vs {away}")
    lines.append("")

    recent = bundle.get("recent_form") or {}
    avg = (recent.get("avg") or {}) if isinstance(recent, dict) else {}
    n = recent.get("n") if isinstance(recent, dict) else None
    if avg and n:
        lines.append(f"Recent Form (Last {n})")
        pts = avg.get("points")
        reb = avg.get("rebounds")
        ast = avg.get("assists")
        parts = []
        if pts is not None:
            parts.append(f"PTS: {_fmt_float(pts, 1)}")
        if reb is not None:
            parts.append(f"REB: {_fmt_float(reb, 1)}")
        if ast is not None:
            parts.append(f"AST: {_fmt_float(ast, 1)}")
        if parts:
            lines.append(" | ".join(parts))
            lines.append("")

    main_odds = bundle.get("main_odds") or []
    if isinstance(main_odds, list) and len(main_odds) > 0:
        # assume one book for now; show first book label encountered
        book_label: Optional[str] = None
        for r in main_odds:
            if r.get("book"):
                book_label = str(r.get("book"))
                break

        lines.append(f"Main Markets ({book_label or 'book'})")
        grouped = _group_main_markets(main_odds)

        ml_lines = _render_moneyline(grouped["moneyline"])
        sp_lines = _render_spread(grouped["spread"])
        tot_lines = _render_total(grouped["total"])

        for l in (ml_lines + sp_lines + tot_lines):
            lines.append(l)
        lines.append("")

    props = bundle.get("props") or []
    for p in props:
        prop_type = str(p.get("prop_type") or "").title()
        line = p.get("line")
        price = p.get("price")
        lines.append(f"{prop_type} {line} @ {price}")

        # optional v1 “edge” fields
        edge = p.get("edge")
        bias = p.get("bias")
        conf = p.get("confidence")

        detail_parts = []
        if edge is not None:
            detail_parts.append(f"Edge: {edge}")
        if bias:
            detail_parts.append(f"Bias: {str(bias).upper()}")
        if conf:
            detail_parts.append(f"Confidence: {str(conf).upper()}")

        if detail_parts:
            lines.append(" | ".join(detail_parts))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
