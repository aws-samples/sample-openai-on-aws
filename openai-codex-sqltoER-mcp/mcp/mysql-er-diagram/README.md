# MySQL ER Diagram MCP

Local-only MCP server for generating Mermaid ER diagrams from MySQL or Aurora
MySQL schema metadata in `INFORMATION_SCHEMA`.

The server is intended for authorized dev/test databases using a read-only
database user. It does not execute arbitrary SQL and does not read table row
data.
