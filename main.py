"""
Price Watchdog — entry point.

Usage:
  python main.py check --url URL --target PRICE [--currency PKR]
  python main.py monitor [--interval HOURS]
  python main.py dashboard
  python main.py list
"""
import argparse
import logging
import subprocess
import sys
import time

import schedule

from config import CHECK_INTERVAL_HOURS, validate_config
from core.database import get_all_products, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _run_check(url: str, target: float, currency: str) -> None:
    """Run a single agent price check with clean error reporting."""
    from crew import run_price_check
    try:
        run_price_check(url, target, currency)
    except ValueError as exc:
        logger.error("Invalid input: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.error("Price check failed for %s — %s", url, exc)


def _check_all_active() -> None:
    """Run price checks for every active product in the database."""
    products = get_all_products(active_only=True)
    if not products:
        logger.info("No active products to check.")
        return

    logger.info("Starting scheduled check — %d product(s)", len(products))
    for p in products:
        logger.info("Checking: %s", p["url"])
        _run_check(p["url"], p["target_price"], p["currency"])

    logger.info("Scheduled check complete.")


# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_check(args: argparse.Namespace) -> None:
    """One-time price check for a single URL."""
    validate_config()
    init_db()
    _run_check(args.url.strip(), args.target, args.currency)


def cmd_monitor(args: argparse.Namespace) -> None:
    """Continuous monitoring — checks all active products every N hours."""
    validate_config()
    init_db()

    interval = args.interval or CHECK_INTERVAL_HOURS
    logger.info("Monitor mode — checking every %d hour(s). Press Ctrl+C to stop.", interval)

    # Run immediately on start, then on schedule
    _check_all_active()

    schedule.every(interval).hours.do(_check_all_active)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Monitor stopped.")


def cmd_dashboard(_args: argparse.Namespace) -> None:
    """Launch the Streamlit dashboard."""
    import os
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    logger.info("Launching dashboard at http://localhost:8501")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", dashboard_path],
        check=False,
    )


def cmd_list(_args: argparse.Namespace) -> None:
    """List all tracked products and their latest prices."""
    init_db()
    from core.database import get_latest_price

    products = get_all_products(active_only=False)
    if not products:
        print("No products tracked yet.")
        print("  Add one:  python main.py check --url URL --target PRICE")
        return

    print(f"\n{'ID':<4} {'Status':<8} {'Target':>12} {'Current':>12}  Product")
    print("─" * 70)
    for p in products:
        latest = get_latest_price(p["id"])
        current = f"{p['currency']} {latest['price']:,.0f}" if latest and latest["price"] else "No data"
        target  = f"{p['currency']} {p['target_price']:,.0f}"
        status  = "Active" if p["is_active"] else "Paused"
        name    = p.get("name") or p["url"].split("/")[-1][:35]
        print(f"{p['id']:<4} {status:<8} {target:>12} {current:>12}  {name}")
    print()


# ── CLI parser ─────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="price-watchdog",
        description="Autonomous AI price tracker for Pakistani e-commerce",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # check
    p_check = sub.add_parser("check", help="One-time price check for a URL")
    p_check.add_argument("--url",      required=True, help="Product URL to check")
    p_check.add_argument("--target",   required=True, type=float, help="Target price (numeric)")
    p_check.add_argument("--currency", default="PKR", help="Currency code (default: PKR)")
    p_check.set_defaults(func=cmd_check)

    # monitor
    p_monitor = sub.add_parser("monitor", help="Continuous monitoring of all active products")
    p_monitor.add_argument("--interval", type=int, default=None,
                           help=f"Check interval in hours (default: {CHECK_INTERVAL_HOURS})")
    p_monitor.set_defaults(func=cmd_monitor)

    # dashboard
    p_dash = sub.add_parser("dashboard", help="Launch the Streamlit dashboard")
    p_dash.set_defaults(func=cmd_dashboard)

    # list
    p_list = sub.add_parser("list", help="List all tracked products")
    p_list.set_defaults(func=cmd_list)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
