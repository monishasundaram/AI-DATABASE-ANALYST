"""
database/loader.py
Handles connecting to SQLite databases, saving uploaded files, and
auto-generating a realistic sample database when none is supplied.
"""

from __future__ import annotations

import os
import random
import sqlite3
from datetime import datetime, timedelta

# Directory where the bundled sample database lives.
SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_database")
SAMPLE_DB = os.path.join(SAMPLE_DIR, "sample.db")


class DatabaseLoader:
    """Load and validate SQLite databases from disk or an upload."""

    def __init__(self, path: str | None = None):
        self.path = path

    # ------------------------------------------------------------------ #
    # Connections
    # ------------------------------------------------------------------ #
    def connect(self) -> sqlite3.Connection:
        """Return a read-only-ish connection to the active database."""
        if not self.path or not os.path.exists(self.path):
            raise FileNotFoundError("No valid SQLite database is loaded.")
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def is_valid_sqlite(self) -> bool:
        """Cheap check that the file is a real SQLite database."""
        try:
            with open(self.path, "rb") as fh:
                header = fh.read(16)
            return header.startswith(b"SQLite format 3")
        except OSError:
            return False

    # ------------------------------------------------------------------ #
    # Uploads
    # ------------------------------------------------------------------ #
    @staticmethod
    def save_upload(uploaded_file, dest_dir: str) -> str:
        """Persist a Streamlit UploadedFile to disk and return its path."""
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, uploaded_file.name)
        with open(dest, "wb") as out:
            out.write(uploaded_file.getbuffer())
        return dest


# --------------------------------------------------------------------------- #
# Sample database generation
# --------------------------------------------------------------------------- #

def _create_schema(cur: sqlite3.Cursor) -> None:
    """Create the six related tables with primary and foreign keys."""
    cur.executescript(
        """
        CREATE TABLE Suppliers (
            supplier_id   INTEGER PRIMARY KEY,
            supplier_name TEXT NOT NULL,
            country       TEXT,
            contact_email TEXT
        );

        CREATE TABLE Products (
            product_id   INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category     TEXT,
            unit_price   REAL NOT NULL,
            supplier_id  INTEGER,
            FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id)
        );

        CREATE TABLE Customers (
            customer_id INTEGER PRIMARY KEY,
            full_name   TEXT NOT NULL,
            city        TEXT,
            country     TEXT,
            signup_date TEXT
        );

        CREATE TABLE Employees (
            employee_id INTEGER PRIMARY KEY,
            full_name   TEXT NOT NULL,
            department  TEXT,
            hire_date   TEXT,
            salary      REAL
        );

        CREATE TABLE Orders (
            order_id    INTEGER PRIMARY KEY,
            customer_id INTEGER,
            employee_id INTEGER,
            product_id  INTEGER,
            quantity    INTEGER NOT NULL,
            order_date  TEXT,
            FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
            FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
            FOREIGN KEY (product_id)  REFERENCES Products(product_id)
        );

        CREATE TABLE Payments (
            payment_id INTEGER PRIMARY KEY,
            order_id   INTEGER,
            amount     REAL NOT NULL,
            method     TEXT,
            paid_date  TEXT,
            FOREIGN KEY (order_id) REFERENCES Orders(order_id)
        );
        """
    )


def _seed_data(cur: sqlite3.Cursor) -> None:
    """Insert deterministic, realistic-looking sample data."""
    random.seed(42)

    countries = ["USA", "India", "Germany", "UK", "Canada", "Australia", "Japan"]
    cities = ["New York", "Mumbai", "Berlin", "London", "Toronto", "Sydney", "Tokyo"]
    categories = ["Electronics", "Apparel", "Home", "Sports", "Beauty", "Grocery"]
    methods = ["Credit Card", "UPI", "PayPal", "Bank Transfer", "Cash"]
    departments = ["Sales", "Support", "Marketing", "Operations", "Finance"]

    # Suppliers
    suppliers = [
        (i, f"Supplier {chr(64 + i)} Co.", random.choice(countries),
         f"contact{i}@supplier.com")
        for i in range(1, 11)
    ]
    cur.executemany("INSERT INTO Suppliers VALUES (?,?,?,?)", suppliers)

    # Products
    products = []
    for pid in range(1, 41):
        products.append((
            pid,
            f"{random.choice(categories)} Item {pid}",
            random.choice(categories),
            round(random.uniform(5, 900), 2),
            random.randint(1, 10),
        ))
    cur.executemany("INSERT INTO Products VALUES (?,?,?,?,?)", products)

    # Customers
    customers = []
    base = datetime(2023, 1, 1)
    for cid in range(1, 61):
        idx = random.randint(0, len(countries) - 1)
        customers.append((
            cid,
            f"Customer {cid:02d}",
            cities[idx],
            countries[idx],
            (base + timedelta(days=random.randint(0, 700))).strftime("%Y-%m-%d"),
        ))
    cur.executemany("INSERT INTO Customers VALUES (?,?,?,?,?)", customers)

    # Employees
    employees = []
    for eid in range(1, 16):
        employees.append((
            eid,
            f"Employee {eid:02d}",
            random.choice(departments),
            (base + timedelta(days=random.randint(0, 900))).strftime("%Y-%m-%d"),
            round(random.uniform(35000, 120000), 2),
        ))
    cur.executemany("INSERT INTO Employees VALUES (?,?,?,?,?)", employees)

    # Orders
    orders = []
    for oid in range(1, 301):
        orders.append((
            oid,
            random.randint(1, 60),
            random.randint(1, 15),
            random.randint(1, 40),
            random.randint(1, 8),
            (base + timedelta(days=random.randint(0, 900))).strftime("%Y-%m-%d"),
        ))
    cur.executemany("INSERT INTO Orders VALUES (?,?,?,?,?,?)", orders)

    # Payments (one per order, using the product price * quantity)
    price_map = {p[0]: p[3] for p in products}
    qty_map = {o[0]: (o[3], o[4]) for o in orders}  # order_id -> (product_id, qty)
    payments = []
    for pid, oid in enumerate(range(1, 301), start=1):
        prod_id, qty = qty_map[oid]
        amount = round(price_map[prod_id] * qty, 2)
        payments.append((
            pid,
            oid,
            amount,
            random.choice(methods),
            (base + timedelta(days=random.randint(0, 900))).strftime("%Y-%m-%d"),
        ))
    cur.executemany("INSERT INTO Payments VALUES (?,?,?,?,?)", payments)


def generate_sample_db(path: str = SAMPLE_DB, overwrite: bool = False) -> str:
    """Create the bundled sample database and return its path.

    If the database already exists and ``overwrite`` is False, the existing
    file is reused so repeated app starts are fast.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path) and not overwrite:
        return path
    if os.path.exists(path):
        os.remove(path)

    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        _create_schema(cur)
        _seed_data(cur)
        conn.commit()
    finally:
        conn.close()
    return path
