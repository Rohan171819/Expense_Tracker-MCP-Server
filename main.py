import os
import json
import tempfile
import sqlite3
from datetime import datetime
import aiosqlite
from fastmcp import FastMCP

# Use temp directory for safe write permissions
TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

# Start MCP server
mcp = FastMCP(name="ExpenseTracker", host="0.0.0.0", port=8000)


def init_db():
    """Initialize the database synchronously with WAL mode."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_date 
            ON expenses(date)
        """)
        conn.commit()


def validate_date(date_str: str) -> bool:
    """Ensure valid YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# Run database initialization at import
init_db()


# ------------------------------
#        ASYNC TOOLS
# ------------------------------

@mcp.tool()
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Add a new expense entry."""
    if not validate_date(date):
        return {"status": "error", "message": "Invalid date format (YYYY-MM-DD)."}

    if amount <= 0:
        return {"status": "error", "message": "Amount must be positive."}

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
                (date, amount, category, subcategory, note)
            )
            await db.commit()
            return {"status": "success", "id": cur.lastrowid}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    """Return all expenses between two dates."""
    if not validate_date(start_date) or not validate_date(end_date):
        return {"status": "error", "message": "Invalid date format (YYYY-MM-DD)."}

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
        """, (start_date, end_date))

        rows = await cur.fetchall()
        cols = [c[0] for c in cur.description]

        return [dict(zip(cols, r)) for r in rows]


@mcp.tool()
async def summarize(start_date: str, end_date: str, category: str = None):
    """Summarize total expenses grouped by category."""
    if not validate_date(start_date) or not validate_date(end_date):
        return {"status": "error", "message": "Invalid date format."}

    query = """
        SELECT category, SUM(amount) AS total, COUNT(*) AS count
        FROM expenses
        WHERE date BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " GROUP BY category ORDER BY total DESC"

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(query, params)
        rows = await cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]


@mcp.tool()
async def delete_expense(expense_id: int):
    """Delete an expense by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,))
        exists = await cur.fetchone()

        if not exists:
            return {"status": "error", "message": "Expense not found."}

        await db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        await db.commit()
        return {"status": "success"}


# ------------------------------
#        RESOURCE: Categories
# ------------------------------

@mcp.resource("expense:///categories", mime_type="application/json")
def categories():
    """Return categories JSON file, or defaults."""
    default = {
        "categories": [
            "Food & Dining", "Transportation", "Shopping", "Entertainment",
            "Bills & Utilities", "Healthcare", "Travel", "Education",
            "Business", "Other"
        ]
    }
    try:
        if os.path.exists(CATEGORIES_PATH):
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                return f.read()
        return json.dumps(default, indent=2)
    except:
        return json.dumps(default, indent=2)


# ------------------------------
#        START SERVER
# ------------------------------

if __name__ == "__main__":
    mcp.run(transport="http")
