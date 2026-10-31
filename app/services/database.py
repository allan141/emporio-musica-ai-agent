"""Load the six provided CSVs into a local read-only SQLite-backed data store.

This intentionally imports the raw data without fabricating records or dates.
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
DATABASE = ROOT / "data" / "store.db"

TABLES = {
    "categories": {"category_id": "INTEGER", "name": "TEXT", "description": "TEXT"},
    "customers": {"customer_id": "INTEGER", "name": "TEXT", "phone": "TEXT", "email": "TEXT", "city": "TEXT"},
    "products": {"product_id": "INTEGER", "price_brl": "REAL", "name": "TEXT", "category_id": "INTEGER", "description": "TEXT", "stock_quantity": "INTEGER", "status": "TEXT", "specs": "TEXT", "created_at": "TEXT"},
    "orders": {"order_id": "INTEGER", "customer_id": "INTEGER", "order_date": "TEXT", "status": "TEXT", "total_brl": "REAL", "payment_method": "TEXT", "tracking_code": "TEXT", "estimated_delivery": "TEXT", "notes": "TEXT"},
    "order_items": {"order_id": "INTEGER", "quantity": "INTEGER", "product_id": "INTEGER"},
    "promotions": {"promotion_id": "INTEGER", "product_id": "INTEGER", "discount_percent": "REAL", "description": "TEXT", "is_active": "INTEGER"},
}


def initialize_database(path: Path = DATABASE) -> Path:
    """Create a SQLite snapshot from the challenge CSV files when absent."""
    path = Path(path)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        for table, columns in TABLES.items():
            csv_path = RAW / f"{table}.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing source file: {csv_path}")
            column_definitions = ", ".join(f'"{col}" {kind}' for col, kind in columns.items())
            connection.execute(f'CREATE TABLE "{table}" ({column_definitions})')
            with csv_path.open(encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))
            if rows:
                placeholders = ", ".join("?" for _ in columns)
                quoted_columns = ", ".join(f'"{col}"' for col in columns)
                connection.executemany(
                    f'INSERT INTO "{table}" ({quoted_columns}) VALUES ({placeholders})',
                    [[row[col] if row[col] != "" else None for col in columns] for row in rows],
                )
    return path


def connect(path: Path = DATABASE) -> sqlite3.Connection:
    """Open a connection with dict-like rows; database is a demo snapshot."""
    db_path = initialize_database(path)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection
