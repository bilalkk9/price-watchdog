"""Tests for core/database.py — FR7 history management."""
import sys, os, pytest, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# Redirect database to a temp file for all tests
@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    import config
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config, "DATABASE_PATH", db_path)
    monkeypatch.setattr(config, "EXPORTS_DIR", tmp_path)
    import core.database as db
    monkeypatch.setattr(db, "DATABASE_PATH", db_path)
    monkeypatch.setattr(db, "EXPORTS_DIR", tmp_path)
    db.init_db()
    yield db


# ── Products ───────────────────────────────────────────────────────────────────

def test_add_and_get_product(tmp_db):
    pid = tmp_db.add_product("https://example.com/p1", 50000.0)
    product = tmp_db.get_product(pid)
    assert product["url"] == "https://example.com/p1"
    assert product["target_price"] == 50000.0
    assert product["is_active"] == 1


def test_duplicate_url_raises(tmp_db):
    tmp_db.add_product("https://example.com/dup", 1000.0)
    with pytest.raises(Exception):   # sqlite3.IntegrityError
        tmp_db.add_product("https://example.com/dup", 2000.0)


def test_invalid_url_raises(tmp_db):
    with pytest.raises(ValueError):
        tmp_db.add_product("not-a-url", 1000.0)


def test_negative_price_raises(tmp_db):
    with pytest.raises(ValueError):
        tmp_db.add_product("https://example.com/p", -1.0)


def test_get_product_by_url(tmp_db):
    tmp_db.add_product("https://example.com/p2", 30000.0)
    product = tmp_db.get_product_by_url("https://example.com/p2")
    assert product is not None
    assert product["target_price"] == 30000.0


def test_get_all_products_active_only(tmp_db):
    pid1 = tmp_db.add_product("https://example.com/a", 1000.0)
    pid2 = tmp_db.add_product("https://example.com/b", 2000.0)
    tmp_db.deactivate_product(pid2)
    active = tmp_db.get_all_products(active_only=True)
    ids = [p["id"] for p in active]
    assert pid1 in ids
    assert pid2 not in ids


def test_update_product_name(tmp_db):
    pid = tmp_db.add_product("https://example.com/upd", 5000.0)
    tmp_db.update_product(pid, name="Test Product")
    assert tmp_db.get_product(pid)["name"] == "Test Product"


def test_update_unknown_field_raises(tmp_db):
    pid = tmp_db.add_product("https://example.com/bad", 1000.0)
    with pytest.raises(KeyError):
        tmp_db.update_product(pid, nonexistent_field="x")


def test_get_nonexistent_product_returns_none(tmp_db):
    assert tmp_db.get_product(99999) is None


# ── Price checks ───────────────────────────────────────────────────────────────

def test_add_and_get_price_check(tmp_db):
    pid = tmp_db.add_product("https://example.com/pc", 50000.0)
    cid = tmp_db.add_price_check(pid, 49000.0, "PKR", "256GB", "In Stock", "reasoning", "{}")
    assert cid > 0
    history = tmp_db.get_price_history(pid)
    assert len(history) == 1
    assert history[0]["price"] == 49000.0
    assert history[0]["variant"] == "256GB"


def test_get_latest_price(tmp_db):
    pid = tmp_db.add_product("https://example.com/lp", 50000.0)
    tmp_db.add_price_check(pid, 55000.0, "PKR", None, "In Stock", None, None)
    tmp_db.add_price_check(pid, 48000.0, "PKR", None, "In Stock", None, None)
    latest = tmp_db.get_latest_price(pid)
    assert latest["price"] == 48000.0


def test_get_latest_price_no_history(tmp_db):
    pid = tmp_db.add_product("https://example.com/nohist", 1000.0)
    assert tmp_db.get_latest_price(pid) is None


def test_price_history_limit(tmp_db):
    pid = tmp_db.add_product("https://example.com/lim", 1000.0)
    for i in range(10):
        tmp_db.add_price_check(pid, float(i * 1000), "PKR", None, "In Stock", None, None)
    assert len(tmp_db.get_price_history(pid, limit=3)) == 3


# ── Alerts ─────────────────────────────────────────────────────────────────────

def test_add_and_get_alert(tmp_db):
    pid = tmp_db.add_product("https://example.com/al", 50000.0)
    tmp_db.add_alert(pid, "price_drop", 55000.0, 49000.0, 10.9, "Price dropped!", "console")
    alerts = tmp_db.get_alerts(pid)
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "price_drop"
    assert alerts[0]["drop_percentage"] == 10.9


def test_get_all_alerts(tmp_db):
    pid1 = tmp_db.add_product("https://example.com/al1", 1000.0)
    pid2 = tmp_db.add_product("https://example.com/al2", 2000.0)
    tmp_db.add_alert(pid1, "price_drop", 2000.0, 1800.0, 10.0, "drop", "console")
    tmp_db.add_alert(pid2, "back_in_stock", None, None, None, "back", "console")
    assert len(tmp_db.get_alerts()) == 2


# ── Exports ────────────────────────────────────────────────────────────────────

def test_export_json(tmp_db, tmp_path):
    pid = tmp_db.add_product("https://example.com/ex", 1000.0)
    tmp_db.add_price_check(pid, 900.0, "PKR", None, "In Stock", None, None)
    out = tmp_db.export_history_json(pid, "history.json")
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert data[0]["price"] == 900.0


def test_export_csv(tmp_db, tmp_path):
    pid = tmp_db.add_product("https://example.com/csv", 1000.0)
    tmp_db.add_price_check(pid, 850.0, "PKR", None, "In Stock", None, None)
    out = tmp_db.export_history_csv(pid, "history.csv")
    lines = out.read_text().splitlines()
    assert "price" in lines[0]   # header
    assert "850.0" in lines[1]


def test_export_path_traversal_rejected(tmp_db):
    pid = tmp_db.add_product("https://example.com/trav", 1000.0)
    with pytest.raises(ValueError):
        tmp_db.export_history_json(pid, "../../etc/passwd")
