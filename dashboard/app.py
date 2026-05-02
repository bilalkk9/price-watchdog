"""Streamlit dashboard — Price Watchdog UI (Phase 3)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st

st.set_page_config(
    page_title="Price Watchdog",
    page_icon="🐕",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd

from core.database import (
    add_product,
    deactivate_product,
    export_history_csv,
    export_history_json,
    get_alerts,
    get_all_products,
    get_latest_price,
    get_price_history,
    get_product,
    get_product_by_url,
    init_db,
    update_product,
)
from dashboard.components import (
    alerts_table,
    fmt_price,
    history_table,
    metric_card,
    price_trend_chart,
    status_badge,
    time_ago,
    trend_arrow,
)

init_db()

# ── Global styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0e0e1a; }
    section[data-testid="stSidebar"] { background-color: #161625; }
    .block-container { padding-top: 1.5rem; }
    h1, h2, h3 { color: #e0e0ff; }
    .stButton > button {
        border-radius: 8px; font-weight: 600;
        border: 1px solid #4c9be8; color: #4c9be8; background: transparent;
    }
    .stButton > button:hover { background: #4c9be8; color: #fff; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🐕 Price Watchdog")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "➕ Add Product", "📈 Product Detail", "🔔 Alerts", "⚙️ Settings"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Autonomous AI price tracker\nfor Pakistani e-commerce")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Dashboard
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("📊 Dashboard")

    products = get_all_products(active_only=False)
    active = [p for p in products if p["is_active"]]
    all_alerts = get_alerts(limit=100)
    today = pd.Timestamp.now().date()
    alerts_today = [
        a for a in all_alerts
        if a["created_at"] and str(a["created_at"])[:10] == str(today)
    ]

    last_check = "Never"
    for p in active:
        lp = get_latest_price(p["id"])
        if lp:
            last_check = time_ago(lp["checked_at"])
            break

    # Summary cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Products", str(len(products)), color="#4c9be8")
    with c2:
        metric_card("Active Tracking", str(len(active)), color="#00c875")
    with c3:
        metric_card("Alerts Today", str(len(alerts_today)), color="#ff6b6b")
    with c4:
        metric_card("Last Checked", last_check, color="#a78bfa")

    st.markdown("---")
    st.subheader("Tracked Products")

    if not products:
        st.info("No products tracked yet. Go to **➕ Add Product** to start.")
    else:
        for p in products:
            latest = get_latest_price(p["id"])
            history = get_price_history(p["id"], limit=10)
            current_price = latest["price"] if latest else None
            availability = latest["availability"] if latest else "Unknown"

            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
            with col1:
                name = p.get("name") or p["url"].split("/")[-1][:40]
                st.markdown(f"**{name}**")
                st.caption(p["url"][:55] + ("…" if len(p["url"]) > 55 else ""))
            with col2:
                st.markdown(fmt_price(current_price, p["currency"]))
            with col3:
                st.markdown(fmt_price(p["target_price"], p["currency"]))
            with col4:
                st.markdown(status_badge(availability), unsafe_allow_html=True)
            with col5:
                st.markdown(trend_arrow(history))
            with col6:
                active_label = "Active" if p["is_active"] else "Paused"
                st.caption(active_label)
            st.markdown("<hr style='margin:6px 0;border-color:#2a2a3e'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Add Product
# ══════════════════════════════════════════════════════════════════════════════
elif page == "➕ Add Product":
    st.title("➕ Add Product to Track")
    st.markdown("Paste any product URL — the AI agent will validate, scrape, and extract the price automatically.")

    with st.form("add_product_form"):
        url = st.text_input("Product URL", placeholder="https://priceoye.pk/samsung-galaxy-s24")
        col1, col2 = st.columns(2)
        with col1:
            target_price = st.number_input("Target Price", min_value=1.0, value=50000.0, step=500.0)
        with col2:
            currency = st.selectbox("Currency", ["PKR", "USD", "EUR", "GBP"], index=0)
        submitted = st.form_submit_button("🚀 Start Tracking", use_container_width=True)

    if submitted:
        url = url.strip()
        if not url:
            st.error("Please enter a product URL.")
        elif not url.startswith(("http://", "https://")):
            st.error("URL must start with http:// or https://")
        elif get_product_by_url(url):
            st.warning("This URL is already being tracked.")
        else:
            # Quick URL validation before running the agent
            from core.url_validator import validate_url
            with st.spinner("Validating URL…"):
                check = validate_url(url)

            if not check["valid"]:
                st.error(f"❌ URL check failed: {check['message']}")
            else:
                st.success(f"✅ URL is reachable ({check['response_time_ms']:.0f}ms)")
                pid = add_product(url, target_price, currency)
                st.success(f"Product added (id={pid}). Run a price check from the terminal to populate data:")
                st.code(
                    f'python -c "from crew import run_price_check; '
                    f'run_price_check(\'{url}\', {target_price}, \'{currency}\')"',
                    language="bash",
                )
                st.info("Tip: after running the agent, come back to **📈 Product Detail** to see the chart.")

    # Show existing products as a quick reference
    st.markdown("---")
    st.subheader("Currently Tracked")
    products = get_all_products(active_only=False)
    if products:
        for p in products:
            st.markdown(
                f"- **{p.get('name') or 'Unnamed'}** — {p['url'][:60]} "
                f"| Target: {fmt_price(p['target_price'], p['currency'])} "
                f"| {'✅ Active' if p['is_active'] else '⏸ Paused'}"
            )
    else:
        st.caption("None yet.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Product Detail
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Product Detail":
    st.title("📈 Product Detail")

    products = get_all_products(active_only=False)
    if not products:
        st.info("No products tracked yet. Go to **➕ Add Product** first.")
        st.stop()

    options = {
        f"{p.get('name') or p['url'].split('/')[-1][:40]} (id={p['id']})": p["id"]
        for p in products
    }
    selected_label = st.selectbox("Select product", list(options.keys()))
    product_id = options[selected_label]
    product = get_product(product_id)
    latest = get_latest_price(product_id)
    history = get_price_history(product_id, limit=50)
    product_alerts = get_alerts(product_id, limit=20)

    # Header info
    col1, col2 = st.columns([2, 1])
    with col1:
        name = product.get("name") or "Unnamed Product"
        st.markdown(f"### {name}")
        st.markdown(f"🔗 [{product['url'][:70]}]({product['url']})")
    with col2:
        if latest:
            st.markdown(status_badge(latest["availability"]), unsafe_allow_html=True)
            st.caption(f"Last checked: {time_ago(latest['checked_at'])}")

    # Key metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Current Price", fmt_price(latest["price"] if latest else None, product["currency"]), color="#4c9be8")
    with c2:
        metric_card("Target Price", fmt_price(product["target_price"], product["currency"]), color="#ff6b6b")
    with c3:
        metric_card("Checks", str(len(history)), color="#00c875")
    with c4:
        metric_card("Alerts", str(len(product_alerts)), color="#a78bfa")

    # Price chart
    st.markdown("---")
    fig = price_trend_chart(history, name, product["target_price"])
    st.plotly_chart(fig, use_container_width=True)

    # Tabs for history / alerts / reasoning
    tab1, tab2, tab3 = st.tabs(["📋 Price History", "🔔 Alerts", "🧠 Agent Reasoning"])

    with tab1:
        history_table(history)

    with tab2:
        alerts_table(product_alerts)

    with tab3:
        if not history:
            st.info("No checks recorded yet.")
        else:
            for h in history[:10]:
                with st.expander(f"{h['checked_at']} — {fmt_price(h['price'], h['currency'])}"):
                    st.markdown(f"**Availability:** {h['availability']}")
                    st.markdown(f"**Variant:** {h['variant'] or 'N/A'}")
                    st.markdown(f"**Reasoning:**\n\n{h['agent_reasoning'] or 'Not recorded'}")

    # Action buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        new_target = st.number_input(
            "New Target Price", value=float(product["target_price"]), step=500.0, key="new_target"
        )
        if st.button("💾 Update Target"):
            update_product(product_id, target_price=new_target)
            st.success("Target price updated!")
            st.rerun()

    with col2:
        label = "⏸ Pause" if product["is_active"] else "▶️ Resume"
        if st.button(label):
            update_product(product_id, is_active=0 if product["is_active"] else 1)
            st.rerun()

    with col3:
        if st.button("📥 Export CSV"):
            if history:
                path = export_history_csv(product_id, f"product_{product_id}_history.csv")
                st.success(f"Saved to {path}")
            else:
                st.warning("No data to export.")

    with col4:
        if st.button("📥 Export JSON"):
            if history:
                path = export_history_json(product_id, f"product_{product_id}_history.json")
                st.success(f"Saved to {path}")
            else:
                st.warning("No data to export.")

    # Danger zone
    with st.expander("⚠️ Danger Zone"):
        if st.button("🗑️ Remove Product", type="primary"):
            deactivate_product(product_id)
            st.success("Product deactivated.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Alerts
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Alerts":
    st.title("🔔 Alert History")

    products = get_all_products(active_only=False)
    all_alerts = get_alerts(limit=200)

    if not all_alerts:
        st.info("No alerts have been triggered yet.")
        st.stop()

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        product_options = {"All Products": None} | {
            f"{p.get('name') or p['url'].split('/')[-1][:35]} (id={p['id']})": p["id"]
            for p in products
        }
        selected_product = st.selectbox("Filter by product", list(product_options.keys()))
        filter_pid = product_options[selected_product]
    with col2:
        alert_types = ["All Types", "price_drop", "back_in_stock", "target_reached"]
        selected_type = st.selectbox("Filter by type", alert_types)

    # Apply filters
    filtered = all_alerts
    if filter_pid:
        filtered = [a for a in filtered if a["product_id"] == filter_pid]
    if selected_type != "All Types":
        filtered = [a for a in filtered if a["alert_type"] == selected_type]

    st.markdown(f"**{len(filtered)} alert(s)**")
    st.markdown("---")

    # Enrich alerts with product name
    pid_to_name = {p["id"]: (p.get("name") or p["url"].split("/")[-1][:35]) for p in products}

    for a in filtered:
        product_name = pid_to_name.get(a["product_id"], f"Product #{a['product_id']}")
        alert_label = a["alert_type"].replace("_", " ").title()
        colour = "#ff6b6b" if "drop" in a["alert_type"] else "#00c875"

        with st.expander(
            f"[{a['created_at'][:16]}]  {alert_label}  —  {product_name}"
        ):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Previous:** {fmt_price(a['old_price'])}")
                st.markdown(f"**Current:** {fmt_price(a['new_price'])}")
            with c2:
                pct = a.get("drop_percentage")
                st.markdown(f"**Drop:** {f'{pct:.1f}%' if pct else '—'}")
                st.markdown(f"**Sent via:** {a.get('sent_via') or '—'}")
            with c3:
                st.markdown(f"**Time:** {a['created_at']}")
            if a.get("message"):
                st.markdown(f"**Message:** {a['message']}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Settings
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")

    st.subheader("Scheduler")
    from config import CHECK_INTERVAL_HOURS
    st.markdown(f"Current check interval: **{CHECK_INTERVAL_HOURS} hours**")
    st.info("To change the interval, update `CHECK_INTERVAL_HOURS` in your `.env` file and restart.")

    st.markdown("---")
    st.subheader("Email Notifications")

    from config import GMAIL_ADDRESS
    if GMAIL_ADDRESS:
        st.success(f"✅ Gmail configured: `{GMAIL_ADDRESS}`")
    else:
        st.warning("Email not configured. Add `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` to `.env`.")
        with st.expander("How to set up Gmail App Password"):
            st.markdown("""
1. Go to **Google Account → Security → 2-Step Verification**
2. Scroll to **App Passwords**
3. Select **Mail** → **Other (Custom Name)** → `Price Watchdog`
4. Copy the 16-character password
5. Add to `.env`:
   ```
   GMAIL_ADDRESS=your@gmail.com
   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   ```
""")

    st.markdown("---")
    st.subheader("Manual Check All")
    st.markdown("Run the agent on every active product right now.")

    if st.button("🔄 Check All Products Now", use_container_width=True):
        products = get_all_products(active_only=True)
        if not products:
            st.warning("No active products to check.")
        else:
            from crew import run_price_check
            progress = st.progress(0)
            status_area = st.empty()
            for i, p in enumerate(products):
                status_area.info(f"Checking {i+1}/{len(products)}: {p['url'][:60]}")
                try:
                    run_price_check(p["url"], p["target_price"], p["currency"])
                    st.success(f"✅ {p['url'][:55]}")
                except Exception as exc:
                    st.error(f"❌ {p['url'][:55]} — {exc}")
                progress.progress((i + 1) / len(products))
            status_area.success("All products checked!")

    st.markdown("---")
    st.subheader("Database")
    from config import DATABASE_PATH
    st.markdown(f"Database path: `{DATABASE_PATH}`")
    products_all = get_all_products(active_only=False)
    st.markdown(f"Total products: **{len(products_all)}**")
    total_checks = sum(len(get_price_history(p["id"], limit=10000)) for p in products_all)
    st.markdown(f"Total price checks: **{total_checks}**")
