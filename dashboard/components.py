"""Reusable Streamlit UI components and chart builders."""
from datetime import datetime, timezone
from typing import Optional

import plotly.graph_objects as go
import streamlit as st


# ── Metric cards ───────────────────────────────────────────────────────────────

def metric_card(label: str, value: str, delta: Optional[str] = None, color: str = "#1f77b4") -> None:
    """Render a single styled metric card."""
    delta_html = f"<p style='color:#888;font-size:13px;margin:2px 0'>{delta}</p>" if delta else ""
    st.markdown(
        f"""
        <div style='background:#1e1e2e;border-radius:10px;padding:18px 20px;
                    border-left:4px solid {color};margin-bottom:8px'>
            <p style='color:#aaa;font-size:13px;margin:0 0 4px 0'>{label}</p>
            <p style='color:#fff;font-size:26px;font-weight:700;margin:0'>{value}</p>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    """Return coloured HTML badge for availability status."""
    colours = {
        "In Stock":      ("#00c875", "#003d1f"),
        "Out of Stock":  ("#ff4b4b", "#3d0000"),
        "Limited Stock": ("#ffa500", "#3d2600"),
        "Pre-Order":     ("#a78bfa", "#1e1040"),
        "Unknown":       ("#888", "#222"),
    }
    bg, fg = colours.get(status, ("#888", "#222"))
    return (
        f"<span style='background:{bg};color:{fg};padding:2px 10px;"
        f"border-radius:12px;font-size:12px;font-weight:600'>{status}</span>"
    )


def trend_arrow(history: list[dict]) -> str:
    """Return ▲/▼/— based on last two price checks."""
    prices = [h["price"] for h in history if h["price"] is not None]
    if len(prices) < 2:
        return "—"
    return "🟢 ▼" if prices[0] < prices[1] else "🔴 ▲" if prices[0] > prices[1] else "⚪ —"


# ── Charts ─────────────────────────────────────────────────────────────────────

def price_trend_chart(history: list[dict], product_name: str, target_price: float) -> go.Figure:
    """Build a Plotly line chart of price over time with a target price line."""
    records = [h for h in reversed(history) if h["price"] is not None]
    if not records:
        fig = go.Figure()
        fig.update_layout(title="No price data yet", template="plotly_dark")
        return fig

    dates = [h["checked_at"] for h in records]
    prices = [h["price"] for h in records]
    currency = records[-1].get("currency", "PKR")

    fig = go.Figure()

    # Price line
    fig.add_trace(go.Scatter(
        x=dates, y=prices,
        mode="lines+markers",
        name="Price",
        line=dict(color="#4c9be8", width=2),
        marker=dict(size=6),
        hovertemplate=f"%{{x}}<br>{currency} %{{y:,.0f}}<extra></extra>",
    ))

    # Target price line
    fig.add_hline(
        y=target_price,
        line_dash="dash",
        line_color="#ff6b6b",
        annotation_text=f"Target: {currency} {target_price:,.0f}",
        annotation_position="bottom right",
        annotation_font_color="#ff6b6b",
    )

    fig.update_layout(
        title=dict(text=f"Price History — {product_name}", font=dict(size=15)),
        xaxis_title="Date",
        yaxis_title=f"Price ({currency})",
        template="plotly_dark",
        height=380,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


# ── Tables ─────────────────────────────────────────────────────────────────────

def history_table(history: list[dict]) -> None:
    """Render price history as a clean Streamlit table."""
    if not history:
        st.info("No price checks recorded yet.")
        return

    import pandas as pd
    rows = []
    for h in history:
        rows.append({
            "Date": h["checked_at"],
            "Price": f"{h['currency']} {h['price']:,.0f}" if h["price"] else "N/A",
            "Variant": h["variant"] or "—",
            "Availability": h["availability"],
            "Reasoning": (h["agent_reasoning"] or "")[:80] + ("…" if len(h.get("agent_reasoning") or "") > 80 else ""),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def alerts_table(alerts: list[dict]) -> None:
    """Render alerts as a styled table."""
    if not alerts:
        st.info("No alerts triggered yet.")
        return

    import pandas as pd
    rows = []
    for a in alerts:
        rows.append({
            "Date": a["created_at"],
            "Type": a["alert_type"].replace("_", " ").title(),
            "Old Price": f"PKR {a['old_price']:,.0f}" if a["old_price"] else "—",
            "New Price": f"PKR {a['new_price']:,.0f}" if a["new_price"] else "—",
            "Drop %": f"{a['drop_percentage']:.1f}%" if a["drop_percentage"] else "—",
            "Sent Via": a["sent_via"] or "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def fmt_price(price: Optional[float], currency: str = "PKR") -> str:
    """Format a price for display."""
    return f"{currency} {price:,.0f}" if price is not None else "N/A"


def time_ago(ts_str: Optional[str]) -> str:
    """Convert an ISO timestamp string to a human-readable 'X ago' string."""
    if not ts_str:
        return "Never"
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - ts
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        if seconds < 3600:
            return f"{seconds // 60}m ago"
        if seconds < 86400:
            return f"{seconds // 3600}h ago"
        return f"{seconds // 86400}d ago"
    except (ValueError, TypeError):
        return ts_str
