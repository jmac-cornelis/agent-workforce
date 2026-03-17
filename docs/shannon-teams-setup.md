# Shannon Teams Setup

This document describes the first Shannon deployment target for this repo:

1. A dedicated `#agent-shannon` standard channel exists in the `Agent Workforce` team.
2. A single Teams bot called Shannon is installed at team scope with the minimum practical permissions.
3. Shannon can receive channel messages when `@mentioned`.
4. Shannon can reply in-thread and post notifications back into `#agent-shannon`.

## Recommended v1 interaction model

- Use one Teams app and one bot identity for Shannon.
- Install the app into the `Agent Workforce` team.
- Create `#agent-shannon` as a standard channel.
- Require users to `@mention` Shannon in the channel.
- Do not request Resource-Specific Consent permissions in v1.
- Do not request Microsoft Graph application permissions in v1.
- Do not require Teams SSO in v1.

This keeps the first rollout on the lower-permission bot path while still allowing:

- `/stats`
- `/busy`
- `/work-today`
- `/token-status`
- `/decision-tree`
- `/why <record-id>`

## What to ask IT / Azure for

Ask IT for:

1. A Microsoft Entra app registration for Shannon.
2. A client secret or certificate for that app.
3. An Azure Bot resource connected to that app registration.
4. The Microsoft Teams channel enabled on that bot resource.
5. A public HTTPS messaging endpoint for Shannon:
   `https://<your-public-host>/api/messages`
6. Permission to upload a custom Teams app package, or an admin-managed upload into the org app catalog.
7. Installation of the app into the `Agent Workforce` team.

You do not need to ask for:

- `ChannelMessage.Read.Group`
- Graph application permissions
- Channel-wide message read access
- Personal-scope app install for v1

## Teams-side app settings

Use the template in [config/shannon/teams-app-manifest.template.json](/Users/johnmacdonald/tmp/jira-utilities/config/shannon/teams-app-manifest.template.json).

Important choices:

- `scopes`: `["team"]`
- `defaultInstallScope`: `"team"`
- no `authorization.permissions.resourceSpecific` block

## Channel and registry mapping

Shannon uses [config/shannon/agent_registry.yaml](/Users/johnmacdonald/tmp/jira-utilities/config/shannon/agent_registry.yaml) to map Teams channels to agents.

For the first rollout:

- keep only `shannon`
- leave `channel_id` and `team_id` blank until IT creates the channel
- fill them in after the first install or after you capture them from an inbound activity payload

## Local environment

Add these values to `.env` or `.env_prod`:

```bash
SHANNON_AGENT_REGISTRY_PATH=./config/shannon/agent_registry.yaml
SHANNON_STATE_DIR=./data/shannon
SHANNON_TEAMS_BOT_NAME=Shannon
SHANNON_TEAMS_POST_MODE=memory
SHANNON_SEND_WELCOME_ON_INSTALL=true
SHANNON_HOST=0.0.0.0
SHANNON_PORT=8200

# For live Teams posting:
SHANNON_TEAMS_APP_ID=
SHANNON_TEAMS_APP_PASSWORD=
```

Use `memory` mode for local testing. Switch to `botframework` once the bot credentials are available:

```bash
SHANNON_TEAMS_POST_MODE=botframework
```

## Running Shannon

From the repo root:

```bash
.venv/bin/python -m uvicorn shannon.app:app --host 0.0.0.0 --port 8200
```

Or through the helper:

```bash
.venv/bin/python -c "from shannon.app import run; run()"
```

## First verification sequence

1. Start Shannon locally or in your hosted environment.
2. Confirm health:

```bash
curl http://localhost:8200/v1/bot/health
```

3. Install the Teams app into the `Agent Workforce` team.
4. Add or verify the `#agent-shannon` channel.
5. In `#agent-shannon`, send:

```text
@Shannon /stats
```

6. Shannon should store the conversation reference and reply in-thread.
7. Then test the internal notification path:

```bash
curl -X POST http://localhost:8200/v1/bot/notify \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_id": "shannon",
    "title": "Shannon Notification Test",
    "text": "This is a direct notification test from the Shannon service."
  }'
```

## What this repo now provides

- `POST /api/messages`
  Standard Teams bot webhook endpoint.
- `POST /v1/teams/activities`
  Alias for easier local testing.
- `POST /v1/bot/notify`
  Internal notification API for Shannon and future agents.
- `GET /v1/bot/health`
  Health summary.
- `GET /v1/status/stats`
- `GET /v1/status/load`
- `GET /v1/status/work-summary`
- `GET /v1/status/tokens`
- `GET /v1/status/decisions`

## Current limitations

- Inbound Bot Framework JWT validation is not implemented yet.
- Only Shannon’s own commands are implemented in this first slice.
- Other agent channels are not routed yet.
- Proactive posting depends on a stored conversation reference from a prior install/update/message event.

Those are good next tasks after the Shannon bootstrap is standing up cleanly.
