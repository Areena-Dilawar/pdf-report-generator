import sqlite3
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright


DB_NAME = "report.db"
REPORTS_DIR = Path("reports")


def get_report_data():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    total_orders = conn.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    total_revenue = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM orders"
    ).fetchone()[0]

    top_products = conn.execute(
        """
        SELECT
            product,
            ROUND(SUM(amount), 2) AS revenue
        FROM orders
        GROUP BY product
        ORDER BY revenue DESC
        LIMIT 5
        """
    ).fetchall()

    orders_per_day = conn.execute(
        """
        SELECT
            created_at,
            COUNT(*) AS orders
        FROM orders
        WHERE created_at >= date('now', '-6 days')
        GROUP BY created_at
        ORDER BY created_at
        """
    ).fetchall()

    all_orders = conn.execute(
        """
        SELECT
            id,
            customer,
            product,
            amount,
            created_at
        FROM orders
        ORDER BY created_at DESC, id DESC
        """
    ).fetchall()

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_products": [dict(row) for row in top_products],
        "orders_per_day": [dict(row) for row in orders_per_day],
        "all_orders": [dict(row) for row in all_orders],
    }


def build_html(data):
    report_date = date.today().strftime("%B %d, %Y")

    # -------------------------
    # Top products
    # -------------------------
    top_product_rows = ""

    for index, product in enumerate(data["top_products"], start=1):
        top_product_rows += f"""
        <tr>
            <td class="rank">{index}</td>
            <td class="product-name">{product["product"]}</td>
            <td class="money">
                ${product["revenue"]:,.2f}
            </td>
        </tr>
        """

    # -------------------------
    # Orders per day
    # -------------------------
    daily = data["orders_per_day"]

    max_orders = max(
        [item["orders"] for item in daily],
        default=1
    )

    daily_rows = ""

    for item in daily:
        percentage = (item["orders"] / max_orders) * 100

        daily_rows += f"""
        <div class="day-row">
            <div class="day-label">
                {item["created_at"]}
            </div>

            <div class="bar-container">
                <div
                    class="bar"
                    style="width: {percentage:.2f}%"
                ></div>
            </div>

            <div class="day-value">
                {item["orders"]}
            </div>
        </div>
        """

    # -------------------------
    # All orders
    # -------------------------
    order_rows = ""

    for order in data["all_orders"]:
        order_rows += f"""
        <tr>
            <td>#{order["id"]}</td>
            <td>{order["customer"]}</td>
            <td>{order["product"]}</td>
            <td class="money">
                ${order["amount"]:,.2f}
            </td>
            <td>{order["created_at"]}</td>
        </tr>
        """

    # -------------------------
    # HTML
    # -------------------------
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <style>

        @page {{
            size: A4;
            margin: 18mm 15mm 18mm 15mm;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            color: #1f2937;
            background: #ffffff;
            font-size: 12px;
        }}

        /* -------------------------
           Header
        ------------------------- */

        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding-bottom: 18px;
            border-bottom: 2px solid #111827;
            margin-bottom: 22px;
        }}

        .brand {{
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #6b7280;
            margin-bottom: 7px;
        }}

        .title {{
            font-size: 28px;
            font-weight: 700;
            color: #111827;
            margin: 0;
        }}

        .subtitle {{
            margin-top: 7px;
            color: #6b7280;
            font-size: 11px;
        }}

        .report-date {{
            text-align: right;
            color: #6b7280;
            font-size: 10px;
        }}

        .report-date strong {{
            display: block;
            color: #111827;
            font-size: 12px;
            margin-top: 4px;
        }}

        /* -------------------------
           Summary cards
        ------------------------- */

        .summary {{
            display: flex;
            gap: 14px;
            margin-bottom: 25px;
        }}

        .card {{
            flex: 1;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 17px;
            background: #f9fafb;
        }}

        .card-label {{
            font-size: 10px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: bold;
        }}

        .card-value {{
            margin-top: 8px;
            font-size: 25px;
            font-weight: 700;
            color: #111827;
        }}

        /* -------------------------
           Section
        ------------------------- */

        .section {{
            margin-top: 25px;
            margin-bottom: 20px;
        }}

        .section-title {{
            font-size: 17px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 5px;
        }}

        .section-description {{
            color: #6b7280;
            font-size: 10px;
            margin-bottom: 13px;
        }}

        /* -------------------------
           Two-column layout
        ------------------------- */

        .two-column {{
            display: flex;
            gap: 18px;
        }}

        .column {{
            flex: 1;
        }}

        /* -------------------------
           Tables
        ------------------------- */

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 10px;
        }}

        thead {{
            display: table-header-group;
        }}

        tr {{
            break-inside: avoid;
            page-break-inside: avoid;
        }}

        th {{
            text-align: left;
            padding: 9px 8px;
            background: #111827;
            color: white;
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 8px;
            border-bottom: 1px solid #e5e7eb;
            color: #374151;
        }}

        tbody tr:nth-child(even) {{
            background: #f9fafb;
        }}

        .rank {{
            width: 30px;
            color: #9ca3af;
            font-weight: bold;
        }}

        .product-name {{
            font-weight: 600;
            color: #111827;
        }}

        .money {{
            text-align: right;
            font-weight: 600;
            color: #111827;
        }}

        /* -------------------------
           Daily chart
        ------------------------- */

        .daily-chart {{
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 15px;
        }}

        .day-row {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }}

        .day-row:last-child {{
            margin-bottom: 0;
        }}

        .day-label {{
            width: 67px;
            font-size: 9px;
            color: #6b7280;
        }}

        .bar-container {{
            flex: 1;
            height: 13px;
            background: #f3f4f6;
            border-radius: 7px;
            overflow: hidden;
        }}

        .bar {{
            height: 100%;
            background: #111827;
            border-radius: 7px;
        }}

        .day-value {{
            width: 22px;
            text-align: right;
            font-weight: bold;
            font-size: 10px;
        }}

        /* -------------------------
           Orders table
        ------------------------- */

        .orders-table {{
            margin-top: 10px;
        }}

        .orders-table th:first-child {{
            width: 45px;
        }}

        .orders-table th:nth-child(4) {{
            text-align: right;
        }}

        /* -------------------------
           Footer
        ------------------------- */

        .footer {{
            margin-top: 25px;
            padding-top: 10px;
            border-top: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            color: #9ca3af;
            font-size: 9px;
        }}

    </style>
</head>

<body>

    <!-- HEADER -->

    <div class="header">

        <div>
            <div class="brand">
                Sales Analytics
            </div>

            <h1 class="title">
                Workshop Report
            </h1>

            <div class="subtitle">
                Orders, revenue and product performance overview
            </div>
        </div>

        <div class="report-date">
            Generated
            <strong>{report_date}</strong>
        </div>

    </div>


    <!-- SUMMARY -->

    <div class="summary">

        <div class="card">
            <div class="card-label">
                Total Orders
            </div>

            <div class="card-value">
                {data["total_orders"]:,}
            </div>
        </div>


        <div class="card">
            <div class="card-label">
                Total Revenue
            </div>

            <div class="card-value">
                ${data["total_revenue"]:,.2f}
            </div>
        </div>

    </div>


    <!-- PERFORMANCE -->

    <div class="section">

        <div class="section-title">
            Product Performance
        </div>

        <div class="section-description">
            Top five products ranked by total revenue.
        </div>


        <div class="two-column">

            <!-- TOP PRODUCTS -->

            <div class="column">

                <table>

                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Product</th>
                            <th style="text-align:right;">
                                Revenue
                            </th>
                        </tr>
                    </thead>

                    <tbody>
                        {top_product_rows}
                    </tbody>

                </table>

            </div>


            <!-- DAILY ORDERS -->

            <div class="column">

                <div class="daily-chart">

                    <div style="
                        font-weight:600;
                        margin-bottom:13px;
                        color:#111827;
                        font-size:11px;
                    ">
                        Orders — Last 7 Days
                    </div>

                    {daily_rows}

                </div>

            </div>

        </div>

    </div>


    <!-- ALL ORDERS -->

    <div class="section">

        <div class="section-title">
            Order Details
        </div>

        <div class="section-description">
            Complete list of orders included in this report.
        </div>


        <table class="orders-table">

            <thead>

                <tr>
                    <th>ID</th>
                    <th>Customer</th>
                    <th>Product</th>
                    <th>Amount</th>
                    <th>Date</th>
                </tr>

            </thead>

            <tbody>
                {order_rows}
            </tbody>

        </table>

    </div>


    <!-- FOOTER -->

    <div class="footer">

        <div>
            Generated automatically from report.db
        </div>

        <div>
            Workshop Analytics Report
        </div>

    </div>

</body>
</html>
"""


def generate_pdf(output_path=None):
    data = get_report_data()

    if output_path is None:
        REPORTS_DIR.mkdir(exist_ok=True)
        output_path = REPORTS_DIR / "test.pdf"

    output_path = Path(output_path)

    html = build_html(data)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()

        page = browser.new_page(
            viewport={
                "width": 1280,
                "height": 900,
            }
        )

        page.set_content(html, wait_until="networkidle")

        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
        )

        browser.close()


if __name__ == "__main__":
    generate_pdf()
    print("PDF generated successfully.")