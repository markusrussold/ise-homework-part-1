# ISE Industrial Computing – Homework Part 1

Custom MCP math & database tool server, following the lecture samples
(`Sample 3 MCP` / `Sample 4 MCP Architecture`).

The MCP server exposes three tools. A LiteLLM ReAct client discovers those tools
at runtime and calls them over Streamable HTTP.

## Tools

| Tool | Purpose |
|---|---|
| `lookup_inventory` | SQLite lookup against `inventory.db` (`products`) |
| `compute_tiered_discount` | Tiered discount formula based on order volume |
| `append_audit_event` | Append a timestamped event to `logs/audit.log` |

The audit file is also published as the MCP resource `file://audit/events`.

Discount brackets:

- 1–9 units → 0%
- 10–49 units → 5%
- 50–99 units → 12%
- 100–249 units → 18%
- 250+ units → 25%

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- LiteLLM proxy running locally
- SQLite (`sqlite3` is in the Python standard library)

## Environment setup

```powershell
python -m pip install uv
python -m uv sync
copy .env.example .env
```

Edit `.env`:

```
LITELLM_API_BASE=http://localhost:4000
LITELLM_KEY=sk-your-litellm-key
LITELLM_DEFAULT_MODEL=gpt-4o-mini
MCP_SERVER_URL=http://localhost:8000/mcp
```

The first server start creates `inventory.db` if it is missing and seeds:

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL
);
```

You can also point the project at an existing `inventory.db` by placing the file
in this directory.

## Run

Terminal 1 – MCP server:

```powershell
python -m uv run python server.py
```

Terminal 2 – ReAct client (LiteLLM):

```powershell
python -m uv run python client.py
```

The client prompt looks up **Hydraulic Pump**, computes an 80-unit discount at
$120, and writes an audit event.

## Execution logs

See [`logs/execution.log`](logs/execution.log) for a captured client run that
exercises all three tools.
