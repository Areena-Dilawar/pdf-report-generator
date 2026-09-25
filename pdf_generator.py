import asyncio
from datetime import date
from pathlib import Path

from playwright.async_api import async_playwright

from report_queries import get_report_data


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


def build_html(data):
    top_products_rows = ""

    for product in data["top_products"]:
        top_products_rows += f"""
        <tr>
            <td>{product["product"]}</td>
            <td>{product["revenue"]:.2f}</td>
        </tr>
        """

    orders_per_day_rows = ""

    for day in data["orders_per_day"]:
        orders_per_day_rows += f"""
        <tr>
            <td>{day["created_at"]}</td>
            <td>{day["orders"]}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Shop Report</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                color: #222;
            }}

            h1 {{
                margin-bottom: 5px;
            }}

            .date {{
                color: #666;
                margin-bottom: 30px;
            }}

            .totals {{
                display: flex;
                gap: 30px;
                margin-bottom: 30px;
            }}

            .card {{
                border: 1px solid #ddd;
                padding: 20px;
                width: 200px;
            }}

            .card h2 {{
                margin: 0 0 10px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                margin-bottom: 30px;
            }}

            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}

            th {{
                background: #f2f2f2;
            }}

            tr {{
                break-inside: avoid;
            }}

            thead {{
                display: table-header-group;
            }}
        </style>
    </head>

    <body>
        <h1>Shop Sales Report</h1>
        <div class="date">Generated on {date.today()}</div>

        <div class="totals">
            <div class="card">
                <h2>{data["total_orders"]}</h2>
                <div>Total Orders</div>
            </div>

            <div class="card">
                <h2>{data["total_revenue"]:.2f}</h2>
                <div>Total Revenue</div>
            </div>
        </div>

        <h2>Top 5 Products by Revenue</h2>

        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Revenue</th>
                </tr>
            </thead>

            <tbody>
                {top_products_rows}
            </tbody>
        </table>

        <h2>Orders Per Day — Last 7 Days</h2>

        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Orders</th>
                </tr>
            </thead>

            <tbody>
                {orders_per_day_rows}
            </tbody>
        </table>

        <h2>All Orders</h2>

        <table>
            <thead>
                <tr>
                    <th>Order ID</th>
                    <th>Customer</th>
                    <th>Product</th>
                    <th>Amount</th>
                    <th>Date</th>
                </tr>
            </thead>

            <tbody>
                {"".join(
                    f'''
                    <tr>
                        <td>{order["id"]}</td>
                        <td>{order["customer"]}</td>
                        <td>{order["product"]}</td>
                        <td>{order["amount"]:.2f}</td>
                        <td>{order["created_at"]}</td>
                    </tr>
                    '''
                    for order in get_all_orders()
                )}
            </tbody>
        </table>

    </body>
    </html>
    """


def get_all_orders():
    import sqlite3

    conn = sqlite3.connect("report.db")
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, customer, product, amount, created_at
        FROM orders
        ORDER BY created_at DESC, id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


async def generate_pdf():
    data = get_report_data()
    html = build_html(data)

    output_path = REPORTS_DIR / "test.pdf"

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()

        page = await browser.new_page()
        await page.set_content(html)

        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
        )

        await browser.close()

    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    asyncio.run(generate_pdf())