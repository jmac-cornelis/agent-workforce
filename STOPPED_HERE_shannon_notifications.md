# Shannon Notifications — Stopped Here

**Branch**: shannon-notifications
**Date**: 2026-04-04
**Status**: Code complete, blocked on Azure AD admin consent

---

## What Was Built

### New Files
- shannon/notification_router.py — Multi-channel notification dispatcher (Teams DM + email)

### Modified Files
| File | Change |
|------|--------|
| config/identity_map.yaml | Full jmac-cornelis entry with all platform IDs + notify prefs |
| agents/shannon/graph_client.py | Added send_email() method via Graph API |
| shannon/service.py | Wired send_notification() into post_notification() |
| shannon/app.py | Added POST /v1/bot/notify/dm endpoint |
| agents/hemingway/api.py | Added 3 notify_shannon() triggers (PR review, publish, impact) |
| agents/drucker/config/polling.yaml | Enabled PR reminders, notify_shannon: true on all jobs |
| config/shannon/agent_registry.yaml | Added Gantt notify_shannon: true |
| deploy/env/teams.env | Added SHANNON_APP_ID, SHANNON_APP_SECRET, SHANNON_TENANT_ID |

## What Works
- All 4 services healthy (Shannon:8200, Drucker:8201, Gantt:8202, Hemingway:8203)
- POST /v1/bot/notify/dm endpoint registered and functional
- Identity map loaded correctly for jmac-cornelis
- Graph API token acquisition works
- User.Read.All works (user lookup returns 200)
- Existing channel notifications unchanged

## What Is Blocked

### 1. Email — Mail.Send permission needs admin consent
- Permission added to Azure AD app Cornelis Agent Workforce Bot
- Grant admin consent button is greyed out (jmac is not Global Admin)
- Action needed: Azure AD Global Admin must visit this URL and click Accept:
  https://login.microsoftonline.com/4dbdb7da-74ee-4b45-8747-ef5ce5ebe68a/adminconsent?client_id=108ddbfd-d57d-4ead-8fd1-2baa72fa5e5f
- Once consented, email will work immediately (code is deployed)
- Sender address: john.macdonald@cornelisnetworks.com (configurable in identity_map.yaml)

### 2. Teams DMs — deferred to Power Automate approach
- Direct Graph API DMs require Chat.Create + Chat.ReadWrite.All (Teams Premium licensing)
- Decided to use Power Automate flow instead (free, same pattern as Drucker webhooks)
- NotificationRouter code supports both; just swap Teams DM implementation to webhook POST

## To Resume

### After admin consent is granted:
1. Restart services
2. Test: curl -X POST http://localhost:8200/v1/bot/notify/dm -H Content-Type: application/json -d '{agent_id:shannon,title:Test,text:Hello,target_users:[jmac-cornelis]}'
3. Check inbox for email

### For Teams DMs via Power Automate:
1. Create a Power Automate flow: HTTP trigger -> Send chat in Teams -> target user from body
2. Add flow webhook URL to identity_map.yaml or agent_registry.yaml
3. Update NotificationRouter._send_teams_dm() to POST to webhook instead of Graph API

### Azure AD App Details
- App Name: Cornelis Agent Workforce Bot
- Application (client) ID: 108ddbfd-d57d-4ead-8fd1-2baa72fa5e5f
- Directory (tenant) ID: 4dbdb7da-74ee-4b45-8747-ef5ce5ebe68a
- Secret expiry: 2028-03-15
