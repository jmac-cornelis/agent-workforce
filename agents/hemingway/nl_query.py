##########################################################################################
#
# Module: agents/hemingway/nl_query.py
#
# Description: Natural language query translation for Hemingway. Uses LLM function calling
#              to convert plain English questions into structured documentation tool calls,
#              execute them via Hemingway REST API, and summarize results.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict

log = logging.getLogger(os.path.basename(sys.argv[0]))


# ---------------------------------------------------------------------------
# OpenAI function-calling tool schemas
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "doc_search",
            "description": "Search stored documentation records by query text, doc type, project, or source reference. Use when the user asks to find, search, or look up docs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free-text search query"},
                    "doc_type": {
                        "type": "string",
                        "description": "Filter by doc type: as_built, engineering_reference, how_to, user_guide, release_note_support",
                    },
                    "project_key": {"type": "string", "description": "Jira project key (e.g. STL)"},
                    "published_only": {"type": "boolean", "description": "Only return published records", "default": False},
                    "limit": {"type": "integer", "description": "Max results to return", "default": 10},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "doc_generate",
            "description": "Generate a documentation record from source files. Use when the user asks to generate, create, or write documentation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_title": {"type": "string", "description": "Title for the documentation record"},
                    "doc_type": {
                        "type": "string",
                        "description": "Document type: as_built, engineering_reference, how_to, user_guide, release_note_support",
                        "default": "engineering_reference",
                    },
                    "source_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Source files to analyze",
                    },
                    "repo_name": {"type": "string", "description": "GitHub repo in owner/name format (e.g. cornelisnetworks/opa-psm2)"},
                    "project_key": {"type": "string", "description": "Jira project key"},
                    "doc_summary": {"type": "string", "description": "Brief summary of the document"},
                },
                "required": ["doc_title", "doc_type", "source_paths"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "doc_impact",
            "description": "Detect which documentation is impacted by source changes. Use when the user asks about impact, what changed, or what docs need updating.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_title": {"type": "string", "description": "Title of the document to assess impact for"},
                    "source_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Changed source files to analyze",
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Document type (default: engineering_reference)",
                    },
                },
                "required": ["doc_title", "source_paths"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "doc_records",
            "description": "List stored documentation records with optional filtering. Use when the user asks to list, show all, or enumerate docs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_type": {
                        "type": "string",
                        "description": "Filter by doc type: as_built, engineering_reference, how_to, user_guide, release_note_support",
                    },
                    "limit": {"type": "integer", "description": "Max records to return", "default": 20},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pr_review",
            "description": "Analyze a pull request and generate documentation. Use when the user mentions a PR number or asks about PR documentation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "GitHub repo in owner/name format (e.g. cornelisnetworks/opa-psm2)"},
                    "pr_number": {"type": "integer", "description": "Pull request number"},
                },
                "required": ["repo", "pr_number"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# System prompt for the LLM query translator
# ---------------------------------------------------------------------------

NL_SYSTEM_PROMPT = """You are a Hemingway query assistant for Cornelis Networks documentation.
You translate plain English questions into structured tool calls.

Hemingway is a documentation agent that generates, searches, and publishes
source-grounded engineering documentation.

CONVENTIONS:
- Doc types: as_built, engineering_reference, how_to, user_guide, release_note_support
- Repos follow pattern: cornelisnetworks/{repo} or jmac-cornelis/{repo}
- Default project: STL

TOOL SELECTION:
- User asks to "find", "search", "look up" docs → doc_search
- User asks to "generate", "create", "write" docs → doc_generate
- User asks to "list", "show all", "enumerate" docs → doc_records
- User mentions a "PR", "pull request", or PR number → pr_review
- User asks about "impact", "what changed", "what docs need updating" → doc_impact

Always call exactly one tool per query."""


# ---------------------------------------------------------------------------
# Tool executor functions — HTTP calls to Hemingway REST API on localhost:8203
# ---------------------------------------------------------------------------

def _exec_doc_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search documentation records via Hemingway API."""
    import requests
    resp = requests.post("http://localhost:8203/v1/docs/search", json=args, timeout=30)
    return resp.json()


def _exec_doc_generate(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate documentation from source files via Hemingway API."""
    import requests
    # Set dry_run=True by default for NL queries to avoid accidental generation
    if "dry_run" not in args:
        args["dry_run"] = True
    resp = requests.post("http://localhost:8203/v1/docs/generate", json=args, timeout=120)
    return resp.json()


def _exec_doc_impact(args: Dict[str, Any]) -> Dict[str, Any]:
    """Detect documentation impact of changes via Hemingway API."""
    import requests
    resp = requests.post("http://localhost:8203/v1/docs/impact", json=args, timeout=30)
    return resp.json()


def _exec_doc_records(args: Dict[str, Any]) -> Dict[str, Any]:
    """List stored documentation records via Hemingway API."""
    import requests
    params = {}
    if "doc_type" in args:
        params["doc_type"] = args["doc_type"]
    if "limit" in args:
        params["limit"] = args["limit"]
    resp = requests.get("http://localhost:8203/v1/docs/records", params=params, timeout=30)
    return resp.json()


def _exec_pr_review(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a PR and generate docs via Hemingway API."""
    import requests
    resp = requests.post("http://localhost:8203/v1/docs/pr-review", json=args, timeout=30)
    return resp.json()


TOOL_EXECUTORS = {
    "doc_search": _exec_doc_search,
    "doc_generate": _exec_doc_generate,
    "doc_impact": _exec_doc_impact,
    "doc_records": _exec_doc_records,
    "pr_review": _exec_pr_review,
}


# ---------------------------------------------------------------------------
# Result summarizer — second LLM call (no tools)
# ---------------------------------------------------------------------------

def _summarize_results(llm, query, tool_name, tool_args, result):
    result_preview = json.dumps(result, default=str)
    if len(result_preview) > 8000:
        # Truncate large results but keep structure
        preview = dict(result) if isinstance(result, dict) else {"data": result}
        if "data" in preview and isinstance(preview["data"], list):
            preview["data"] = preview["data"][:10]
            preview["data_truncated"] = True
        if "results" in preview and isinstance(preview["results"], list):
            preview["results"] = preview["results"][:10]
            preview["results_truncated"] = True
        result_preview = json.dumps(preview, default=str)

    from llm.base import Message

    messages = [
        Message.system(
            "Summarize these Hemingway documentation query results concisely for the user. "
            "Be specific with numbers and document titles. Use plain English, not JSON."
        ),
        Message.user(
            f"User asked: {query}\nTool: {tool_name}\nArgs: {json.dumps(tool_args)}\n"
            f"Results:\n{result_preview}"
        ),
    ]
    response = llm.chat(messages=messages, temperature=0.3, max_tokens=500)
    return response.content


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_nl_query(query: str) -> Dict[str, Any]:
    """Translate a plain English query into a Hemingway tool call, execute it,
    and return structured results with a natural language summary."""
    from llm.cornelis_llm import CornelisLLM
    from llm.base import Message

    llm = CornelisLLM(model="developer-sonnet")

    messages = [
        Message.system(NL_SYSTEM_PROMPT),
        Message.user(query),
    ]

    response = llm.chat(messages=messages, temperature=0.1, tools=TOOL_SCHEMAS)

    raw = response.raw_response
    choice = raw.choices[0]

    # If the LLM chose not to call a tool, return its text response directly
    if not hasattr(choice.message, "tool_calls") or not choice.message.tool_calls:
        return {
            "ok": True,
            "query": query,
            "tool_used": None,
            "tool_args": {},
            "result": None,
            "summary": response.content,
        }

    tool_call = choice.message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

    # Execute the selected tool
    executor = TOOL_EXECUTORS.get(tool_name)
    if not executor:
        return {"ok": False, "error": f"Unknown tool: {tool_name}"}

    try:
        result = executor(tool_args)
    except Exception as e:
        log.error(f"NL query tool execution failed: {tool_name} — {e}")
        return {"ok": False, "error": str(e), "tool_used": tool_name, "tool_args": tool_args}

    # Summarize with second LLM call
    summary = _summarize_results(llm, query, tool_name, tool_args, result)

    return {
        "ok": True,
        "query": query,
        "tool_used": tool_name,
        "tool_args": tool_args,
        "result": result,
        "summary": summary,
    }
