# config/env/ — Credential-Domain Environment Files

## Purpose

This directory contains **credential-domain segregated** `.env` files for the
Docker Compose deployment. Instead of a single monolithic `.env`, credentials
are split by service domain so each agent container only mounts the env files
it actually needs (**least-privilege principle**).

| File | Domain | Example consumers |
|------|--------|-------------------|
| `shared.env` | Non-sensitive shared config | All agents |
| `jira.env` | Jira credentials | Drucker, Gantt, Hedy, Babbage, Linnaeus, Nightingale, Brooks |
| `llm.env` | LLM provider keys | Shannon, Drucker, Gantt, Hypatia, Ada, Curie, Hedy, Linus, Herodotus, Nightingale, Brooks |
| `github.env` | GitHub credentials | Drucker, Josephine, Hedy, Linus, Nightingale, Brandeis |
| `teams.env` | Teams / Azure credentials | Shannon, Herodotus |

## Usage

These files are **templates** — all secret values are left blank. Before
deployment:

1. Copy or fill in actual values for your environment.
2. Each variable appears in **exactly one** file (no duplication).
3. In `docker-compose.yml`, mount only the files each service needs:

```yaml
services:
  drucker:
    env_file:
      - config/env/shared.env
      - config/env/jira.env
      - config/env/llm.env
      - config/env/github.env
```

### Jira Identity Guidance

For shared deployment, prefer this split:

- `JIRA_SERVICE_EMAIL` / `JIRA_SERVICE_API_TOKEN`: the standing automation identity
- `JIRA_REQUESTER_EMAIL` / `JIRA_REQUESTER_API_TOKEN`: only for per-user or interactive execution, not for shared containers
- `JIRA_EMAIL` / `JIRA_API_TOKEN`: legacy local-development compatibility only

Use `JIRA_ENABLE_LEGACY_FALLBACK=false` in shared deployment to prevent
requester-mode execution from silently falling back to the legacy single-profile
credentials.

## Security

> **NEVER commit actual credentials.** The `.gitignore` is configured to block
> `config/env/*.env` files, but these templates are tracked because they contain
> no real secrets. If you add actual values, ensure your `.gitignore` rules
> prevent them from being committed.

For production, consider using Docker secrets or a vault integration instead of
plain env files.

## Local Development

For local development (outside Docker), use a single `.env` file at the
repository root instead. Agents use `from dotenv import load_dotenv; load_dotenv()`
which reads from `.env` by default.

## Further Reading

See [DEPLOYMENT_GUIDE.md](../../docs/workforce/DEPLOYMENT_GUIDE.md) for the
full deployment context and Docker Compose configuration.
