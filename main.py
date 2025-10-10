import os
from fastmcp import FastMCP
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")

# Create a FastMCP server instance with only the 'name' parameter
mcp = FastMCP(name="Expense Tracker",host="0.0.0.0",port=8000)


def init_db():
    """Initialize the database with necessary tables and indexes"""
    with sqlite3.connect(DB_PATH) as conn:
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
        # Add index for date range queries
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_expenses_date 
        ON expenses(date)
        """)
        conn.commit()


def validate_date(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


# Initialize the database
init_db()


@mcp.tool()
def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Add an expense entry to database."""
    # Validate date format
    if not validate_date(date):
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}
    
    # Validate amount
    if amount <= 0:
        return {"status": "error", "message": "Amount must be positive"}
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
                (date, amount, category, subcategory, note)
            )
            conn.commit()
            return {
                "status": "success",
                "message": "Expense added successfully.",
                "id": cur.lastrowid
            }
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


@mcp.tool()
def list_expenses(start_date: str, end_date: str):
    """List expenses from the given date range."""
    # Validate date formats
    if not validate_date(start_date) or not validate_date(end_date):
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                "SELECT id, date, amount, category, subcategory, note FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date ASC, id ASC",
                (start_date, end_date)
            )
            cols = [column[0] for column in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


@mcp.tool()
def summarize_expenses(start_date: str, end_date: str, category: str = None):
    """Summarize expenses from the given date range, optionally filtered by category."""
    # Validate date formats
    if not validate_date(start_date) or not validate_date(end_date):
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            if category:
                cur = conn.execute(
                    "SELECT category, SUM(amount) as total FROM expenses WHERE date BETWEEN ? AND ? AND category = ? GROUP BY category",
                    (start_date, end_date, category)
                )
            else:
                cur = conn.execute(
                    "SELECT category, SUM(amount) as total FROM expenses WHERE date BETWEEN ? AND ? GROUP BY category",
                    (start_date, end_date)
                )
            cols = [column[0] for column in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


@mcp.tool()
def edit_expense(expense_id: int, date: str = None, amount: float = None, category: str = None, subcategory: str = None, note: str = None):
    """Edit an expense entry by ID."""
    # Validate date if provided
    if date is not None and not validate_date(date):
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}
    
    # Validate amount if provided
    if amount is not None and amount <= 0:
        return {"status": "error", "message": "Amount must be positive"}
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            expense = cur.fetchone()
            
            if not expense:
                return {"status": "error", "message": f"Expense with ID {expense_id} not found."}

            # Use existing values if no new value provided
            updated_date = date if date is not None else expense[1]
            updated_amount = amount if amount is not None else expense[2]
            updated_category = category if category is not None else expense[3]
            updated_subcategory = subcategory if subcategory is not None else expense[4]
            updated_note = note if note is not None else expense[5]

            conn.execute(
                "UPDATE expenses SET date = ?, amount = ?, category = ?, subcategory = ?, note = ? WHERE id = ?",
                (updated_date, updated_amount, updated_category, updated_subcategory, updated_note, expense_id)
            )
            conn.commit()

            return {"status": "success", "message": "Expense updated successfully."}
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


@mcp.tool()
def delete_expense(expense_id: int):
    """Delete an expense entry by ID."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            expense = cur.fetchone()
            
            if not expense:
                return {"status": "error", "message": f"Expense with ID {expense_id} not found."}

            conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()

            return {"status": "success", "message": "Expense deleted successfully."}
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


@mcp.tool()
def get_expense_by_id(expense_id: int):
    """Get a single expense by ID."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute("SELECT id, date, amount, category, subcategory, note FROM expenses WHERE id = ?", (expense_id,))
            expense = cur.fetchone()
            if expense:
                cols = [column[0] for column in cur.description]
                return dict(zip(cols, expense))
            return {"status": "error", "message": f"Expense with ID {expense_id} not found."}
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


@mcp.tool()
def get_categories():
    """Get list of all unique categories used."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute("SELECT DISTINCT category FROM expenses ORDER BY category")
            categories = [row[0] for row in cur.fetchall()]
            return {"status": "success", "categories": categories}
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


@mcp.tool()
def get_total_expenses(start_date: str, end_date: str):
    """Get total expenses for a date range."""
    # Validate date formats
    if not validate_date(start_date) or not validate_date(end_date):
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                "SELECT SUM(amount) as total, COUNT(*) as count FROM expenses WHERE date BETWEEN ? AND ?",
                (start_date, end_date)
            )
            result = cur.fetchone()
            return {
                "status": "success",
                "total": result[0] if result[0] else 0,
                "count": result[1],
                "start_date": start_date,
                "end_date": end_date
            }
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
