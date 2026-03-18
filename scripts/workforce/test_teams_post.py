#!/usr/bin/env python3
"""
Test script: Post a message to the #agent-shannon channel in Microsoft Teams.

Uses Microsoft Graph API with client credentials (app-only) auth flow.
Requires AZURE_TENANT_ID, AZURE_BOT_APP_ID, AZURE_BOT_APP_SECRET in .env.
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_BOT_APP_ID")
CLIENT_SECRET = os.getenv("AZURE_BOT_APP_SECRET")
TEAM_NAME = os.getenv("TEAMS_TEAM_NAME", "Agent Workforce")
CHANNEL_NAME = os.getenv("TEAMS_CHANNEL_NAME", "agent-shannon")

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["https://graph.microsoft.com/.default"]


def get_access_token() -> str:
    """Acquire an app-only access token via MSAL client credentials flow."""
    try:
        import msal
    except ImportError as exc:
        print("ERROR: msal is required to use this helper script.")
        print("Install it with: pip install msal")
        raise SystemExit(1) from exc

    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=SCOPES)

    if "access_token" not in result:
        print(f"ERROR: Failed to acquire token: {result.get('error_description', result)}")
        sys.exit(1)

    print("OK: Access token acquired.")
    return result["access_token"]


def find_team(headers: dict) -> str:
    """Find the Team by display name, return its ID."""
    # Use $filter to find the team by name
    resp = requests.get(
        f"{GRAPH_BASE}/groups",
        headers=headers,
        params={
            "$filter": f"displayName eq '{TEAM_NAME}' and resourceProvisioningOptions/Any(x:x eq 'Team')",
            "$select": "id,displayName",
        },
    )
    resp.raise_for_status()
    groups = resp.json().get("value", [])

    if not groups:
        print(f"ERROR: Team '{TEAM_NAME}' not found. Available teams:")
        # List all teams for debugging
        all_resp = requests.get(
            f"{GRAPH_BASE}/groups",
            headers=headers,
            params={
                "$filter": "resourceProvisioningOptions/Any(x:x eq 'Team')",
                "$select": "id,displayName",
                "$top": "20",
            },
        )
        if all_resp.ok:
            for g in all_resp.json().get("value", []):
                print(f"  - {g['displayName']} ({g['id']})")
        sys.exit(1)

    team_id = groups[0]["id"]
    print(f"OK: Found team '{TEAM_NAME}' (id={team_id})")
    return team_id


def find_channel(headers: dict, team_id: str) -> str:
    """Find the channel by display name within the team, return its ID."""
    resp = requests.get(
        f"{GRAPH_BASE}/teams/{team_id}/channels",
        headers=headers,
        params={"$select": "id,displayName"},
    )
    resp.raise_for_status()
    channels = resp.json().get("value", [])

    # Match channel name (case-insensitive, with or without # prefix)
    target = CHANNEL_NAME.lstrip("#").lower()
    match = None
    for ch in channels:
        if ch["displayName"].lstrip("#").lower() == target:
            match = ch
            break

    if not match:
        print(f"ERROR: Channel '{CHANNEL_NAME}' not found in team '{TEAM_NAME}'. Available channels:")
        for ch in channels:
            print(f"  - {ch['displayName']} ({ch['id']})")
        sys.exit(1)

    print(f"OK: Found channel '{match['displayName']}' (id={match['id']})")
    return match["id"]


def post_message(headers: dict, team_id: str, channel_id: str, message: str) -> None:
    """Post a message to the channel via Graph API."""
    resp = requests.post(
        f"{GRAPH_BASE}/teams/{team_id}/channels/{channel_id}/messages",
        headers=headers,
        json={
            "body": {
                "contentType": "html",
                "content": message,
            }
        },
    )

    if resp.status_code == 201:
        msg_id = resp.json().get("id", "unknown")
        print(f"OK: Message posted successfully (id={msg_id})")
    else:
        print(f"ERROR: Failed to post message (HTTP {resp.status_code})")
        print(f"  Response: {resp.text}")
        sys.exit(1)


def main():
    # Validate env vars
    missing = []
    for var in ("AZURE_TENANT_ID", "AZURE_BOT_APP_ID", "AZURE_BOT_APP_SECRET"):
        if not os.getenv(var):
            missing.append(var)
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print(f"  Looked for .env at: {env_path}")
        sys.exit(1)

    # Authenticate
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Find team and channel
    team_id = find_team(headers)
    channel_id = find_channel(headers, team_id)

    # Post test message
    message = (
        "<b>Shannon Communications Agent — Test Message</b><br><br>"
        "If you can see this, the bot has the correct permissions to post to this channel.<br>"
        "<em>Sent via Microsoft Graph API (app-only auth)</em>"
    )
    post_message(headers, team_id, channel_id, message)
    print("\nDone. Check #agent-shannon in Teams.")


if __name__ == "__main__":
    main()
