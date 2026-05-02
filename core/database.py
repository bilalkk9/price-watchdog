"""SQLite persistence layer — products, price checks, and alerts (FR7)."""
import csv
import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional

from config import DATABASE_PATH, EXPORTS_DIR

logger = logging.getLogger(__name__)

# ── Schema ─────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    url         TEXT    NOT NULL UNIQUE,
    name        TEXT,
    target_price REAL   NOT NULL,
    currency    TEXT    NOT NULL DEFAULT 'PKR',
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS price_checks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL,
    price           REAL,
    currency        TEXT    NOT NULL DEFAULT 'PKR',
    variant         TEXT,
    availability    TEXT    NOT NULL DEFAULT 'Unknown',
    agent_reasoning TEXT,
    raw_extraction  TEXT,
    checked_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL,
    alert_type      TEXT    NOT NULL,
    old_price       REAL,
    new_price       REAL,
    drop_percentage REAL,
    message         TEXT,
    sent_via        TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""


# ── Connection helper ──────────────────────────────────────────────────────────

@contextmanager
def _conn() -> Generator[sqlite3.Connection, None, None]:
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    """Create tables if they don't exist. Safe to call multiple times."""
    with _conn() as con:
        con.executescript(_DDL)
    logger.info("database initialised at %s", DATABASE_PATH)


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row else None


# ── Products ───────────────────────────────────────────────────────────────────

def add_product(url: str, target_price: float, currency: str = "PKR") -> int:
    """Insert a new product; return its id. Raises ValueError on duplicate URL."""
    if not url or not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL: {url!r}")
    if target_price <= 0:
        raise ValueError(f"target_price must be positive, got {target_price}")

    with _conn() as con:
        cur = con.execute(
            "INSERT INTO products (url, target_price, currency) VALUES (?, ?, ?)",
            (url, target_price, currency),
        )
        return cur.lastrowid


def get_product(product_id: int) -> Optional[dict]:
    """Return a product row as dict, or None if not found."""
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
    return _row_to_dict(row)


def get_product_by_url(url: str) -> Optional[dict]:
    """Return a product row matching the URL, or None."""
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM products WHERE url = ?", (url,)
        ).fetchone()
    return _row_to_dict(row)


def get_all_products(active_only: bool = True) -> list[dict]:
    """Return all products, optionally filtered to active ones."""
    query = "SELECT * FROM products"
    params: tuple = ()
    if active_only:
        query += " WHERE is_active = 1"
    with _conn() as con:
        rows = con.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def update_product(product_id: int, **kwargs: Any) -> None:
    """Update allowed product fields. Raises KeyError for unknown fields."""
    allowed = {"name", "target_price", "currency", "is_active"}
    bad = set(kwargs) - allowed
    if bad:
        raise KeyError(f"Unknown product fields: {bad}")

    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [datetime.now(timezone.utc).isoformat(), product_id]
    with _conn() as con:
        con.execute(
            f"UPDATE products SET {set_clause}, updated_at = ? WHERE id = ?",
            values,
        )


def deactivate_product(product_id: int) -> None:
    """Soft-delete a product (sets is_active = 0)."""
    update_product(product_id, is_active=0)


# ── Price checks ───────────────────────────────────────────────────────────────

def add_price_check(
    product_id: int,
    price: Optional[float],
    currency: str,
    variant: Optional[str],
    availability: str,
    reasoning: Optional[str],
    raw: Optional[str],
) -> int:
    """Record a single price check; return its id."""
    with _conn() as con:
        cur = con.execute(
            """INSERT INTO price_checks
               (product_id, price, currency, variant, availability, agent_reasoning, raw_extraction)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (product_id, price, currency, variant, availability, reasoning, raw),
        )
        return cur.lastrowid


def get_price_history(product_id: int, limit: int = 50) -> list[dict]:
    """Return the most recent `limit` price checks for a product."""
    with _conn() as con:
        rows = con.execute(
            """SELECT * FROM price_checks
               WHERE product_id = ?
               ORDER BY checked_at DESC
               LIMIT ?""",
            (product_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_latest_price(product_id: int) -> Optional[dict]:
    """Return the most recent price check row, or None."""
    with _conn() as con:
        row = con.execute(
            """SELECT * FROM price_checks
               WHERE product_id = ?
               ORDER BY id DESC
               LIMIT 1""",
            (product_id,),
        ).fetchone()
    return _row_to_dict(row)


# ── Alerts ─────────────────────────────────────────────────────────────────────

def add_alert(
    product_id: int,
    alert_type: str,
    old_price: Optional[float],
    new_price: Optional[float],
    drop_pct: Optional[float],
    message: str,
    sent_via: str,
) -> int:
    """Record a triggered alert; return its id."""
    with _conn() as con:
        cur = con.execute(
            """INSERT INTO alerts
               (product_id, alert_type, old_price, new_price, drop_percentage, message, sent_via)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (product_id, alert_type, old_price, new_price, drop_pct, message, sent_via),
        )
        return cur.lastrowid


def get_alerts(product_id: Optional[int] = None, limit: int = 20) -> list[dict]:
    """Return recent alerts, optionally filtered to a specific product."""
    if product_id is not None:
        query = "SELECT * FROM alerts WHERE product_id = ? ORDER BY created_at DESC LIMIT ?"
        params: tuple = (product_id, limit)
    else:
        query = "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?"
        params = (limit,)
    with _conn() as con:
        rows = con.execute(query, params).fetchall()
    return [dict(r) for r in rows]


# ── Exports ────────────────────────────────────────────────────────────────────

def _safe_export_path(filename: str) -> Path:
    """Reject path traversal and ensure file lands in EXPORTS_DIR."""
    path = (EXPORTS_DIR / filename).resolve()
    if not str(path).startswith(str(EXPORTS_DIR.resolve())):
        raise ValueError(f"Path traversal rejected: {filename!r}")
    return path


def export_history_json(product_id: int, filename: str) -> Path:
    """Export price history for a product to a JSON file in data/exports/."""
    path = _safe_export_path(filename)
    history = get_price_history(product_id, limit=10_000)
    path.write_text(json.dumps(history, indent=2, default=str), encoding="utf-8")
    logger.info("exported %d rows to %s", len(history), path)
    return path


def export_history_csv(product_id: int, filename: str) -> Path:
    """Export price history for a product to a CSV file in data/exports/."""
    path = _safe_export_path(filename)
    history = get_price_history(product_id, limit=10_000)
    if not history:
        path.write_text("", encoding="utf-8")
        return path
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)
    logger.info("exported %d rows to %s", len(history), path)
    return path
