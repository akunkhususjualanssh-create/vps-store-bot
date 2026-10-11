import sqlite3
import os
import time
from config import DB_PATH

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price INTEGER NOT NULL,
        created_at REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        username TEXT,
        first_name TEXT,
        product_id INTEGER NOT NULL,
        product_name TEXT,
        price INTEGER,
        status TEXT DEFAULT 'pending_payment',
        payment_proof TEXT,
        vps_data TEXT,
        created_at REAL DEFAULT 0,
        confirmed_at REAL
    );
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_at REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    db.commit()
    db.close()

def add_user(user_id, username, first_name):
    db = get_db()
    db.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, joined_at) VALUES (?, ?, ?, ?)",
               (user_id, username, first_name, time.time()))
    db.execute("UPDATE users SET username=?, first_name=? WHERE user_id=?",
               (username, first_name, user_id))
    db.commit()
    db.close()

def get_all_users():
    db = get_db()
    users = db.execute("SELECT user_id FROM users").fetchall()
    db.close()
    return [u['user_id'] for u in users]

def add_product(name, description, price):
    db = get_db()
    db.execute("INSERT INTO products (name, description, price, created_at) VALUES (?, ?, ?, ?)",
               (name, description, price, time.time()))
    db.commit()
    db.close()

def get_products():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    db.close()
    return products

def get_product(product_id):
    db = get_db()
    p = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    db.close()
    return p

def update_product(product_id, name=None, description=None, price=None):
    db = get_db()
    if name is not None:
        db.execute("UPDATE products SET name=? WHERE id=?", (name, product_id))
    if description is not None:
        db.execute("UPDATE products SET description=? WHERE id=?", (description, product_id))
    if price is not None:
        db.execute("UPDATE products SET price=? WHERE id=?", (price, product_id))
    db.commit()
    db.close()

def delete_product(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (product_id,))
    db.commit()
    db.close()

def create_order(user_id, username, first_name, product_id, product_name, price):
    order_id = f"VPS-{int(time.time())}-{user_id % 10000}"
    db = get_db()
    db.execute("""INSERT INTO orders (order_id, user_id, username, first_name, product_id, product_name, price, status, created_at)
                  VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_payment', ?)""",
               (order_id, user_id, username, first_name, product_id, product_name, price, time.time()))
    db.commit()
    db.close()
    return order_id

def get_order(order_id):
    db = get_db()
    o = db.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()
    db.close()
    return o

def get_user_orders(user_id):
    db = get_db()
    orders = db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
    db.close()
    return orders

def get_pending_orders():
    db = get_db()
    orders = db.execute("SELECT * FROM orders WHERE status IN ('pending_delivery', 'payment_received') ORDER BY created_at DESC").fetchall()
    db.close()
    return orders

def update_order_status(order_id, status):
    db = get_db()
    if status == 'payment_received':
        db.execute("UPDATE orders SET status=?, confirmed_at=? WHERE order_id=?", (status, time.time(), order_id))
    else:
        db.execute("UPDATE orders SET status=? WHERE order_id=?", (status, order_id))
    db.commit()
    db.close()

def save_payment_proof(order_id, file_id):
    db = get_db()
    db.execute("UPDATE orders SET payment_proof=?, status='payment_received' WHERE order_id=?", (file_id, order_id))
    db.execute("UPDATE orders SET confirmed_at=? WHERE order_id=?", (time.time(), order_id))
    db.commit()
    db.close()

def save_vps_data(order_id, vps_data):
    db = get_db()
    db.execute("UPDATE orders SET vps_data=?, status='completed' WHERE order_id=?", (vps_data, order_id))
    db.commit()
    db.close()

def cancel_order(order_id):
    db = get_db()
    db.execute("UPDATE orders SET status='cancelled' WHERE order_id=? AND status IN ('pending_payment','payment_received','pending_delivery')", (order_id,))
    db.commit()
    db.close()
    return db.total_changes > 0

def backup_database():
    """Copy database file for backup"""
    import shutil
    backup_path = DB_PATH.replace(".db", "_backup.db")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path

def restore_database(backup_path):
    """Restore database from backup file"""
    import shutil
    # Verify it's a valid SQLite file
    import sqlite3 as sq
    try:
        conn = sq.connect(backup_path)
        conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        conn.close()
    except:
        return False
    shutil.copy2(backup_path, DB_PATH)
    return True

def get_setting(key):
    db = get_db()
    s = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    db.close()
    return s['value'] if s else None

def set_setting(key, value):
    db = get_db()
    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    db.commit()
    db.close()
