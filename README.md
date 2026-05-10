<div align="center">

# 💸 Expense Tracker — Remote MCP Server

### A Production-Ready MCP Server That Lets Claude Manage Your Expenses via Natural Language

> _"Add ₹500 lunch expense" → Claude calls your MCP → SQLite updated. No UI needed._

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Model_Context_Protocol-6B46C1?style=for-the-badge&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io)
[![Claude](https://img.shields.io/badge/Claude-AI_Client-CC785C?style=for-the-badge&logo=anthropic&logoColor=white)](https://claude.ai)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![uv](https://img.shields.io/badge/uv-Package_Manager-DE5FE9?style=for-the-badge&logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![FastMCP](https://img.shields.io/badge/FastMCP-Server_Framework-FF6B35?style=for-the-badge&logo=python&logoColor=white)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## 📌 What It Does

**Expense Tracker MCP Server** is a **remote MCP (Model Context Protocol) server** that exposes expense management tools directly to Claude — letting you log, query, and summarize your expenses using plain English conversation, with all data persisted in a local SQLite database.

No frontend. No forms. No dashboards. Just talk to Claude.

### 🎯 What You Can Do (via Claude)

| Natural Language | What Happens Under the Hood |
|---|---|
| `"Add ₹450 for groceries today"` | `add_expense(amount=450, category="groceries", date=today)` |
| `"How much did I spend this week?"` | `get_expenses(date_range="this_week")` → summed & returned |
| `"Show all food expenses in April"` | `get_expenses(category="food", month="April")` |
| `"Delete that duplicate taxi entry"` | `delete_expense(id=42)` |
| `"What's my biggest spending category?"` | `summarize_expenses()` → grouped by category |
| `"Give me a monthly breakdown"` | `monthly_summary()` → totals per month |

---

## 🏛️ Architecture

### How MCP Works — The Full Flow

```
  YOU (talking to Claude)
        │
        │  "Add ₹500 lunch expense for today"
        │
        ▼
  ┌─────────────────────────────────────────────────┐
  │               CLAUDE (AI Client)                │
  │                                                 │
  │  Understands intent → selects the right tool    │
  │  → formats arguments → calls MCP server         │
  └─────────────────────┬───────────────────────────┘
                        │
                        │  HTTP/SSE  (Remote MCP Protocol)
                        │
                        ▼
  ┌─────────────────────────────────────────────────┐
  │         EXPENSE TRACKER MCP SERVER              │
  │              (main.py — FastMCP)                │
  │                                                 │
  │  Registered Tools:                              │
  │  ┌──────────────────────────────────────────┐   │
  │  │  @mcp.tool()  add_expense()              │   │
  │  │  @mcp.tool()  get_expenses()             │   │
  │  │  @mcp.tool()  delete_expense()           │   │
  │  │  @mcp.tool()  summarize_expenses()       │   │
  │  │  @mcp.tool()  monthly_summary()          │   │
  │  └──────────────────────────────────────────┘   │
  │                                                 │
  │  Tool execution → SQL query built & run         │
  └─────────────────────┬───────────────────────────┘
                        │
                        │  SQL (read / write)
                        │
                        ▼
  ┌─────────────────────────────────────────────────┐
  │              expenses.db (SQLite)               │
  │                                                 │
  │  Table: expenses                                │
  │  ┌────┬────────┬──────────┬────────┬──────────┐ │
  │  │ id │ amount │ category │  date  │  notes   │ │
  │  ├────┼────────┼──────────┼────────┼──────────┤ │
  │  │  1 │  450   │ groceries│2025-04 │ Big Bazar│ │
  │  │  2 │  150   │ food     │2025-04 │ lunch    │ │
  │  └────┴────────┴──────────┴────────┴──────────┘ │
  └─────────────────────────────────────────────────┘
                        │
                        │  JSON result
                        │
                        ▼
  ┌─────────────────────────────────────────────────┐
  │               CLAUDE (AI Client)                │
  │  Formats result into a human-friendly response  │
  └─────────────────────────────────────────────────┘
                        │
                        ▼
  YOU get: "Added ₹500 lunch expense for today ✅
            Your total food spend this month: ₹2,340"
```

### MCP Tool Registration Pattern

```python
# How tools are exposed to Claude — clean decorator pattern
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Expense Tracker")

@mcp.tool()
def add_expense(amount: float, category: str, date: str, notes: str = "") -> str:
    """Add a new expense entry to the database."""
    # → inserts into SQLite → returns confirmation string

@mcp.tool()
def get_expenses(category: str = None, date_range: str = None) -> list[dict]:
    """Retrieve expenses with optional filters."""
    # → queries SQLite → returns list of expense dicts

@mcp.tool()
def summarize_expenses() -> dict:
    """Get total spending grouped by category."""
    # → GROUP BY query → returns category totals
```

---

## 🖥️ Demo

> **Replace this with a real screen recording.** Here's exactly how to record it:

```
📹  Best demo flow (2 min recording):

  1. Start the MCP server  →  python main.py
  2. Open Claude.ai        →  Settings → MCP Servers → Add yours
  3. In Claude chat, type:
       "Add ₹800 dinner expense for yesterday"
       "Add ₹1200 groceries today"
       "What's my total spend this week?"
       "Break it down by category"
  4. Screenshot Claude's response showing the expense summary

  Tools:  scrcpy (Android screen mirror) + OBS for recording
          OR just screenshot Claude's response panel
```

**Expected Claude Response Preview:**

```
┌──────────────────────────────────────────────────────┐
│  You: "Show me my spending breakdown this month"     │
│                                                      │
│  Claude:  Here's your expense breakdown for April:   │
│                                                      │
│  📊 Category Summary                                 │
│  ─────────────────────────────                       │
│  🍔 Food & Dining      ₹3,240   (34%)               │
│  🛒 Groceries          ₹2,800   (29%)               │
│  🚕 Transport          ₹1,450   (15%)               │
│  💊 Health             ₹900     (9%)                │
│  📦 Other              ₹1,210   (13%)               │
│  ─────────────────────────────                       │
│  💰 Total              ₹9,600                       │
│                                                      │
│  Your biggest category is Food & Dining. Want me     │
│  to set a budget limit for next month?               │
└──────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Technology | Role |
|---|---|
| **Python 3.12+** | Core server language |
| **MCP (Model Context Protocol)** | Anthropic's open standard for AI ↔ tool communication |
| **FastMCP** | High-level MCP server framework (decorator-based tool registration) |
| **SQLite** (`expenses.db`) | Lightweight, zero-config persistent storage |
| **uv** | Ultra-fast Python package manager (replaces pip + venv) |
| **Claude** | AI client that discovers and calls the MCP tools |

---

## ⚡ How to Run

### Prerequisites

- Python 3.12+
- `uv` installed → `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Claude.ai Pro/Team account (for remote MCP support) **OR** Claude Desktop (for local MCP)

### 1. Clone & Install

```bash
git clone https://github.com/Rohan171819/Expense-Tracker-Remote-MCP-Server.git
cd Expense-Tracker-Remote-MCP-Server

# Install dependencies with uv (fast)
uv sync

# OR with pip
pip install -r requirements.txt
```

### 2. Run the MCP Server

```bash
# With uv
uv run main.py

# OR directly
python main.py
```

Server starts on `http://localhost:8000` (or configured port).

### 3. Connect to Claude Desktop (Local)

Add this to your Claude Desktop config file:

**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "uv",
      "args": ["run", "main.py"],
      "cwd": "/absolute/path/to/Expense-Tracker-Remote-MCP-Server"
    }
  }
}
```

Restart Claude Desktop → you'll see a 🔧 tools icon in chat.

### 4. Connect to Claude.ai (Remote — Web)

If deployed remotely:

1. Go to `claude.ai` → Settings → **Integrations**
2. Add MCP Server URL: `https://your-deployed-url/mcp`
3. Claude will auto-discover all registered tools

### 5. Test It

Once connected, open Claude and try:

```
"Add ₹500 expense for lunch today"
"Show all my expenses this week"
"What's my total spending by category?"
"Delete expense number 3"
```

---

## 📂 Project Structure

```
Expense-Tracker-Remote-MCP-Server/
│
├── main.py           # MCP server — all tools defined here
├── expenses.db       # SQLite database (auto-created on first run)
├── pyproject.toml    # Project metadata + dependencies (uv)
├── uv.lock           # Locked dependency versions
├── .python-version   # Python version pin (3.12)
├── .gitignore
└── README.md
```

---

## 🔧 Available MCP Tools

| Tool | Arguments | Returns |
|---|---|---|
| `add_expense` | `amount`, `category`, `date`, `notes?` | Confirmation string |
| `get_expenses` | `category?`, `date_range?`, `limit?` | List of expense objects |
| `delete_expense` | `id` | Confirmation string |
| `summarize_expenses` | — | Dict of category → total |
| `monthly_summary` | `year?` | Dict of month → total |

---

## 🗺️ Roadmap

- [x] Remote MCP server with FastMCP
- [x] SQLite persistence
- [x] Add / get / delete / summarize tools
- [x] uv-based dependency management
- [ ] Budget alerts (`set_budget`, `check_budget`)
- [ ] Export to CSV tool
- [ ] Multi-currency support
- [ ] Deploy to Railway / Render (public MCP endpoint)
- [ ] N8N webhook integration for automated logging

---

## 👤 Author

**Rohan Sharma** — AI/ML Engineer · LangGraph + MCP Developer  
MCA @ GL Bajaj Institute of Technology & Management

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/rohan-sharma-048266246)
[![Email](https://img.shields.io/badge/Email-sharma1718rohan@gmail.com-D14836?style=flat-square&logo=gmail)](mailto:sharma1718rohan@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github)](https://github.com/Rohan171819)

---

<div align="center">

**⭐ Star this if you want AI to manage your money — not spreadsheets**

</div>
