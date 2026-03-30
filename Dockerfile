##########################################################################
# Dockerfile — Cornelis Networks AI Agent Workforce
#
# Single-image, multi-entrypoint pattern:
#   This Dockerfile builds ONE image shared by all 17 agents. Each agent
#   runs as a separate container (via docker-compose) that overrides the
#   default CMD with its own uvicorn entrypoint. For example:
#
#     drucker:
#       image: cn-agent-workforce
#       command: ["uvicorn", "agents.drucker_api:app", "--host", "0.0.0.0", "--port", "8201"]
#
#     shannon:
#       image: cn-agent-workforce
#       command: ["uvicorn", "agents.shannon_api:app", "--host", "0.0.0.0", "--port", "8200"]
#
#   Environment variables (.env) are mounted at runtime — never baked in.
#   Port assignments: Shannon 8200, Drucker 8201, Gantt 8202, Hypatia 8203, etc.
##########################################################################

# =======================================================================
# Stage 1: Builder
# Purpose: Install all Python dependencies in an isolated build stage so
# that build tools, caches, and intermediate artifacts stay out of the
# final runtime image.
# =======================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy dependency manifests first to maximise Docker layer caching.
# Changes to source code won't invalidate the expensive pip-install layer.
COPY pyproject.toml requirements.txt ./

# Install core + agent pipeline dependencies (no dev/test extras).
RUN pip install --no-cache-dir -e ".[agents]"

# Copy all source files into the build context.
COPY . .

# =======================================================================
# Stage 2: Runtime
# Purpose: Minimal production image containing only the installed packages,
# application source, and runtime system dependencies. No compilers, no
# build caches, no test fixtures.
# =======================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime-only system dependencies.
# git: required by some version/tagging operations at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# --- Copy installed Python packages from builder ---
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# --- Copy installed CLI scripts/entrypoints from builder ---
COPY --from=builder /usr/local/bin /usr/local/bin

# --- Copy application source from builder ---
# Top-level modules (mcp_server.py, jira_utils.py, confluence_utils.py, etc.)
COPY --from=builder /build/*.py /app/

# Agent definitions, APIs, and workforce sub-agents
COPY --from=builder /build/agents/ /app/agents/

# Thin tool wrappers that return ToolResult objects
COPY --from=builder /build/tools/ /app/tools/

# Adapters for external service integrations
COPY --from=builder /build/adapters/ /app/adapters/

# Prompt files and agent configuration (config/prompts/*.md, etc.)
COPY --from=builder /build/config/ /app/config/

# FastAPI app factory and shared middleware
COPY --from=builder /build/framework/ /app/framework/

# Pure business logic (no CLI concerns)
COPY --from=builder /build/core/ /app/core/

# Per-domain state stores and persistence backends
COPY --from=builder /build/state/ /app/state/

# LLM client abstractions
COPY --from=builder /build/llm/ /app/llm/

# Static data files
COPY --from=builder /build/data/ /app/data/

# Notification dispatchers
COPY --from=builder /build/notifications/ /app/notifications/

# JSON schemas for validation
COPY --from=builder /build/schemas/ /app/schemas/

# Legacy Shannon FastAPI Teams service
COPY --from=builder /build/shannon/ /app/shannon/

# Create persistent data directories for state, logs, and artifacts.
RUN mkdir -p /data/state /data/logs /data/artifacts

# Runtime environment defaults.
# PYTHONUNBUFFERED: flush stdout/stderr immediately (critical for container logging).
# PYTHONDONTWRITEBYTECODE: skip .pyc generation (read-only filesystem friendly).
# PERSISTENCE_DIR / LOG_DIR: default paths for state stores and log output.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PERSISTENCE_DIR=/data/state \
    LOG_DIR=/data/logs

# All agents listen on ports in the 8200-8227 range.
EXPOSE 8200-8227

# Health check — probes the /health endpoint exposed by create_agent_app().
# PORT defaults to 8200 if not set; each compose service sets its own PORT.
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8200}/health')" || exit 1

# Default entrypoint: Drucker agent on port 8201.
# Each docker-compose service overrides this CMD with its own agent + port.
CMD ["uvicorn", "agents.drucker.api:app", "--host", "0.0.0.0", "--port", "8201"]
