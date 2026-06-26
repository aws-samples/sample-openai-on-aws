# MySQL ER Diagram - workshop

Generated: `2026-06-22T20:38:53.385881+00:00`

Scope: schema metadata only from `INFORMATION_SCHEMA`. No table row data is queried or written.

- Tables/views: 3
- Foreign keys: 2

```mermaid
erDiagram
  applications {
    BIGINT application_id PK
    BIGINT team_id
    VARCHAR_128 application_name
    TIMESTAMP created_at
  }
  deployments {
    BIGINT deployment_id PK
    BIGINT application_id
    VARCHAR_64 environment_name
    TIMESTAMP deployed_at
  }
  teams {
    BIGINT team_id PK
    VARCHAR_128 team_name UK
    TIMESTAMP created_at
  }
  applications }o--|| teams : "team_id references team_id"
  deployments }o--|| applications : "application_id references application_id"
```
