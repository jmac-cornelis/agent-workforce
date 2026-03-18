# Shannon Teams Setup

This document describes the first Shannon deployment target for this repo:

1. A dedicated `#agent-shannon` standard channel exists in the `Agent Workforce` team.
2. A Teams Outgoing Webhook called Shannon is installed in that team with no Azure subscription requirement.
3. Shannon can receive channel messages when `@mentioned`.
4. Shannon can reply in-thread inside `#agent-shannon`.

## Recommended v1 interaction model

- Use one Teams Outgoing Webhook named Shannon.
- Create `#agent-shannon` as a standard channel.
- Require users to `@mention` Shannon in the channel.
- Do not request Azure Bot resources in v1.
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

## What you can do without Azure

If you are allowed to manage apps for the target team, you can do this without
an Azure subscription:

1. Open the target team in Teams.
2. Select `...` next to the team name.
3. Select `Manage team`.
4. Open the `Apps` tab.
5. Under `Upload an app`, select `Create an outgoing webhook`.
6. Create an outgoing webhook named `Shannon`.
7. Set the callback URL to:
   `https://<your-public-host>/v1/teams/outgoing-webhook`
8. Copy the HMAC secret Teams shows you.
9. Put that secret into:
   `SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET`

Microsoft documents this flow here:
https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook

## What to ask IT / Azure for later

Ask IT for:

1. A Microsoft Entra app registration for Shannon.
2. A client secret or certificate for that app.
3. An Azure Bot resource connected to that app registration.
4. The Microsoft Teams channel enabled on that bot resource.
5. A public HTTPS messaging endpoint for Shannon:
   `https://<your-public-host>/api/messages`
6. Permission to upload a custom Teams app package, or an admin-managed upload into the org app catalog.
7. Installation of the app into the `Agent Workforce` team.

You do not need to ask for the outgoing-webhook rollout:

- an Azure subscription
- an Azure Bot resource
- Graph application permissions
- Channel-wide message read access
- Personal-scope app install

You also do not need to ask for later bot rollout:

- `ChannelMessage.Read.Group`
- Graph application permissions
- Channel-wide message read access
- Personal-scope app install for v1

## Teams-side app settings for the no-Azure path

You do not need a Teams app manifest for the outgoing-webhook rollout.
The manifest template in [config/shannon/teams-app-manifest.template.json](/Users/johnmacdonald/tmp/jira-utilities/config/shannon/teams-app-manifest.template.json)
is still useful if you later move to a fuller bot deployment.

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
SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET=
SHANNON_SEND_WELCOME_ON_INSTALL=true
SHANNON_HOST=0.0.0.0
SHANNON_PORT=8200
```

Use `memory` mode for local testing. If you later move to a fuller bot setup,
switch to `botframework` once the bot credentials are available:

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

3. Create the Teams Outgoing Webhook in the `Agent Workforce` team.
4. Add or verify the `#agent-shannon` channel.
5. In `#agent-shannon`, send:

```text
@Shannon /stats
```

6. Shannon should validate the HMAC signature, store the request for audit, and reply in-thread.

## What this repo now provides

- `POST /v1/teams/outgoing-webhook`
  Teams Outgoing Webhook endpoint with HMAC verification.
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

- Only Shannon’s own commands are implemented in this first slice.
- Other agent channels are not routed yet.
- Outgoing Webhooks are channel-only and synchronous.
- Adaptive Cards in Teams Outgoing Webhooks support only `openURL` actions.
- Proactive posting is still a later follow-on if we stay on the no-Azure path.

Those are good next tasks after the Shannon bootstrap is standing up cleanly.
