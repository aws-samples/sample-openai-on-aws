import json
import sqlite3
import shutil
import os

DB_SOURCE = "/var/task/workshop.db"
DB_PATH = "/tmp/workshop.db"


def get_connection(readonly=True):
    if not os.path.exists(DB_PATH):
        shutil.copy2(DB_SOURCE, DB_PATH)
    if readonly:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


TOOLS = [
    {
        "name": "list_tables",
        "description": "Returns all table names in the database",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "describe_table",
        "description": "Returns column info and 3 sample rows for a given table",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Name of the table to describe"}
            },
            "required": ["table_name"]
        }
    },
    {
        "name": "read_query",
        "description": "Executes a read-only SQL query and returns results as JSON",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SELECT SQL query to execute"}
            },
            "required": ["sql"]
        }
    },
    {
        "name": "write_query",
        "description": "Executes a write SQL statement (CREATE VIEW or INSERT only)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SQL statement (CREATE VIEW or INSERT only)"}
            },
            "required": ["sql"]
        }
    }
]


def handle_list_tables():
    conn = get_connection()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def handle_describe_table(table_name):
    conn = get_connection()
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [{"name": row[1], "type": row[2]} for row in cursor.fetchall()]
    cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT 3")
    samples = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"columns": columns, "sample_rows": samples}


def handle_read_query(sql):
    stmt = sql.strip().upper()
    if not stmt.startswith("SELECT") and not stmt.startswith("WITH"):
        return {"error": "Only SELECT queries are allowed for read_query"}
    conn = get_connection(readonly=True)
    cursor = conn.execute(sql)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def handle_write_query(sql):
    stmt = sql.strip().upper()
    allowed = stmt.startswith("CREATE VIEW") or stmt.startswith("INSERT")
    blocked = any(kw in stmt for kw in ["DROP", "DELETE", "ALTER", "TRUNCATE", "UPDATE"])
    if not allowed or blocked:
        return {"error": "Only CREATE VIEW and INSERT statements are allowed"}
    conn = get_connection(readonly=False)
    conn.execute(sql)
    conn.commit()
    conn.close()
    return {"success": True}


def lambda_handler(event, context):
    method = event.get("method")
    req_id = event.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "workshop-db-mcp", "version": "1.0.0"}
            }
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS}
        }

    if method == "tools/call":
        tool_name = event["params"]["name"]
        args = event["params"].get("arguments", {})

        if tool_name == "list_tables":
            result = handle_list_tables()
        elif tool_name == "describe_table":
            result = handle_describe_table(args["table_name"])
        elif tool_name == "read_query":
            result = handle_read_query(args["sql"])
        elif tool_name == "write_query":
            result = handle_write_query(args["sql"])
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": json.dumps(result)}]}
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"}
    }
