import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

# Initialize the FastMCP server instance
mcp = FastMCP("Math_Database_Tools")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "inventory.db"
AUDIT_LOG_PATH = BASE_DIR / "logs" / "audit.log"

SEED_PRODUCTS = [
    (1, "Steel Roll", 120),
    (2, "Copper Wire", 450),
    (3, "Hydraulic Pump", 35),
    (4, "Ball Bearing Set", 800),
    (5, "Control Cabinet", 18),
]


def ensure_inventory_db() -> None:
    """Creates the SQLite inventory database and seed rows if they do not exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO products (id, name, quantity) VALUES (?, ?, ?)",
                SEED_PRODUCTS,
            )
        conn.commit()


def ensure_audit_log() -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not AUDIT_LOG_PATH.exists():
        AUDIT_LOG_PATH.write_text("", encoding="utf-8")


# 1. SQL DATABASE LOOKUP TOOL
@mcp.tool()
def lookup_inventory(identifier: str) -> str:
    """Looks up product inventory in the local SQLite database.

    Args:
        identifier: A product id (e.g. '3') or a product name (e.g. 'Hydraulic Pump').
    """
    ensure_inventory_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if identifier.strip().isdigit():
            rows = conn.execute(
                "SELECT id, name, quantity FROM products WHERE id = ?",
                (int(identifier),),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, quantity FROM products WHERE name LIKE ?",
                (f"%{identifier.strip()}%",),
            ).fetchall()

    products = [dict(row) for row in rows]
    if not products:
        return json.dumps({"found": False, "identifier": identifier, "products": []})
    return json.dumps({"found": True, "identifier": identifier, "products": products})


# 2. FORMULA ENGINE TOOL (TIERED VOLUME DISCOUNTS)
@mcp.tool()
def compute_tiered_discount(order_volume: int, unit_price: float) -> str:
    """Computes a complex tiered discount based on order volume.

    Discount brackets:
      1-9 units     -> 0%
      10-49 units   -> 5%
      50-99 units   -> 12%
      100-249 units -> 18%
      250+ units    -> 25%

    Args:
        order_volume: Number of units in the order.
        unit_price: Price per unit before discount.
    """
    if order_volume < 0 or unit_price < 0:
        return json.dumps({"error": "order_volume and unit_price must be non-negative"})

    if order_volume >= 250:
        rate = 0.25
        bracket = "250+"
    elif order_volume >= 100:
        rate = 0.18
        bracket = "100-249"
    elif order_volume >= 50:
        rate = 0.12
        bracket = "50-99"
    elif order_volume >= 10:
        rate = 0.05
        bracket = "10-49"
    else:
        rate = 0.0
        bracket = "1-9"

    subtotal = order_volume * unit_price
    discount_amount = round(subtotal * rate, 2)
    total = round(subtotal - discount_amount, 2)

    return json.dumps(
        {
            "order_volume": order_volume,
            "unit_price": unit_price,
            "bracket": bracket,
            "discount_rate": rate,
            "subtotal": round(subtotal, 2),
            "discount_amount": discount_amount,
            "total": total,
        }
    )


# 3. LOG AUDIT TOOL (APPENDS TO A LOCAL FILE RESOURCE)
@mcp.tool()
def append_audit_event(event: str) -> str:
    """Appends a timestamped event to the local audit log file resource.

    Args:
        event: Human-readable description of the action that should be audited.
    """
    ensure_audit_log()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{timestamp} | {event.strip()}\n"
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line)
    return json.dumps(
        {
            "status": "logged",
            "path": str(AUDIT_LOG_PATH),
            "entry": line.strip(),
        }
    )


# READ-ONLY RESOURCE FOR THE AUDIT FILE
@mcp.resource("file://audit/events")
def read_audit_log() -> str:
    """Provides the read-only contents of the local audit log file."""
    ensure_audit_log()
    content = AUDIT_LOG_PATH.read_text(encoding="utf-8").strip()
    return content if content else "(audit log is empty)"


if __name__ == "__main__":
    ensure_inventory_db()
    ensure_audit_log()
    mcp.run(transport="http", host="0.0.0.0", port=8000)
