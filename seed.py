import sqlite3
import random
from datetime import date, timedelta

DB_NAME = "report.db"

products = [
    "Laptop",
    "Keyboard",
    "Mouse",
    "Monitor",
    "Headphones",
    "Webcam",
]

customers = [
    "Ali",
    "Ahmed",
    "Sara",
    "Ayesha",
    "Usman",
    "Fatima",
    "Hassan",
    "Zainab",
]


def seed_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at DATE NOT NULL
        )
    """)

    # Clean previous seed data
    cursor.execute("DELETE FROM orders")

    today = date.today()

    for _ in range(200):
        customer = random.choice(customers)
        product = random.choice(products)
        amount = round(random.uniform(5, 200), 2)
        created_at = today - timedelta(days=random.randint(0, 29))

        cursor.execute("""
            INSERT INTO orders (customer, product, amount, created_at)
            VALUES (?, ?, ?, ?)
        """, (customer, product, amount, created_at))

    conn.commit()

    count = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    conn.close()

    print(f"Seeded {count} orders into {DB_NAME}")


if __name__ == "__main__":
    seed_database()