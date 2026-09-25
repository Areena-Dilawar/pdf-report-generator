import sqlite3
import json

DB_NAME = "report.db"


def get_report_data():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    total_orders = cursor.execute("""
        SELECT COUNT(*) AS total_orders
        FROM orders
    """).fetchone()["total_orders"]

    total_revenue = cursor.execute("""
        SELECT SUM(amount) AS total_revenue
        FROM orders
    """).fetchone()["total_revenue"]

    top_products = cursor.execute("""
        SELECT
            product,
            SUM(amount) AS revenue
        FROM orders
        GROUP BY product
        ORDER BY revenue DESC
        LIMIT 5
    """).fetchall()

    orders_per_day = cursor.execute("""
        SELECT
            created_at,
            COUNT(*) AS orders
        FROM orders
        WHERE created_at >= date('now', '-6 days')
        GROUP BY created_at
        ORDER BY created_at
    """).fetchall()

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue or 0, 2),
        "top_products": [dict(row) for row in top_products],
        "orders_per_day": [dict(row) for row in orders_per_day],
    }


if __name__ == "__main__":
    data = get_report_data()
    print(json.dumps(data, indent=2))