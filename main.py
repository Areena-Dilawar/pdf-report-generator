import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from pdf_generator import generate_pdf


app = FastAPI()

DB_NAME = "report.db"
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


def initialize_reports_table():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
    """)

    conn.commit()
    conn.close()


initialize_reports_table()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/reports", status_code=201)
async def create_report():
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute("""
        INSERT INTO reports (path, created_at)
        VALUES (?, ?)
    """, ("", datetime.now().isoformat()))

    report_id = cursor.lastrowid

    file_path = REPORTS_DIR / f"{report_id}.pdf"

    conn.execute("""
        UPDATE reports
        SET path = ?
        WHERE id = ?
    """, (str(file_path), report_id))

    conn.commit()
    conn.close()

    await asyncio.to_thread(generate_pdf, file_path)

    return {
        "id": report_id,
        "file": f"/reports/{report_id}/file"
    }


@app.get("/reports/{report_id}")
async def get_report(report_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    report = conn.execute("""
        SELECT id, path, created_at
        FROM reports
        WHERE id = ?
    """, (report_id,)).fetchone()

    conn.close()

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    return dict(report)


@app.get("/reports/{report_id}/file")
async def get_report_file(report_id: int):
    conn = sqlite3.connect(DB_NAME)

    report = conn.execute("""
        SELECT path
        FROM reports
        WHERE id = ?
    """, (report_id,)).fetchone()

    conn.close()

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = Path(report[0])

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=file_path.name,
    )