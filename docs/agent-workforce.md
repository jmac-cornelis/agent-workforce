# Agent Workforce — Design Reference

## Purpose
This internal document candidate was generated from authoritative source artifacts for review before publication.

## Metadata
- Documentation class: `as_built`
- Generated: `2026-04-08 14:47 UTC`
- Confidence: `medium`

## Authoritative Inputs
- `jmac-cornelis/agent-workforce:AGENTS.md` (source)
- `jmac-cornelis/agent-workforce:STOPPED_HERE_shannon_notifications.md` (source)
- `jmac-cornelis/agent-workforce:.github/workflows/tests.yml` (source)
- `jmac-cornelis/agent-workforce:.github/workflows/docs.yml` (source)
- `jmac-cornelis/agent-workforce:README.md` (source)
- `jmac-cornelis/agent-workforce:.sisyphus/plans/12.2-release-cockpit-recommendations.md` (source)
- `jmac-cornelis/agent-workforce:.sisyphus/plans/12.2-release-status-page.md` (source)
- `jmac-cornelis/agent-workforce:.github/workflows/doc-generation.yml` (source)
- `jmac-cornelis/agent-workforce:TODO.md` (source)
- `jmac-cornelis/agent-workforce:adapters/__init__.py` (source)
- `jmac-cornelis/agent-workforce:adapters/environment/__init__.py` (source)
- `jmac-cornelis/agent-workforce:adapters/fuze/adapter.py` (source)
- `jmac-cornelis/agent-workforce:adapters/fuze/__init__.py` (source)
- `jmac-cornelis/agent-workforce:adapters/github/__init__.py` (source)
- `jmac-cornelis/agent-workforce:adapters/environment/adapter.py` (source)
- `jmac-cornelis/agent-workforce:adapters/github/adapter.py` (source)
- `jmac-cornelis/agent-workforce:adapters/github/webhook.py` (source)
- `jmac-cornelis/agent-workforce:adapters/teams/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/README.md` (source)
- `jmac-cornelis/agent-workforce:adapters/teams/adapter.py` (source)
- `jmac-cornelis/agent-workforce:agents/ada/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/ada/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agent_cli.py` (source)
- `jmac-cornelis/agent-workforce:agents/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/ada/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/ada/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/ada/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/ada/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/ada/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/ada/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/babbage/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/babbage/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/babbage/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/babbage/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/babbage/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/babbage/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/babbage/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/babbage/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/base.py` (source)
- `jmac-cornelis/agent-workforce:agents/bernerslee/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/bernerslee/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/bernerslee/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/bernerslee/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/bernerslee/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/bernerslee/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/blackstone/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/bernerslee/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/bernerslee/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/blackstone/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/blackstone/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/blackstone/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/blackstone/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/brandeis/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/brandeis/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/brooks/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/brandeis/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/brooks/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/brooks/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/brooks/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/brooks/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/brooks/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/brooks/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/brooks/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/curie/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/curie/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/curie/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/curie/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/curie/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/curie/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/curie/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/curie/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/cards.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/config/monitor.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/config/polling.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/cli.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/config/pr_reminders.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/docs/as-built.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/docs/config.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/docs/docs.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/jira_reporting.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/docs/state.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/nl_query.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/pr_reminders.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/state/activity_counter.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/state/learning_store.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/state/monitor_state.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/state/report_store.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/state/pr_reminder_state.py` (source)
- `jmac-cornelis/agent-workforce:agents/drucker/tools.py` (source)
- `jmac-cornelis/agent-workforce:agents/faraday/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/faraday/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/faraday/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/faraday/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/faraday/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/faraday/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/faraday/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/faraday/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/feature_plan_builder.py` (source)
- `jmac-cornelis/agent-workforce:agents/feature_planning_models.py` (source)
- `jmac-cornelis/agent-workforce:agents/feature_planning_orchestrator.py` (source)
- `jmac-cornelis/agent-workforce:agents/galileo/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/galileo/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/galileo/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/galileo/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/galileo/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/galileo/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/galileo/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/galileo/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/cli.py` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/components.py` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/docs/PM_IMPLEMENTATION_BACKLOG.md` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/docs/as-built.md` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/docs/prompts.md` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/nl_query.py` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/state/dependency_review_store.py` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/state/release_monitor_store.py` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/state/release_survey_store.py` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/state/snapshot_store.py` (source)
- `jmac-cornelis/agent-workforce:agents/gantt/tools.py` (source)
- `jmac-cornelis/agent-workforce:agents/hardware_analyst.py` (source)
- `jmac-cornelis/agent-workforce:agents/hedy/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/hedy/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/hedy/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/hedy/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/hedy/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/hedy/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/hedy/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/hedy/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/cli.py` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/nl_query.py` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/prompts/as-built-design.md` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/prompts/traceability.md` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/prompts/user-guide.md` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/tools.py` (source)
- `jmac-cornelis/agent-workforce:agents/hemingway/state/record_store.py` (source)
- `jmac-cornelis/agent-workforce:agents/herodotus/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/herodotus/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/herodotus/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/herodotus/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/herodotus/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/herodotus/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/herodotus/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/herodotus/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/humphrey/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/humphrey/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/humphrey/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/humphrey/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/humphrey/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/humphrey/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/humphrey/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/humphrey/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/jira_analyst.py` (source)
- `jmac-cornelis/agent-workforce:agents/josephine/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/josephine/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/josephine/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/josephine/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/josephine/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/josephine/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/josephine/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/josephine/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/linnaeus/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/linnaeus/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/linnaeus/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/linnaeus/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/linnaeus/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/linnaeus/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/linnaeus/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/linnaeus/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/linus/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/linus/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/linus/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/linus/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/linus/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/linus/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/linus/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/linus/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/mercator/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/mercator/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/mercator/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/mercator/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/mercator/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/mercator/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/mercator/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/mercator/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/nightingale/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/nightingale/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/nightingale/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/nightingale/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/nightingale/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/nightingale/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/nightingale/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/nightingale/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/orchestrator.py` (source)
- `jmac-cornelis/agent-workforce:agents/planning_agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/pliny/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/pliny/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/pliny/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/pliny/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/pliny/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/pliny/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/pliny/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/pliny/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/pm_runtime.py` (source)
- `jmac-cornelis/agent-workforce:agents/research_agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/rename_registry.py` (source)
- `jmac-cornelis/agent-workforce:agents/review_agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/scoping_agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/shackleton/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/shackleton/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/shackleton/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/shackleton/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/shackleton/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/shackleton/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/shackleton/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/shackleton/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/cli.py` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/cards.py` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/docs/TEAMS_BOT_FRAMEWORK.md` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/docs/as-built.md` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/docs/deployment-plan.md` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/docs/teams-setup.md` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/docs/config.md` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/docs/service.md` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/graph_client.py` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/registry.py` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/state_store.py` (source)
- `jmac-cornelis/agent-workforce:agents/shannon/service.py` (source)
- `jmac-cornelis/agent-workforce:agents/tesla/README.md` (source)
- `jmac-cornelis/agent-workforce:agents/tesla/__init__.py` (source)
- `jmac-cornelis/agent-workforce:agents/tesla/agent.py` (source)
- `jmac-cornelis/agent-workforce:agents/tesla/api.py` (source)
- `jmac-cornelis/agent-workforce:agents/tesla/config.yaml` (source)
- `jmac-cornelis/agent-workforce:agents/tesla/docs/PLAN.md` (source)
- `jmac-cornelis/agent-workforce:agents/vision_analyzer.py` (source)
- `jmac-cornelis/agent-workforce:agents/tesla/models.py` (source)
- `jmac-cornelis/agent-workforce:agents/tesla/prompts/system.md` (source)
- `jmac-cornelis/agent-workforce:config/__init__.py` (source)
- `jmac-cornelis/agent-workforce:config/claude_desktop_config.example.json` (source)
- `jmac-cornelis/agent-workforce:config/env/README.md` (source)
- `jmac-cornelis/agent-workforce:config/env_loader.py` (source)
- `jmac-cornelis/agent-workforce:config/hemingway/voice_config.yaml` (source)
- `jmac-cornelis/agent-workforce:config/jira_actor_identity_policy.yaml` (source)
- `jmac-cornelis/agent-workforce:config/identity_map.yaml` (source)
- `jmac-cornelis/agent-workforce:config/jira_identity.py` (source)
- `jmac-cornelis/agent-workforce:config/prompts/cn5000_bugs_clean.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/feature_plan_builder.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/feature_planning_orchestrator.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/hardware_analyst.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/jira_analyst.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/plan_building_instructions.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/orchestrator.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/research_agent.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/planning_agent.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/review_agent.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/scope_document_parser.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/scoping_agent.md` (source)
- `jmac-cornelis/agent-workforce:config/prompts/vision_roadmap_analysis.md` (source)
- `jmac-cornelis/agent-workforce:config/settings.py` (source)
- `jmac-cornelis/agent-workforce:config/prompts/vision_analyzer.md` (source)
- `jmac-cornelis/agent-workforce:config/shannon/agent_registry.yaml` (source)
- `jmac-cornelis/agent-workforce:core/__init__.py` (source)
- `jmac-cornelis/agent-workforce:confluence_utils.py` (source)
- `jmac-cornelis/agent-workforce:config/shannon/teams-app-manifest.template.json` (source)
- `jmac-cornelis/agent-workforce:core/evidence.py` (source)
- `jmac-cornelis/agent-workforce:core/jira_actor_policy.py` (source)
- `jmac-cornelis/agent-workforce:core/monitoring.py` (source)
- `jmac-cornelis/agent-workforce:core/queries.py` (source)
- `jmac-cornelis/agent-workforce:core/release_tracking.py` (source)
- `jmac-cornelis/agent-workforce:core/tickets.py` (source)
- `jmac-cornelis/agent-workforce:core/utils.py` (source)
- `jmac-cornelis/agent-workforce:core/reporting.py` (source)
- `jmac-cornelis/agent-workforce:daily_report.py` (source)
- `jmac-cornelis/agent-workforce:data/knowledge/cornelis_products.md` (source)
- `jmac-cornelis/agent-workforce:data/knowledge/heqing_org.json` (source)
- `jmac-cornelis/agent-workforce:data/knowledge/embedded_sw_fw_patterns.md` (source)
- `jmac-cornelis/agent-workforce:data/templates/create_story.json` (source)
- `jmac-cornelis/agent-workforce:data/knowledge/jira_conventions.md` (source)
- `jmac-cornelis/agent-workforce:data/templates/create_ticket_input.example.json` (source)
- `jmac-cornelis/agent-workforce:data/templates/create_ticket_input.schema.json` (source)
- `jmac-cornelis/agent-workforce:data/templates/epic.json` (source)
- `jmac-cornelis/agent-workforce:data/templates/task.json` (source)
- `jmac-cornelis/agent-workforce:data/templates/story.json` (source)
- `jmac-cornelis/agent-workforce:data/templates/release.json` (source)
- `jmac-cornelis/agent-workforce:deploy/README.md` (source)
- `jmac-cornelis/agent-workforce:deploy/scripts/deploy-shannon.sh` (source)
- `jmac-cornelis/agent-workforce:deploy/scripts/fix-server.sh` (source)
- `jmac-cornelis/agent-workforce:docker-compose.yml` (source)
- `jmac-cornelis/agent-workforce:docs/agent-usefulness-and-applications.md` (source)
- `jmac-cornelis/agent-workforce:docs/agent-workforce-mapping.md` (source)
- `jmac-cornelis/agent-workforce:docs/agents-drucker.md` (source)
- `jmac-cornelis/agent-workforce:docs/agent-workforce.md` (source)
- `jmac-cornelis/agent-workforce:docs/agents-gantt-prompts.md` (source)
- `jmac-cornelis/agent-workforce:docs/agents-hemingway.md` (source)
- `jmac-cornelis/agent-workforce:docs/agents-gantt.md` (source)
- `jmac-cornelis/agent-workforce:docs/agents/index.md` (source)
- `jmac-cornelis/agent-workforce:docs/config.md` (source)
- `jmac-cornelis/agent-workforce:docs/deploy-systemd.md` (source)
- `jmac-cornelis/agent-workforce:docs/index.md` (source)
- `jmac-cornelis/agent-workforce:docs/shannon.md` (source)
- `jmac-cornelis/agent-workforce:docs/installation.md` (source)
- `jmac-cornelis/agent-workforce:docs/tools.md` (source)
- `jmac-cornelis/agent-workforce:docs/tests.md` (source)
- `jmac-cornelis/agent-workforce:docs/workforce/AWS_HYBRID_DEPLOYMENT_PROPOSAL.md` (source)
- `jmac-cornelis/agent-workforce:docs/workflows.md` (source)
- `jmac-cornelis/agent-workforce:docs/workforce/DEPLOYMENT_GUIDE.md` (source)
- `jmac-cornelis/agent-workforce:docs/workforce/INFRASTRUCTURE_ARCHITECTURE.md` (source)
- `jmac-cornelis/agent-workforce:docs/workforce/JIRA_ACTOR_IDENTITY_POLICY.md` (source)
- `jmac-cornelis/agent-workforce:docs/workforce/README.md` (source)
- `jmac-cornelis/agent-workforce:docs/workforce/JIRA_EPIC_STORY_BREAKDOWN.md` (source)
- `jmac-cornelis/agent-workforce:docs/workforce/TEST_FRAMEWORK_EVALUATION.md` (source)
- `jmac-cornelis/agent-workforce:docs/workforce/ai_agents_spec_complete.md` (source)
- `jmac-cornelis/agent-workforce:docs/workforce/ai_agent_implementation_roadmap.md` (source)
- `jmac-cornelis/agent-workforce:drawio_utilities.py` (source)
- `jmac-cornelis/agent-workforce:excel_utils.py` (source)
- `jmac-cornelis/agent-workforce:fix_author.py` (source)
- `jmac-cornelis/agent-workforce:framework/api/__init__.py` (source)
- `jmac-cornelis/agent-workforce:framework/api/app.py` (source)
- `jmac-cornelis/agent-workforce:framework/api/auth.py` (source)
- `jmac-cornelis/agent-workforce:framework/api/health.py` (source)
- `jmac-cornelis/agent-workforce:framework/api/middleware.py` (source)
- `jmac-cornelis/agent-workforce:framework/api/status.py` (source)
- `jmac-cornelis/agent-workforce:framework/events/consumer.py` (source)
- `jmac-cornelis/agent-workforce:framework/events/__init__.py` (source)
- `jmac-cornelis/agent-workforce:framework/events/dead_letter.py` (source)
- `jmac-cornelis/agent-workforce:framework/events/producer.py` (source)
- `jmac-cornelis/agent-workforce:framework/events/envelope.py` (source)
- `jmac-cornelis/agent-workforce:framework/state/__init__.py` (source)
- `jmac-cornelis/agent-workforce:framework/state/audit.py` (source)
- `jmac-cornelis/agent-workforce:framework/state/tokens.py` (source)
- `jmac-cornelis/agent-workforce:framework/state/postgres.py` (source)
- `jmac-cornelis/agent-workforce:jenkins/jenkins_bug_report.sh` (source)
- `jmac-cornelis/agent-workforce:github_utils.py` (source)
- `jmac-cornelis/agent-workforce:jira_utils.py` (source)
- `jmac-cornelis/agent-workforce:llm/__init__.py` (source)
- `jmac-cornelis/agent-workforce:llm/base.py` (source)
- `jmac-cornelis/agent-workforce:llm/config.py` (source)
- `jmac-cornelis/agent-workforce:llm/cornelis_llm.py` (source)
- `jmac-cornelis/agent-workforce:llm/litellm_client.py` (source)
- `jmac-cornelis/agent-workforce:mkdocs.yml` (source)
- `jmac-cornelis/agent-workforce:mcp_server.py` (source)
- `jmac-cornelis/agent-workforce:notifications/__init__.py` (source)
- `jmac-cornelis/agent-workforce:notifications/base.py` (source)
- `jmac-cornelis/agent-workforce:notifications/jira_comments.py` (source)
- `jmac-cornelis/agent-workforce:parse_changelog.py` (source)
- `jmac-cornelis/agent-workforce:parse_changelog_v2.py` (source)
- `jmac-cornelis/agent-workforce:plans/agent-rename-execution-backlog.md` (source)
- `jmac-cornelis/agent-workforce:plans/agent-pipeline-architecture.md` (source)
- `jmac-cornelis/agent-workforce:plans/branch-pr-naming-proposal.md` (source)
- `jmac-cornelis/agent-workforce:plans/build-excel-map-architecture.md` (source)
- `jmac-cornelis/agent-workforce:plans/conversation-summary.md` (source)
- `jmac-cornelis/agent-workforce:plans/daily-report-tool-design.md` (source)
- `jmac-cornelis/agent-workforce:plans/feature-planning-agent-architecture.md` (source)
- `jmac-cornelis/agent-workforce:plans/full-workflow-fix.md` (source)
- `jmac-cornelis/agent-workforce:plans/github-pr-hygiene-proposal.md` (source)
- `jmac-cornelis/agent-workforce:plans/shannon-permanent-deployment.md` (source)
- `jmac-cornelis/agent-workforce:plans/sharing-planning-agent-via-cn-ai-tools.md` (source)
- `jmac-cornelis/agent-workforce:plans/user-resolver-design.md` (source)
- `jmac-cornelis/agent-workforce:plans/version-field-governance-proposal.md` (source)
- `jmac-cornelis/agent-workforce:plans/workflow-design-analysis.md` (source)
- `jmac-cornelis/agent-workforce:requirements.txt` (source)
- `jmac-cornelis/agent-workforce:run_bug_report.sh` (source)
- `jmac-cornelis/agent-workforce:schemas/__init__.py` (source)
- `jmac-cornelis/agent-workforce:schemas/build_record.py` (source)
- `jmac-cornelis/agent-workforce:schemas/documentation_record.py` (source)
- `jmac-cornelis/agent-workforce:schemas/release_record.py` (source)
- `jmac-cornelis/agent-workforce:schemas/meeting_summary_record.py` (source)
- `jmac-cornelis/agent-workforce:schemas/test_execution_record.py` (source)
- `jmac-cornelis/agent-workforce:schemas/traceability_record.py` (source)
- `jmac-cornelis/agent-workforce:scripts/workforce/drawio_to_png.js` (source)
- `jmac-cornelis/agent-workforce:scripts/workforce/drawio_to_mermaid.py` (source)
- `jmac-cornelis/agent-workforce:scripts/workforce/publish_teams_bot_confluence.py` (source)
- `jmac-cornelis/agent-workforce:scripts/workforce/publish_all.py` (source)
- `jmac-cornelis/agent-workforce:scripts/workforce/render_all_diagrams.py` (source)
- `jmac-cornelis/agent-workforce:scripts/workforce/reorder_plan_sections.py` (source)
- `jmac-cornelis/agent-workforce:scripts/workforce/test_teams_post.py` (source)
- `jmac-cornelis/agent-workforce:shannon/__init__.py` (source)
- `jmac-cornelis/agent-workforce:shannon/app.py` (source)
- `jmac-cornelis/agent-workforce:shannon/cards.py` (source)
- `jmac-cornelis/agent-workforce:shannon/models.py` (source)
- `jmac-cornelis/agent-workforce:shannon/outgoing_webhook.py` (source)
- `jmac-cornelis/agent-workforce:shannon/poster.py` (source)
- `jmac-cornelis/agent-workforce:shannon/notification_router.py` (source)
- `jmac-cornelis/agent-workforce:shannon/registry.py` (source)
- `jmac-cornelis/agent-workforce:shannon/service.py` (source)
- `jmac-cornelis/agent-workforce:state/__init__.py` (source)
- `jmac-cornelis/agent-workforce:state/roadmap_snapshot_store.py` (source)
- `jmac-cornelis/agent-workforce:state/persistence.py` (source)
- `jmac-cornelis/agent-workforce:state/session.py` (source)
- `jmac-cornelis/agent-workforce:template.py` (source)
- `jmac-cornelis/agent-workforce:tests/GITHUB_TEST_COVERAGE_ANALYSIS.md` (source)
- `jmac-cornelis/agent-workforce:tests/conftest.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_agent_rename_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_agents_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_confluence_search_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_confluence_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_core_queries_coverage.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_confluence_utils_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_core_reporting.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_core_tickets.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_core_utils.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_agent_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_api_github_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_github_polling_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_cli_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_learning_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_drucker_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_utils_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_dry_run_mcp_messaging_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_env_loader_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_evidence_contracts_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_excel_utils_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_excel_utils_coverage.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_feature_planning_orchestrator_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_file_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_gantt_agent_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_gantt_cli_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_gantt_components_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_gantt_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_docs_search_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_integration_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_phase5_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_phase5_integration_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_utils_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_api_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_github_write_ops_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_agent_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_confluence_publish_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_cli_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_pr_review_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_search_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_shannon_cards_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_jira_actor_policy_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_jira_identity_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_hemingway_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_jira_utils_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_jira_tools_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_jira_utils_coverage.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_markdown_to_confluence.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_confluence_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_coverage.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_drucker_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_gantt_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_github_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_hemingway_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_notifications_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_release_tracking.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_shannon_pr_cards_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_shannon_dry_run_flow_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_shannon_service_char.py` (source)
- `jmac-cornelis/agent-workforce:tests/test_smoke.py` (source)
- `jmac-cornelis/agent-workforce:tools/__init__.py` (source)
- `jmac-cornelis/agent-workforce:tools/base.py` (source)
- `jmac-cornelis/agent-workforce:tools/confluence_tools.py` (source)
- `jmac-cornelis/agent-workforce:tools/drawio_tools.py` (source)
- `jmac-cornelis/agent-workforce:tools/file_tools.py` (source)
- `jmac-cornelis/agent-workforce:tools/excel_tools.py` (source)
- `jmac-cornelis/agent-workforce:tools/github_tools.py` (source)
- `jmac-cornelis/agent-workforce:tools/jira_tools.py` (source)
- `jmac-cornelis/agent-workforce:tools/knowledge_tools.py` (source)
- `jmac-cornelis/agent-workforce:tools/mcp_tools.py` (source)
- `jmac-cornelis/agent-workforce:tools/plan_export_tools.py` (source)
- `jmac-cornelis/agent-workforce:tools/vision_tools.py` (source)
- `jmac-cornelis/agent-workforce:tools/web_search_tools.py` (source)

## Key Facts

### Source: `jmac-cornelis/agent-workforce:AGENTS.md`
- AGENTS.md
- This file provides guidance to agents when working with code in this repository.
- Build & Test
- **Venv**: `.venv/bin/python` / `.venv/bin/pytest` — always use the venv, no global installs.
- **Install**: `pip install -e ".[agents,test]"` — core deps are minimal; agent pipeline and test deps are optional extras.
- **Run all tests**: `.venv/bin/pytest -q`
- **Run single test**: `.venv/bin/pytest tests/test_drucker_agent_char.py::test_drucker_agent_builds_hygiene_report_and_actions -q`
- **Syntax check**: `python -m py_compile <module.py>` on touched files before committing.
- No linter/formatter config exists (no ruff, flake8, black, mypy). Rely on existing code style.
- Code Style (Discovered)

### Source: `jmac-cornelis/agent-workforce:STOPPED_HERE_shannon_notifications.md`
- Shannon Notifications — Stopped Here
- **Branch**: shannon-notifications
- **Date**: 2026-04-04
- **Status**: Code complete, blocked on Azure AD admin consent
- What Was Built
- New Files
- shannon/notification_router.py — Multi-channel notification dispatcher (Teams DM + email)
- Modified Files
- | File | Change |
- |------|--------|

### Source: `jmac-cornelis/agent-workforce:.github/workflows/tests.yml`
- name: Tests & Coverage
- pull_request:
- branches: [main, master]
- branches: [main, master, refactor-jira-utils]
- concurrency:
- group: pages-deploy-${{ github.head_ref || github.ref_name }}
- cancel-in-progress: true
- permissions:
- contents: write
- checks: write

### Source: `jmac-cornelis/agent-workforce:.github/workflows/docs.yml`
- name: Deploy Documentation
- branches: [main]
- 'docs/**'
- 'agents/*/README.md'
- 'mkdocs.yml'
- '.github/workflows/docs.yml'
- workflow_dispatch:
- permissions:
- contents: write
- runs-on: ubuntu-latest

### Source: `jmac-cornelis/agent-workforce:README.md`
- Cornelis Agent Workforce
- AI-powered engineering agents, reusable tools, and standalone CLI utilities for project management, Jira, Confluence, Excel, and Draw.io at Cornelis Networks.
- Table of Contents
- [Overview](#overview)
- [When to Use What](#when-to-use-what)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Agents](#agents)
- [Implemented Agents](#implemented-agents)
- [Agent Communication](#agent-communication)

### Source: `jmac-cornelis/agent-workforce:.sisyphus/plans/12.2-release-cockpit-recommendations.md`
- 12.2 Release Cockpit — Unified Recommendations
- **Date:** 2026-03-25
- **Author:** John Macdonald
- **Status:** Draft
- **Inputs:** Live Jira survey (2026-03-25) + STL_12_2_RELEASE_COCKPIT_BLUEPRINT.md
- **Scope:** Trustworthy release cockpit for `12.2.0.x` spanning CN5000 and CN6000
- 0. Why This Document
- Two independent analyses of the `12.2.0.x` release produced overlapping but distinct findings:
- **Analysis A** (live Jira survey): Data-heavy. Found 267 tickets via broad `fixVersion` query, quantified the CN6000 gap (319 unversioned), found wrong fixVersions on SW Release trackers, cataloged 582 unversioned open bugs, inventoried existing automation tooling.
- **Analysis B** (cockpit blueprint): Model-heavy. Found 100 tickets via scoped query (fixVersion + labels/Product Family), identified hierarchy defects (8 orphan stories, 3 multi-release feature tickets, 2 stale epics), defined canonical Jira data model, operating rules, and ownership model.

### Source: `jmac-cornelis/agent-workforce:.sisyphus/plans/12.2-release-status-page.md`
- 12.2 Release Status Page — Plan
- **Date:** 2026-03-25
- **Author:** John Macdonald
- **Status:** Draft
- **Scope:** Create a comprehensive release status view for 12.2.0.x covering both CN5000 and CN6000
- 1. Background
- Release 12.2.0.x is an active unreleased software suite spanning the full Cornelis stack (firmware, drivers, middleware, tools, fabric manager) for both the CN5000 (JKR/Jericho) and CN6000 (CYR/Cyrus) product families. All work is tracked in Jira project STL (STLSW).
- Current State (as of 2026-03-25)
- | Metric | CN5000 | CN6000 | Total |
- |--------|--------|--------|-------|

### Source: `jmac-cornelis/agent-workforce:.github/workflows/doc-generation.yml`
- GitHub Action: Hemingway Documentation Generation
- Copy this workflow to any repo that should get auto-generated docs.
- Requires: HEMINGWAY_API_URL secret (optional — defaults to https://hemingway.cn-agents.com)
- PR opened/updated → Hemingway generates docs → commits to PR branch →
- sets hemingway/documentation status to pending → posts full content in PR comment.
- PR review approved → sets status to success → merge unblocked.
- name: Generate Documentation
- pull_request:
- types: [opened, synchronize]
- pull_request_review:

### Source: `jmac-cornelis/agent-workforce:TODO.md`
- Testing Summary
- The `agent-credentials` changes are fully green in the repo's automated tests.
- Full-suite result:
- .venv/bin/pytest -q
- 770 passed, 18 warnings
- Focused validation was also run for:
- Jira identity resolution
- Jira actor policy
- Jira utils and dry-run Jira tools
- Drucker review flow

### Source: `jmac-cornelis/agent-workforce:adapters/__init__.py`
- adapters — External system integration interfaces.
- Each sub-package exposes an ABC interface and a skeleton concrete implementation
- for one external system consumed by the AI Agent Workforce.
- Sub-packages:
- github — GitHub REST API (PRs, status checks, inline comments, webhooks)
- teams — Microsoft Teams / Graph API (messages, adaptive cards, transcripts)
- fuze — Fuze build/test CLI wrapper (builds, artifacts, test execution)
- environment — Test environment manager (ATF resource files, HIL/mock racks)
- NOTE: The Jira adapter already exists in this repository:
- jira_utils.py (top-level utility module)

### Source: `jmac-cornelis/agent-workforce:adapters/environment/__init__.py`
- """Environment adapter — test environment management (ATF resource files)."""
- from .adapter import EnvironmentAdapter, ATFResourceAdapter
- __all__ = ["EnvironmentAdapter", "ATFResourceAdapter"]

### Source: `jmac-cornelis/agent-workforce:adapters/fuze/adapter.py`
- Fuze build/test system adapter interface and CLI implementation skeleton.
- Provides:
- FuzeAdapter — ABC defining the Fuze integration surface.
- FuzeCLIAdapter — Concrete skeleton wrapping the Fuze CLI.
- from abc import ABC, abstractmethod
- from typing import Any
- class FuzeAdapter(ABC):
- """Interface for the Fuze build/test system.
- Fuze is the source of build configuration truth and internal build identity.
- This adapter covers build submission, status polling, artifact retrieval,

### Source: `jmac-cornelis/agent-workforce:adapters/fuze/__init__.py`
- """Fuze adapter — build/test system CLI wrapper."""
- from .adapter import FuzeAdapter, FuzeCLIAdapter
- __all__ = ["FuzeAdapter", "FuzeCLIAdapter"]

### Source: `jmac-cornelis/agent-workforce:adapters/github/__init__.py`
- """GitHub adapter — PR events, status checks, review comments, webhooks."""
- from .adapter import PREvent, GitHubAdapter, GitHubRESTAdapter
- __all__ = ["PREvent", "GitHubAdapter", "GitHubRESTAdapter"]

### Source: `jmac-cornelis/agent-workforce:adapters/environment/adapter.py`
- Test environment adapter interface and ATF resource file implementation skeleton.
- Provides:
- EnvironmentAdapter — ABC defining the environment management surface.
- ATFResourceAdapter — Concrete skeleton that parses ATF resource files.
- from abc import ABC, abstractmethod
- from typing import Any
- class EnvironmentAdapter(ABC):
- """Interface for test environment management.
- Exposes HIL rack availability, hardware identity, capability matrices,
- and health status. Backed by ATF resource files or a scheduling service.

### Source: `jmac-cornelis/agent-workforce:adapters/github/adapter.py`
- GitHub adapter interface and REST implementation skeleton.
- Provides:
- PREvent — Pydantic model for pull request webhook payloads.
- GitHubAdapter — ABC defining the GitHub integration surface.
- GitHubRESTAdapter — Concrete skeleton that calls the GitHub REST API.
- from abc import ABC, abstractmethod
- from pydantic import BaseModel, Field
- class PREvent(BaseModel):
- """Normalized pull-request event received from a GitHub webhook."""
- pr_number: int = Field(..., description="Pull request number")

### Source: `jmac-cornelis/agent-workforce:adapters/github/webhook.py`
- """GitHub webhook receiver — verifies HMAC-SHA256 signatures, parses events, publishes to event bus."""
- import hashlib
- import hmac
- import logging
- from typing import Any
- from fastapi import APIRouter, Request, HTTPException, Header
- from .adapter import PREvent
- logger = logging.getLogger(__name__)
- webhook_router = APIRouter(tags=["github-webhook"])
- _webhook_secret: str | None = None

### Source: `jmac-cornelis/agent-workforce:adapters/teams/__init__.py`
- """Teams adapter — messages, adaptive cards, transcripts via Microsoft Graph."""
- from .adapter import TeamsAdapter, TeamsGraphAdapter
- __all__ = ["TeamsAdapter", "TeamsGraphAdapter"]

### Source: `jmac-cornelis/agent-workforce:agents/README.md`
- Agent Workforce
- The Cornelis Networks Agent Workforce is a system of 17 specialized agents that automate and coordinate the full software development lifecycle. Each agent owns a distinct responsibility — from build orchestration and test generation to release management and project planning — and communicates through well-defined interfaces.
- Agents are organized into operational zones. Four agents are currently implemented and running; the remaining thirteen are planned with full technical specifications.
- Agents by Zone
- Execution Spine
- Core build-test-release pipeline agents.
- | Agent | Role | Status | Port | Description |
- |-------|------|--------|------|-------------|
- | [Josephine](josephine/README.md) | Build & Package | Planned | 8210 | Build orchestration and artifact production via Fuze |
- | [Galileo](galileo/README.md) | Test Planning | Planned | 8211 | Determines what to test based on trigger class, coverage, and environment |

### Source: `jmac-cornelis/agent-workforce:adapters/teams/adapter.py`
- Microsoft Teams adapter interface and Graph API implementation skeleton.
- Provides:
- TeamsAdapter — ABC defining the Teams integration surface.
- TeamsGraphAdapter — Concrete skeleton using Microsoft Graph API.
- from abc import ABC, abstractmethod
- from typing import Any
- class TeamsAdapter(ABC):
- """Interface for Microsoft Teams integration.
- Covers channel messaging, adaptive cards, threaded replies,
- and meeting transcript retrieval.

### Source: `jmac-cornelis/agent-workforce:agents/ada/README.md`
- Ada — Test Planner
- > Status: Planned
- Overview
- Ada is the test-planning agent for the platform. It decides what should be tested and at what depth based on build context, trigger type, environment state, and coverage needs. Ada produces a durable `TestPlan` that downstream agents (Curie and Faraday) act on.
- In the test pipeline: Ada decides what to test, Curie materializes executable test content, Faraday executes it, and Tesla manages environment reservations.
- Responsibilities
- Consume build-trigger events and determine test scope
- Select test suites and depth based on trigger class (PR, merge, nightly, release)
- Factor in environment constraints and availability from Tesla
- Produce structured `TestPlan` records for Curie

### Source: `jmac-cornelis/agent-workforce:agents/ada/__init__.py`
- Module: agents/workforce/ada/__init__.py
- Description: Ada Test Planner Agent package.
- Author: Cornelis Networks
- from agents.ada.agent import AdaAgent
- __all__ = ['AdaAgent']

### Source: `jmac-cornelis/agent-workforce:agent_cli.py`
- !/usr/bin/env python3
- Script name: agent_cli.py
- Description: Unified CLI entry point for the Cornelis Agent Workforce.
- Thin subcommand router that mounts per-agent CLIs and
- houses unique cross-agent orchestration workflows.
- Author: Cornelis Networks
- agent-cli drucker hygiene -p STL
- agent-cli gantt snapshot -p STL
- agent-cli bug-report -p STL --filter-name "My Filter"
- agent-cli llm --prompt "Analyze this" --attachments report.pdf

### Source: `jmac-cornelis/agent-workforce:agents/__init__.py`
- Module: agents
- Description: Agent definitions for Cornelis Agent Pipeline.
- Provides specialized agents for release planning workflow.
- Author: Cornelis Networks
- from agents.base import BaseAgent, AgentConfig, AgentResponse
- from agents.drucker.agent import DruckerCoordinatorAgent
- from agents.drucker.models import (
- DruckerAction,
- DruckerFinding,
- DruckerHygieneReport,

### Source: `jmac-cornelis/agent-workforce:agents/ada/api.py`
- Module: agents/workforce/ada/api.py
- Description: FastAPI router for the Ada Test Planner Agent.
- Exposes test plan selection, retrieval, and event endpoints.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter, HTTPException
- from typing import Any, Dict
- from agents.ada.models import TestPlanRequest, TestPlan
- router = APIRouter(prefix='/v1/test-plans', tags=['ada'])
- @router.post('/select', response_model=Dict[str, Any])

### Source: `jmac-cornelis/agent-workforce:agents/ada/config.yaml`
- Ada Test Planner Agent Configuration
- Author: Cornelis Networks
- agent_id: ada
- display_name: Ada
- zone: execution_spine
- phase: 2
- description: >
- Test Planner Agent. Determines what to test based on trigger class
- (PR, merge, nightly, release), coverage targets, and environment
- constraints. Produces durable TestPlan records for downstream agents.

### Source: `jmac-cornelis/agent-workforce:agents/ada/docs/PLAN.md`
- Ada Test Planner Plan
- Ada should be the test-planning agent for the platform. Its v1 job is to turn build context, trigger type, environment state, and coverage needs into a durable `TestPlan` that downstream test agents can act on.
- In practical terms:
- Ada decides what should be tested and at what depth
- Curie materializes that plan into concrete Fuze Test inputs
- Faraday executes the plan through Fuze Test
- Tesla manages scarce environment reservations
- Ada should use Fuze Test in [atf](/Users/johnmacdonald/code/cornelis/atf) as the planning vocabulary and downstream execution substrate, but Ada itself should not own low-level execution or reservation logic.
- Product definition
- consume build completion events from Josephine

### Source: `jmac-cornelis/agent-workforce:agents/ada/agent.py`
- Module: agents/workforce/ada/agent.py
- Description: Ada Test Planner Agent.
- Determines what to test based on trigger class, coverage targets,
- and environment constraints. Produces durable TestPlan records.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/ada/models.py`
- Module: agents/workforce/ada/models.py
- Description: Data models for the Ada Test Planner Agent.
- Defines test plan requests, plans, coverage summaries,
- and planning policy decisions.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime, timezone
- from enum import Enum
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field

### Source: `jmac-cornelis/agent-workforce:agents/ada/prompts/system.md`
- Ada — Test Planner Agent
- You are Ada, the Test Planner Agent for the Cornelis Networks Execution Spine. Your role is to turn build context, trigger type, environment state, and coverage needs into durable TestPlan records that downstream test agents (Curie, Faraday, Tesla) can act on.
- You use Fuze Test as the planning vocabulary and downstream execution substrate. You do not own low-level execution, environment reservation, or test generation — those belong to Faraday, Tesla, and Curie respectively.
- When planning, optimize PR plans for fast signal and low lab contention, merge plans for increased realism, nightly plans for breadth, and release validation plans for auditability. Prioritize deterministic tool use over LLM inference.

### Source: `jmac-cornelis/agent-workforce:agents/babbage/README.md`
- Babbage — Version Manager
- > Status: Planned
- Overview
- Babbage is the version-mapping agent for the platform. It connects internal build identity from Fuze with external release versions and maintains the lineage between the two. Josephine produces internal build IDs, Hedy decides release intent, and Babbage maps between them as a durable record.
- Responsibilities
- Map internal Fuze build IDs to external customer-facing version strings
- Detect and prevent version mapping conflicts
- Maintain lineage and audit trail for all version assignments
- Serve version lookups for other agents (Hedy, Linnaeus, Hemingway)
- Track version progression across branches and release trains

### Source: `jmac-cornelis/agent-workforce:agents/babbage/__init__.py`
- Module: agents/workforce/babbage/__init__.py
- Description: Babbage Version Manager agent package.
- Author: Cornelis Networks
- from agents.babbage.agent import BabbageAgent
- __all__ = ['BabbageAgent']

### Source: `jmac-cornelis/agent-workforce:agents/babbage/agent.py`
- Module: agents/workforce/babbage/agent.py
- Description: Babbage Version Manager agent.
- Maps internal Fuze build IDs to external customer-facing release
- versions with conflict detection and lineage tracking.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/babbage/api.py`
- Module: agents/workforce/babbage/api.py
- Description: FastAPI router for the Babbage Version Manager agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter
- from agents.babbage.models import (
- VersionMappingRequest,
- VersionMappingRecord,
- router = APIRouter(prefix='/v1/version-mappings', tags=['babbage'])
- @router.post('/', response_model=VersionMappingRecord)

### Source: `jmac-cornelis/agent-workforce:agents/babbage/config.yaml`
- Babbage Version Manager Agent Configuration
- Cornelis Networks
- agent_id: babbage
- agent_name: Babbage Version Manager
- zone: intelligence
- phase: 3
- description: >
- Maps internal Fuze build IDs to external customer-facing release versions
- with conflict detection and lineage tracking.
- temperature: 0.3

### Source: `jmac-cornelis/agent-workforce:agents/babbage/models.py`
- Module: agents/workforce/babbage/models.py
- Description: Pydantic models for the Babbage Version Manager agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class VersionMappingRequest(BaseModel):
- '''Request to map an internal build ID to an external version.'''
- build_id: str = Field(..., description='Internal Fuze build identifier (FuzeID)')

### Source: `jmac-cornelis/agent-workforce:agents/babbage/docs/PLAN.md`
- Babbage Version Manager Plan
- Babbage should be the version-mapping agent for the platform. Its v1 job is to connect internal build identity from `fuze` with external release versions and maintain the lineage between the two.
- In practical terms:
- Josephine produces the internal build identity
- Hedy decides release intent and scope
- Babbage maps internal build IDs to external versions and preserves that mapping as a durable record
- Babbage should not replace `fuze`'s internal identity model. It should build a controlled mapping layer on top of it.
- Product definition
- map internal Fuze build identities to external release versions
- maintain deterministic version lineage over time

### Source: `jmac-cornelis/agent-workforce:agents/babbage/prompts/system.md`
- Babbage — Version Manager Agent
- You are Babbage, the Version Manager agent for the Cornelis Networks Agent Workforce.
- You map internal Fuze build identities (FuzeID) to external customer-facing release versions. You maintain deterministic version lineage, detect mapping conflicts, and preserve compatibility and supersession records.
- Responsibilities
- Map internal build IDs to external version proposals
- Support forward and reverse version lookups
- Detect and surface version collisions and ambiguity
- Record replacement and supersession relationships
- Require confirmation for risky or ambiguous mappings
- One internal build ID may map to one or more scoped external versions only if policy explicitly allows target-specific variation.

### Source: `jmac-cornelis/agent-workforce:agents/base.py`
- Module: agents/base.py
- Description: Base classes for agent definitions.
- Provides common functionality for all agents in the pipeline.
- Author: Cornelis Networks
- import json
- import logging
- import os
- import re
- import sys
- from abc import ABC, abstractmethod

### Source: `jmac-cornelis/agent-workforce:agents/bernerslee/README.md`
- Berners-Lee — Traceability Agent
- > Status: Planned
- Overview
- Berners-Lee is the traceability agent for the platform. It maintains exact, queryable relationships between requirements, Jira issues, commits, builds, test executions, releases, and external version mappings.
- Berners-Lee is not a vague reporting layer. It is the system that establishes and serves relationship facts.
- Responsibilities
- Consume identity-bearing events from Jira, GitHub, Josephine, Faraday, Humphrey, and Mercator
- Maintain a structured traceability graph linking requirements to releases
- Serve traceability queries for any agent or human
- Detect traceability gaps (untested commits, unlinked builds, orphaned requirements)

### Source: `jmac-cornelis/agent-workforce:agents/bernerslee/__init__.py`
- Module: agents/bernerslee/__init__.py
- Description: Berners-Lee Traceability agent package.
- Author: Cornelis Networks
- from typing import Any
- __all__ = ['BernersLeeAgent', 'LinnaeusAgent']
- def __getattr__(name: str) -> Any:
- if name in ('BernersLeeAgent', 'LinnaeusAgent'):
- from agents.bernerslee.agent import BernersLeeAgent, LinnaeusAgent
- if name == 'BernersLeeAgent':
- return BernersLeeAgent

### Source: `jmac-cornelis/agent-workforce:agents/bernerslee/agent.py`
- Module: agents/bernerslee/agent.py
- Description: Berners-Lee Traceability agent.
- Maintains exact, queryable relationships between requirements,
- Jira issues, commits, builds, tests, releases, and versions.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/bernerslee/config.yaml`
- agent_id: bernerslee
- agent_name: Berners-Lee Traceability
- zone: intelligence
- phase: 3
- description: >
- Maintains exact queryable relationships between requirements, Jira issues,
- commits, builds, tests, releases, and external version mappings.
- temperature: 0.3
- max_tokens: 4096
- max_iterations: 10

### Source: `jmac-cornelis/agent-workforce:agents/bernerslee/api.py`
- Module: agents/bernerslee/api.py
- Description: FastAPI router for the Berners-Lee Traceability agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from typing import Optional
- from fastapi import APIRouter
- from agents.bernerslee.models import TraceAssertion
- router = APIRouter(prefix='/v1/trace', tags=['bernerslee'])
- @router.post('/assert', response_model=TraceAssertion)
- async def assert_trace(source_type: str, source_id: str, target_type: str,

### Source: `jmac-cornelis/agent-workforce:agents/bernerslee/models.py`
- Module: agents/bernerslee/models.py
- Description: Pydantic models for the Berners-Lee Traceability agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class TraceabilityRecord(BaseModel):
- '''A stored traceability record linking two system entities.'''
- record_id: str = Field(..., description='Unique traceability record identifier')

### Source: `jmac-cornelis/agent-workforce:agents/blackstone/README.md`
- Blackstone — Legal Compliance & Code Scanning
- > Status: Planned
- Overview
- Blackstone is the legal compliance and code scanning agent. Named after William Blackstone, whose Commentaries helped codify and explain the common law, it scans dependencies for license compliance, flags policy violations on pull requests, and manages license exception workflows.
- Responsibilities
- Scan repository dependencies for license compliance
- Flag license policy violations on PRs via status checks
- Maintain an approved license allowlist and exception registry
- Generate compliance reports per repository or release
- Coordinate license exception approvals with legal stakeholders

### Source: `jmac-cornelis/agent-workforce:agents/bernerslee/docs/PLAN.md`
- Berners-Lee Traceability Agent Plan
- Berners-Lee should be the traceability agent for the platform. Its v1 job is to maintain exact, queryable relationships between requirements, Jira issues, commits, builds, test executions, releases, and external version mappings.
- Berners-Lee should not become a vague reporting layer. It should be the system that establishes and serves relationship facts.
- Namesake
- Berners-Lee is named for Tim Berners-Lee, the inventor of the World Wide Web, who showed how information becomes far more useful when it is linked, navigable, and addressable. We use his name for the traceability agent because Berners-Lee's job is to create and serve the links between requirements, issues, builds, tests, releases, and documents.
- Product definition
- consume identity-bearing events from Jira, GitHub, Josephine, Faraday, Humphrey, Mercator, and project artifacts
- resolve and persist exact links between technical and workflow records
- expose trace views that humans and other agents can query reliably
- push narrow, evidence-backed traceability updates back into Jira where useful

### Source: `jmac-cornelis/agent-workforce:agents/bernerslee/prompts/system.md`
- Berners-Lee — Traceability Agent
- You are Berners-Lee, the Traceability agent for the Cornelis Networks Agent Workforce.
- You maintain exact, queryable relationships between requirements, Jira issues, commits, builds, tests, releases, and external version mappings. You are the authoritative relationship graph.
- Responsibilities
- Consume identity-bearing events from Jira, GitHub, Josephine, Faraday, Humphrey, and Mercator
- Resolve and persist exact links between technical and workflow records
- Expose trace views that humans and other agents can query reliably
- Push narrow, evidence-backed traceability updates back into Jira where useful
- Detect coverage gaps where traceability chains are incomplete
- Every stored relationship names the source record, target record, edge type, confidence, and evidence source.

### Source: `jmac-cornelis/agent-workforce:agents/blackstone/__init__.py`
- Module: agents/blackstone/__init__.py
- Description: Blackstone Legal Compliance agent package placeholder.
- Author: Cornelis Networks
- __all__ = []

### Source: `jmac-cornelis/agent-workforce:agents/blackstone/prompts/system.md`
- Blackstone — Legal Compliance & Code Scanning Agent
- You are Blackstone, the Legal Compliance and Code Scanning agent for the Cornelis Networks Agent Workforce. You are named after William Blackstone, the English jurist whose Commentaries made legal rules durable, explainable, and easier to apply consistently.
- You own software composition analysis, license compliance, regulatory scanning, and legal-risk governance across the engineering delivery pipeline. You ensure that what ships is legally clean, license-compatible, and compliant with organizational and regulatory policy.
- Responsibilities
- Orchestrate and interpret BlackDuck (Synopsys) scan results for open-source license compliance and known vulnerabilities
- Maintain a current software bill of materials (SBOM) for tracked products and releases
- Evaluate license compatibility across dependency trees and flag conflicts before they reach release gates
- Surface regulatory compliance gaps (export control, FIPS, FedRAMP, or sector-specific requirements) relevant to the product
- Produce structured compliance reports that Humphrey can consume as release-readiness evidence
- Track remediation status for flagged findings and coordinate with Drucker for Jira-backed tracking

### Source: `jmac-cornelis/agent-workforce:agents/blackstone/docs/PLAN.md`
- title: "Blackstone \u2014 Legal Compliance & Code Scanning Agent"
- space: ~712020daf767ace9e14880b27724add0de7116
- page_id: '670498836'
- **Zone:** Execution Spine | **Status:** Wave 5 | **Sprint:** S8–S9
- Overview
- Blackstone is the legal compliance and code scanning agent for the platform. Named after William Blackstone, the English jurist whose Commentaries made legal rules durable, explainable, and easier to apply consistently.
- Its v1 job is to orchestrate software composition analysis scans (BlackDuck / Synopsys), interpret results for license compliance and known vulnerabilities, maintain a software bill of materials (SBOM), and produce structured compliance evidence that Humphrey can consume as a release gate input.
- Blackstone is not a generic security scanner or a vulnerability-only tool. It focuses on the legal and regulatory compliance surface: license compatibility, export control, FIPS/FedRAMP requirements, and SBOM accuracy. Humans remain the approval authority for license exceptions and regulatory waivers.
- Namesake
- Blackstone is named for William Blackstone, the eighteenth-century English jurist whose Commentaries organized the common law into a durable, understandable body of rules. We use his name for the compliance agent because Blackstone turns messy policy, licensing, and regulatory obligations into clear, reviewable rules that can be applied consistently before software ships.

### Source: `jmac-cornelis/agent-workforce:agents/blackstone/config.yaml`
- Blackstone Legal Compliance & Code Scanning Agent Configuration
- Author: Cornelis Networks
- agent_id: blackstone
- display_name: Blackstone
- zone: execution_spine
- phase: 5
- description: >
- Legal Compliance and Code Scanning Agent. Orchestrates license and
- regulatory compliance scans, tracks remediation and exception flow,
- and produces release-gating evidence for downstream agents.

### Source: `jmac-cornelis/agent-workforce:agents/brandeis/prompts/system.md`
- Brandeis — Legal Compliance & Code Scanning Agent
- You are Brandeis, the Legal Compliance and Code Scanning agent for the Cornelis Networks Agent Workforce. You are named after Louis Brandeis, the Supreme Court Justice who championed transparency, regulatory reform, and the principle that "sunlight is the best disinfectant."
- You own software composition analysis, license compliance, regulatory scanning, and legal-risk governance across the engineering delivery pipeline. You ensure that what ships is legally clean, license-compatible, and compliant with organizational and regulatory policy.
- Responsibilities
- Orchestrate and interpret BlackDuck (Synopsys) scan results for open-source license compliance and known vulnerabilities
- Maintain a current software bill of materials (SBOM) for tracked products and releases
- Evaluate license compatibility across dependency trees and flag conflicts before they reach release gates
- Surface regulatory compliance gaps (export control, FIPS, FedRAMP, or sector-specific requirements) relevant to the product
- Produce structured compliance reports that Hedy can consume as release-readiness evidence
- Track remediation status for flagged findings and coordinate with Drucker for Jira-backed tracking

### Source: `jmac-cornelis/agent-workforce:agents/brandeis/docs/PLAN.md`
- title: "Brandeis \u2014 Legal Compliance & Code Scanning Agent"
- space: ~712020daf767ace9e14880b27724add0de7116
- page_id: '670498836'
- **Zone:** Execution Spine | **Status:** Wave 5 | **Sprint:** S8–S9
- Overview
- Brandeis is the legal compliance and code scanning agent for the platform. Named after Louis Brandeis, the Supreme Court Justice who championed transparency, regulatory reform, and the principle that “sunlight is the best disinfectant.”
- Its v1 job is to orchestrate software composition analysis scans (BlackDuck / Synopsys), interpret results for license compliance and known vulnerabilities, maintain a software bill of materials (SBOM), and produce structured compliance evidence that Hedy can consume as a release gate input.
- Brandeis is not a generic security scanner or a vulnerability-only tool. It focuses on the legal and regulatory compliance surface: license compatibility, export control, FIPS/FedRAMP requirements, and SBOM accuracy. Humans remain the approval authority for license exceptions and regulatory waivers.
- Components
- Component

### Source: `jmac-cornelis/agent-workforce:agents/brooks/README.md`
- Brooks — Delivery Manager
- > Status: Planned
- Overview
- Brooks is the delivery-management agent for the platform. It monitors execution against plan, detects schedule risk and coordination failures early, and produces operational delivery summaries for humans. Gantt plans; Brooks watches delivery reality and flags drift, blockage, and risk.
- Responsibilities
- Monitor work-in-flight against milestones and release targets
- Detect schedule risk from blocked dependencies, stale work, and velocity changes
- Produce operational delivery summaries and status reports
- Flag coordination failures between teams or agents
- Track delivery metrics over time for trend analysis

### Source: `jmac-cornelis/agent-workforce:agents/brandeis/README.md`
- Brandeis — Legal Compliance & Code Scanning
- > Status: Planned
- Overview
- Brandeis is the legal compliance and code scanning agent. Named after Louis Brandeis, champion of transparency and the right to privacy, it scans dependencies for license compliance, flags policy violations on pull requests, and manages license exception workflows.
- Responsibilities
- Scan repository dependencies for license compliance
- Flag license policy violations on PRs via status checks
- Maintain an approved license allowlist and exception registry
- Generate compliance reports per repository or release
- Coordinate license exception approvals with legal stakeholders

### Source: `jmac-cornelis/agent-workforce:agents/brooks/agent.py`
- Module: agents/workforce/brooks/agent.py
- Description: Brooks Delivery Manager agent.
- Monitors execution against plan, detects schedule risk and
- coordination failures, produces forecasts and escalation prompts.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/brooks/__init__.py`
- Module: agents/workforce/brooks/__init__.py
- Description: Brooks Delivery Manager agent package.
- Author: Cornelis Networks
- from agents.brooks.agent import BrooksAgent
- __all__ = ['BrooksAgent']

### Source: `jmac-cornelis/agent-workforce:agents/brooks/config.yaml`
- agent_id: brooks
- agent_name: Brooks Delivery Manager
- zone: planning
- phase: 6
- description: >
- Monitors execution against plan, detects schedule risk and coordination
- failures, produces forecasts and escalation prompts.
- temperature: 0.3
- max_tokens: 4096
- max_iterations: 10

### Source: `jmac-cornelis/agent-workforce:agents/brooks/api.py`
- Module: agents/workforce/brooks/api.py
- Description: FastAPI router for the Brooks Delivery Manager agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter
- router = APIRouter(prefix='/v1/delivery', tags=['brooks'])
- @router.post('/snapshot')
- async def create_delivery_snapshot(project_key: str):
- '''Create a delivery snapshot combining Jira and technical evidence.'''
- raise NotImplementedError('Brooks API not yet implemented')

### Source: `jmac-cornelis/agent-workforce:agents/brooks/docs/PLAN.md`
- Brooks Delivery Manager Plan
- Brooks should be the delivery-management agent for the platform. Its v1 job is to monitor execution against plan, detect schedule risk and coordination failure early, and produce operational delivery summaries for humans.
- Brooks should not own project planning itself. Gantt plans; Brooks watches delivery reality and flags drift, blockage, and risk.
- Product definition
- monitor work-in-flight against milestones and release targets
- correlate project status with technical evidence from builds, tests, releases, and traceability
- surface delivery risk, slip probability, blocked handoffs, and missing approvals
- make status reporting fast, current, and evidence-backed
- Non-goals for v1
- replacing Jira as the task system

### Source: `jmac-cornelis/agent-workforce:agents/brooks/prompts/system.md`
- Brooks — Delivery Manager Agent
- You are Brooks, the Delivery Manager agent for the Cornelis Networks Agent Workforce.
- You monitor execution against plan, detect schedule risk and coordination failure early, and produce operational delivery summaries for humans. Gantt plans; you watch delivery reality and flag drift, blockage, and risk.
- Responsibilities
- Monitor work-in-flight against milestones and release targets
- Correlate project status with technical evidence from builds, tests, releases, and traceability
- Surface delivery risk, slip probability, blocked handoffs, and missing approvals
- Make status reporting fast, current, and evidence-backed
- Status claims must always be tied to observable evidence.
- "On track" requires both work-state and technical-state support.

### Source: `jmac-cornelis/agent-workforce:agents/brooks/models.py`
- Module: agents/workforce/brooks/models.py
- Description: Pydantic models for the Brooks Delivery Manager agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class DeliverySnapshot(BaseModel):
- '''Point-in-time delivery status combining Jira and technical evidence.'''
- snapshot_id: str = Field(..., description='Unique snapshot identifier')

### Source: `jmac-cornelis/agent-workforce:agents/curie/README.md`
- Curie — Test Generator
- > Status: Planned
- Overview
- Curie is the test-generation agent for the platform. It takes Ada's `TestPlan` and turns it into concrete Fuze Test runtime inputs that Faraday can execute through Fuze Test in ATF. Ada defines the testing intent; Curie materializes executable test content and runtime inputs.
- Responsibilities
- Consume Ada's `TestPlan` and resolve it into executable test inputs
- Generate Fuze Test configuration files and runtime parameters
- Produce reproducible version hashes for test content
- Handle test parameterization based on environment and hardware constraints from Tesla
- Maintain a registry of available test suites and their capabilities

### Source: `jmac-cornelis/agent-workforce:agents/curie/__init__.py`
- Module: agents/workforce/curie/__init__.py
- Description: Curie Test Generator Agent package.
- Author: Cornelis Networks
- from agents.curie.agent import CurieAgent
- __all__ = ['CurieAgent']

### Source: `jmac-cornelis/agent-workforce:agents/curie/api.py`
- Module: agents/workforce/curie/api.py
- Description: FastAPI router for the Curie Test Generator Agent.
- Exposes test input generation, retrieval, and artifact endpoints.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter, HTTPException
- from typing import Any, Dict
- router = APIRouter(prefix='/v1/test-inputs', tags=['curie'])
- @router.post('/generate', response_model=Dict[str, Any])
- async def generate_test_inputs(request: Dict[str, Any]) -> Dict[str, Any]:

### Source: `jmac-cornelis/agent-workforce:agents/curie/agent.py`
- Module: agents/workforce/curie/agent.py
- Description: Curie Test Generator Agent.
- Materializes Ada's TestPlan into concrete Fuze Test runtime
- inputs that Faraday can execute.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/curie/config.yaml`
- Curie Test Generator Agent Configuration
- Author: Cornelis Networks
- agent_id: curie
- display_name: Curie
- zone: execution_spine
- phase: 2
- description: >
- Test Generator Agent. Materializes Ada's TestPlan into concrete Fuze Test
- runtime inputs — explicit suite lists, runtime overlays, and DUT filters —
- that Faraday can execute reproducibly.

### Source: `jmac-cornelis/agent-workforce:agents/curie/docs/PLAN.md`
- Curie Test Generator Plan
- Curie should be the test-generation agent for the platform. Its v1 job is to take Ada's `TestPlan` and turn it into concrete Fuze Test runtime inputs that Faraday can execute through Fuze Test in [atf](/Users/johnmacdonald/code/cornelis/atf).
- In practical terms:
- Ada defines the testing intent
- Curie materializes executable test content and runtime inputs
- Faraday executes the result
- Tesla supplies environment constraints where required
- Curie should not invent a new low-level execution model. It should target the Fuze Test model that already exists.
- Namesake
- Curie is named for Marie Curie, the pioneering physicist and chemist whose laboratory work turned difficult scientific questions into disciplined experiments and reproducible results. We use her name for the test-generation agent because Curie takes a high-level test plan and materializes it into concrete executable inputs that a lab system can actually run.

### Source: `jmac-cornelis/agent-workforce:agents/curie/prompts/system.md`
- Curie — Test Generator Agent
- You are Curie, the Test Generator Agent for the Cornelis Networks Execution Spine. Your role is to take Ada's TestPlan and turn it into concrete Fuze Test runtime inputs that Faraday can execute through ATF.
- You produce explicit suite lists, runtime overlays, and DUT filters without mutating repo-tracked ATF config. All generated inputs are ephemeral, auditable artifacts tied to a specific build_id and test_plan_id. Generated inputs must be deterministic for the same planning inputs and policy version.
- Prioritize deterministic tool use over LLM inference. Prefer explicit suite lists over committed config mutation, and runtime overlays over source edits.

### Source: `jmac-cornelis/agent-workforce:agents/curie/models.py`
- Module: agents/workforce/curie/models.py
- Description: Data models for the Curie Test Generator Agent.
- Defines generated test inputs, suite resolution records,
- and generation decision records.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime, timezone
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class SuiteResolutionRecord(BaseModel):

### Source: `jmac-cornelis/agent-workforce:agents/drucker/README.md`
- Drucker Engineering Hygiene Agent
- Overview
- The Drucker Engineering Hygiene Agent is the most feature-rich implemented agent. It automates Jira ticket hygiene and GitHub pull request lifecycle management, ensuring compliance and visibility across engineering workflows.
- Quick Start
- The Drucker Agent monitors Jira and GitHub to ensure tickets and pull requests adhere to engineering standards. It operates in a safe, dry-run mode by default, allowing you to preview changes before execution.
- You can interact with Drucker through Teams chat (via `@Shannon`), REST API endpoints, or CLI commands.
- Dry-Run Safety
- **All mutation operations default to dry-run mode.** This means Drucker will report on findings but will not modify Jira tickets or GitHub PRs unless explicitly instructed.
- To override dry-run mode and execute changes:
- **Shannon:** Append `execute` to the command.

### Source: `jmac-cornelis/agent-workforce:agents/drucker/agent.py`
- Module: agents/drucker_agent.py
- Description: Drucker Jira Coordinator agent.
- Produces deterministic Jira hygiene reports, ticket-level
- remediation suggestions, and review-gated Jira write-back plans.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- import time

### Source: `jmac-cornelis/agent-workforce:agents/drucker/api.py`
- from __future__ import annotations
- import logging
- import os
- import sys
- from datetime import datetime, timezone
- from typing import Any, Dict, List, Optional
- from config.env_loader import load_env
- load_env()
- from fastapi import FastAPI, HTTPException, Query
- from pydantic import BaseModel

### Source: `jmac-cornelis/agent-workforce:agents/drucker/cards.py`
- Module: agents/drucker/cards.py
- Description: Adaptive Card builders for Drucker PR reminder DMs. Constructs
- interactive cards for snooze, merge, and confirmation flows
- delivered via Teams direct messages.
- Author: Cornelis Networks
- from __future__ import annotations
- from typing import Any, Dict, List, Optional
- ---------------------------------------------------------------------------
- Schema constant shared by all cards
- _CARD_SCHEMA = 'http://adaptivecards.io/schemas/adaptive-card.json'

### Source: `jmac-cornelis/agent-workforce:agents/drucker/config/monitor.yaml`
- project: ''
- poll_interval_minutes: 5
- validation_rules:
- required:
- assignee
- fix_versions
- components
- description
- priority
- learning:

### Source: `jmac-cornelis/agent-workforce:agents/drucker/config/polling.yaml`
- defaults:
- project_key: ''
- limit: 200
- include_done: false
- stale_days: 30
- label_prefix: drucker
- persist: true
- notify_shannon: true
- github_stale_days: 5
- github_repos:

### Source: `jmac-cornelis/agent-workforce:agents/drucker/cli.py`
- Module: agents/drucker/cli.py
- Description: Standalone CLI for Drucker Engineering Hygiene agent.
- Provides direct access to Jira project hygiene scans, single-ticket
- issue checks, intake reports, bug activity summaries, GitHub PR
- hygiene analysis, and scheduled polling.
- Author: Cornelis Networks
- from __future__ import annotations
- import argparse
- import json
- import logging

### Source: `jmac-cornelis/agent-workforce:agents/drucker/config/pr_reminders.yaml`
- defaults:
- reminder_days: [5, 8, 10, 15]
- notify: [author, reviewers]
- channels: [teams_dm]
- snooze_options_days: [2, 5, 7]
- merge_methods: [squash, merge, rebase]
- enabled: true
- repo: jmac-cornelis/agent-workforce
- reminder_days: [3, 5, 8, 12]
- repo: cornelisnetworks/ifs-all

### Source: `jmac-cornelis/agent-workforce:agents/drucker/docs/PLAN.md`
- Drucker Engineering Hygiene Agent Plan
- Drucker should be the engineering hygiene agent for both Jira workflow coordination and GitHub PR lifecycle management for the platform. Its v1 Jira job is to keep Jira operationally coherent: triage incoming issues, enforce workflow hygiene, route work to the right owners or queues, and apply evidence-backed status nudges based on build, test, release, and traceability signals. For GitHub, it scans PRs for staleness, missing reviews, and lifecycle issues.
- Drucker should not replace Jira or GitHub as systems of record. It should make both cleaner, more current, and more trustworthy.
- Namesake
- Drucker is named for Peter Drucker, the management thinker who focused on making knowledge work visible, measurable, and effective. We use his name for the engineering hygiene agent because Drucker identifies drift, missing structure, and workflow breakdowns, then helps the organization operate with more clarity and discipline.
- Product definition
- consume Jira issue events and scheduled hygiene checks
- consume GitHub PR state from configured repositories via scheduled polling
- detect missing required metadata, stale workflow state, and routing mistakes
- detect stale PRs, missing review requests, and PR lifecycle anomalies

### Source: `jmac-cornelis/agent-workforce:agents/drucker/docs/as-built.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Drucker Engineering Hygiene Agent"
- date: "2026-04-08"
- status: "draft"
- Drucker Engineering Hygiene Agent — Design Reference
- 1. Module Overview
- The Drucker Engineering Hygiene Agent is a deterministic-first automation system that monitors Jira ticket quality and GitHub pull request lifecycle health across the Cornelis Networks engineering organization. Named after management theorist Peter Drucker, the agent identifies workflow drift, missing metadata, stale work, and routing mistakes in both Jira and GitHub, then produces actionable hygiene reports with review-gated remediation proposals. Drucker operates in dry-run mode by default, ensuring all mutation operations are previewed before execution. It exposes a REST API (port 8201), integrates with the Shannon Teams bot for interactive commands, and runs scheduled polling jobs for continuous hygiene monitoring. The agent is the most feature-rich implemented agent in the workforce, combining Jira ticket validation, GitHub PR staleness detection, PR reminder DMs via Teams, natural language query translation, and a learning subsystem that observes ticket-intake patterns to suggest metadata for new issues.
- 2. What Changed
- Drucker was a Jira-only hygiene agent with three core workflows: full project hygiene scans, single-ticket intake validation, and recent-ticket intake reports.
- GitHub PR hygiene was a planned feature but not implemented.

### Source: `jmac-cornelis/agent-workforce:agents/drucker/docs/config.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Drucker Agent Configuration"
- date: "2026-04-08"
- status: "draft"
- Module Overview
- The Drucker agent configuration module consists of three YAML configuration files that control automated project management hygiene monitoring across Jira and GitHub. The `polling.yaml` file defines scheduled jobs for scanning Jira tickets and GitHub pull requests, `monitor.yaml` specifies validation rules for different Jira issue types, and `pr_reminders.yaml` configures reminder schedules for stale pull requests. Together, these configurations enable the Drucker agent to monitor 23+ Cornelis Networks repositories, validate ticket hygiene, detect stale work, and send automated notifications through Teams channels and direct messages.
- What Changed
- **Before:** The configuration included test repositories (`jmac-cornelis/agent-workforce`, `cornelisnetworks/opa-psm3`) in the default GitHub repository list. The `github-hygiene-scan` and `github-extended-scan` jobs were disabled (`enabled: false`). The `github-pr-reminders` job included the test repository in its monitored repos list.
- **After:** Test repositories have been removed from all repository lists in `polling.yaml`. Both GitHub hygiene scan jobs are now enabled (`enabled: true`), activating stale PR detection, missing review checks, naming convention validation, merge conflict detection, and stale branch monitoring. The `github-pr-reminders` job no longer monitors test repositories.
- **Impact:** The Drucker agent now actively monitors only production repositories for hygiene issues. GitHub hygiene scans will run on schedule, generating notifications for stale PRs (>5 days), missing reviews, and other issues. PR reminder notifications will be sent to authors and reviewers at 3, 7, and 14-day intervals for production repositories only. Teams will receive more focused notifications without test repository noise.

### Source: `jmac-cornelis/agent-workforce:agents/drucker/docs/docs.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Drucker Engineering Hygiene Agent"
- date: "2026-04-08"
- status: "draft"
- Drucker Engineering Hygiene Agent — Design Reference
- Module Overview
- Drucker is a deterministic-first engineering hygiene agent that monitors Jira ticket quality and GitHub pull request lifecycle health across the Cornelis Networks organization. Named after management theorist Peter Drucker, the agent identifies workflow drift, missing metadata, stale work, and routing mistakes in both Jira and GitHub, then produces actionable hygiene reports with review-gated remediation proposals. Drucker operates in dry-run mode by default, ensuring all mutation operations are previewed before execution. It exposes a REST API (port 8201), integrates with the Shannon Teams bot for interactive commands, and runs scheduled polling jobs for continuous hygiene monitoring. The agent combines Jira ticket validation, GitHub PR staleness detection, PR reminder DMs via Teams, natural language query translation, and a learning subsystem that observes ticket-intake patterns to suggest metadata for new issues.
- What Changed
- Drucker was a Jira-only hygiene agent with three core workflows: full project hygiene scans, single-ticket intake validation, and recent-ticket intake reports.
- GitHub PR hygiene was a planned feature but not implemented.

### Source: `jmac-cornelis/agent-workforce:agents/drucker/models.py`
- Module: agents/drucker_models.py
- Description: Data models for the Drucker Jira Coordinator agent.
- Defines hygiene findings, proposed Jira actions, and durable
- project hygiene reports.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- import uuid

### Source: `jmac-cornelis/agent-workforce:agents/drucker/jira_reporting.py`
- Module: agents/drucker/jira_reporting.py
- Description: Jira query and status reporting utilities for Drucker. Wraps jira_utils
- functions with ticket normalization and breakdown computation.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from collections import Counter
- from datetime import datetime, timezone

### Source: `jmac-cornelis/agent-workforce:agents/drucker/docs/state.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Drucker State Layer"
- date: "2026-04-03"
- status: "draft"
- Module Overview
- The `agents/drucker/state/` package provides the persistence layer for the Drucker agent — a Jira hygiene and PR review automation system within the Cornelis Networks agent workforce. The package contains five SQLite-backed and filesystem-backed stores, each responsible for a distinct domain of durable state: API request activity counters, ticket-intake learning patterns, intake-monitor checkpoints, PR reminder lifecycle tracking, and hygiene report artifact storage. Every SQLite store follows a consistent architectural pattern — thread-safe access via `threading.RLock`, `sqlite3.Row`-based row factories, `check_same_thread=False` connections, automatic parent-directory creation, and an explicit `close()` lifecycle method. The filesystem store (`DruckerReportStore`) persists JSON and Markdown report artifacts to a configurable directory tree. Together, these stores give Drucker durable, crash-recoverable state without requiring an external database server.
- What Changed
- **Before:** The state layer consisted of three stores: `DruckerLearningStore` (keyword/reporter pattern learning), `DruckerMonitorState` (intake checkpoint tracking), and `DruckerReportStore` (hygiene report persistence).
- **After:** Two new SQLite stores were added: `ActivityCounter` for tracking per-category API request and error counts with timestamps, and `PRReminderState` for managing the full PR reminder lifecycle including scheduling, snoozing, unsnoozing, and action history.
- **Impact:** Drucker now has observability into its own API usage patterns via `ActivityCounter`, and can autonomously track and escalate stale pull requests via `PRReminderState`. Consumers of the Drucker API (e.g., the `pr-reminders` and activity/status endpoints) depend on these new stores. Existing stores (`DruckerLearningStore`, `DruckerMonitorState`, `DruckerReportStore`) are unchanged.

### Source: `jmac-cornelis/agent-workforce:agents/drucker/nl_query.py`
- Module: agents/drucker/nl_query.py
- Description: Natural language query translation for Drucker. Uses LLM function calling
- to convert plain English questions into structured Jira tool calls, execute
- them, and summarize results.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/drucker/pr_reminders.py`
- Module: agents/drucker/pr_reminders.py
- Description: Core PR reminder engine. Orchestrates repo scanning, reminder
- scheduling, Teams user resolution, DM delivery via Graph API,
- and snooze / merge action handling.
- Author: Cornelis Networks
- from __future__ import annotations
- import asyncio
- import logging
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/drucker/prompts/system.md`
- Drucker Engineering Hygiene Agent
- You are Drucker, an engineering hygiene agent specialized in project hygiene across Jira and GitHub, operational coherence, and review-gated write-back.
- Your Role
- You examine engineering project state across Jira and GitHub and produce:
- 1. Project-level hygiene summaries (Jira tickets and GitHub PRs)
- 2. Ticket-level and PR-level findings with evidence
- 3. Suggested remediation actions
- 4. Safe, reviewable Jira write-back plans
- 5. GitHub PR lifecycle notifications (stale PRs, missing reviews)
- Operating Principles

### Source: `jmac-cornelis/agent-workforce:agents/drucker/state/activity_counter.py`
- Module: state/activity_counter.py
- Description: SQLite-backed persistent counter for all Drucker API request activity.
- Tracks request counts, error counts, and first/last timestamps by
- endpoint category (hygiene, jira, github, nl, pr-reminders).
- Author: Cornelis Networks
- from __future__ import annotations
- import sqlite3
- import threading
- from datetime import datetime, timezone
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/drucker/state/learning_store.py`
- Module: state/drucker_learning_store.py
- Description: Drucker-owned learning store for ticket-intake suggestions.
- Tracks keyword/component patterns, reporter field habits, and
- basic observation history for review-gated metadata suggestions.
- Author: Cornelis Networks
- from __future__ import annotations
- import hashlib
- import json
- import logging
- import os

### Source: `jmac-cornelis/agent-workforce:agents/drucker/state/monitor_state.py`
- Module: state/drucker_monitor_state.py
- Description: Checkpoint and processed-ticket persistence for Drucker intake
- monitoring. Tracks recent polling cursors and validation history
- without performing any Jira writes.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import sqlite3
- import threading
- from datetime import datetime, timezone

### Source: `jmac-cornelis/agent-workforce:agents/drucker/state/report_store.py`
- Module: state/drucker_report_store.py
- Description: Persistence helpers for Drucker hygiene reports.
- Stores durable JSON + Markdown artifacts for Jira hygiene analysis.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys
- from datetime import datetime

### Source: `jmac-cornelis/agent-workforce:agents/drucker/state/pr_reminder_state.py`
- Module: state/pr_reminder_state.py
- Description: SQLite state store for PR reminder tracking. Manages reminder
- scheduling, snooze state, and action history for pull requests
- that need reviewer attention.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import sqlite3
- import threading
- from datetime import datetime, timezone

### Source: `jmac-cornelis/agent-workforce:agents/drucker/tools.py`
- Module: tools/drucker_tools.py
- Description: Drucker hygiene tools for agent use.
- Wraps the Drucker hygiene workflow as agent-callable tools.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from typing import Optional
- from tools.base import BaseTool, ToolResult, tool
- Logging config - follows jira_utils.py pattern

### Source: `jmac-cornelis/agent-workforce:agents/faraday/README.md`
- Faraday — Test Executor
- > Status: Planned
- Overview
- Faraday is the test-execution agent for the platform. It takes a resolved `TestPlan`, acquires the required environment through Tesla, executes the plan through Fuze Test in ATF, collects results, and publishes machine-readable test execution records tied to the originating build ID.
- In v1, Faraday wraps the existing Fuze Test execution path rather than replacing the ATF executive or Product Test Adapter layers.
- Responsibilities
- Consume concrete TestPlans from Curie
- Acquire test environments through Tesla reservations
- Execute ATF/Fuze Test cycles with proper isolation
- Capture logs, artifacts, and test results

### Source: `jmac-cornelis/agent-workforce:agents/faraday/__init__.py`
- Module: agents/workforce/faraday/__init__.py
- Description: Faraday Test Executor Agent package.
- Author: Cornelis Networks
- from agents.faraday.agent import FaradayAgent
- __all__ = ['FaradayAgent']

### Source: `jmac-cornelis/agent-workforce:agents/faraday/agent.py`
- Module: agents/workforce/faraday/agent.py
- Description: Faraday Test Executor Agent.
- Runs ATF/Fuze Test cycles, captures results and artifacts,
- classifies failures, and produces TestExecutionRecords.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/faraday/api.py`
- Module: agents/workforce/faraday/api.py
- Description: FastAPI router for the Faraday Test Executor Agent.
- Exposes test run creation, cancellation, status, and result endpoints.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter, HTTPException
- from typing import Any, Dict
- from agents.faraday.models import TestRunRequest
- router = APIRouter(prefix='/v1/test-runs', tags=['faraday'])
- @router.post('', response_model=Dict[str, Any])

### Source: `jmac-cornelis/agent-workforce:agents/faraday/docs/PLAN.md`
- Faraday Test Executor Plan
- Faraday should be the test-execution agent for the platform. Its job is to take a resolved `TestPlan`, acquire the required environment through Tesla, execute the plan through Fuze Test in [atf](/Users/johnmacdonald/code/cornelis/atf), collect results, and publish machine-readable test execution records tied to the originating build ID.
- In v1, Faraday should wrap the existing Fuze Test execution path rather than replacing the ATF executive or Product Test Adapter layers.
- Namesake
- Faraday is named for Michael Faraday, one of history's great experimental scientists, famous for careful apparatus work and for turning theory into repeatable demonstrations. We use his name for the test-execution agent because Faraday is where planned experiments meet the real world: environments are bound, runs are executed, and evidence is captured.
- Product definition
- consume a concrete `TestPlan`
- validate or bind the required environment reservation
- invoke Fuze Test execution reliably
- capture normalized results, raw artifacts, and status events

### Source: `jmac-cornelis/agent-workforce:agents/faraday/config.yaml`
- Faraday Test Executor Agent Configuration
- Author: Cornelis Networks
- agent_id: faraday
- display_name: Faraday
- zone: execution_spine
- phase: 2
- description: >
- Test Executor Agent. Runs ATF/Fuze Test cycles, captures logs, artifacts,
- and results, classifies failures, and produces structured
- TestExecutionRecords tied to the originating build ID.

### Source: `jmac-cornelis/agent-workforce:agents/faraday/models.py`
- Module: agents/workforce/faraday/models.py
- Description: Data models for the Faraday Test Executor Agent.
- Defines test run requests, execution records, failure records,
- and environment reservation references.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime, timezone
- from enum import Enum
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field

### Source: `jmac-cornelis/agent-workforce:agents/faraday/prompts/system.md`
- Faraday — Test Executor Agent
- You are Faraday, the Test Executor Agent for the Cornelis Networks Execution Spine. Your role is to take resolved TestPlans, acquire environments through Tesla, execute tests through Fuze Test/ATF, collect results, and publish machine-readable TestExecutionRecords.
- You wrap the existing Fuze Test execution path rather than replacing the ATF executive or Product Test Adapter layers. You classify failures accurately into distinct categories: bad request, missing artifacts, reservation failure, ATF config failure, PTA failure, DUT failure, timeout, and infrastructure loss.
- Prioritize deterministic tool use over LLM inference. Never start a HIL test run without a valid Tesla reservation. Ensure every run reaches a clear terminal state.

### Source: `jmac-cornelis/agent-workforce:agents/feature_plan_builder.py`
- Module: agents/feature_plan_builder.py
- Description: Feature Plan Builder Agent for the Feature Planning pipeline.
- Converts a FeatureScope into a concrete Jira project plan with
- Epics and Stories, ready for human review and execution.
- The plan is produced entirely by the LLM via a ReAct loop.
- The agent sends the scoped work items as a structured prompt
- and the LLM returns a JSON plan conforming to the JiraPlan
- schema. There is no deterministic fallback — the LLM is the
- authoritative plan builder.
- Author: Cornelis Networks

### Source: `jmac-cornelis/agent-workforce:agents/feature_planning_models.py`
- Module: agents/feature_planning_models.py
- Description: Data models for the Feature Planning Agent pipeline.
- Defines structured types for research findings, hardware profiles,
- scope items, and Jira plans used across all feature planning agents.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from dataclasses import dataclass, field
- from typing import Any, Dict, List, Optional

### Source: `jmac-cornelis/agent-workforce:agents/feature_planning_orchestrator.py`
- Module: agents/feature_planning_orchestrator.py
- Description: Feature Planning Orchestrator Agent.
- Coordinates the end-to-end feature-to-Jira workflow:
- Research → Hardware Analysis → Scoping → Plan Building → Review → Execute.
- Author: Cornelis Networks
- import json
- import logging
- import os
- import re
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/galileo/README.md`
- Galileo — Test Planner
- > Status: Planned
- Overview
- Galileo is the test-planning agent for the platform. It decides what should be tested and at what depth based on build context, trigger type, environment state, and coverage needs. Galileo produces a durable `TestPlan` that downstream agents (Curie and Faraday) act on.
- In the test pipeline: Galileo decides what to test, Curie materializes executable test content, Faraday executes it, and Tesla manages environment reservations.
- Responsibilities
- Consume build-trigger events and determine test scope
- Select test suites and depth based on trigger class (PR, merge, nightly, release)
- Factor in environment constraints and availability from Tesla
- Produce structured `TestPlan` records for Curie

### Source: `jmac-cornelis/agent-workforce:agents/galileo/__init__.py`
- Module: agents/galileo/__init__.py
- Description: Galileo Test Planner Agent package.
- Author: Cornelis Networks
- from typing import Any
- __all__ = ['GalileoAgent', 'AdaAgent']
- def __getattr__(name: str) -> Any:
- if name in ('GalileoAgent', 'AdaAgent'):
- from agents.galileo.agent import GalileoAgent, AdaAgent
- if name == 'GalileoAgent':
- return GalileoAgent

### Source: `jmac-cornelis/agent-workforce:agents/galileo/api.py`
- Module: agents/galileo/api.py
- Description: FastAPI router for the Galileo Test Planner Agent.
- Exposes test plan selection, retrieval, and event endpoints.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter, HTTPException
- from typing import Any, Dict
- from agents.galileo.models import TestPlanRequest, TestPlan
- router = APIRouter(prefix='/v1/test-plans', tags=['galileo'])
- @router.post('/select', response_model=Dict[str, Any])

### Source: `jmac-cornelis/agent-workforce:agents/galileo/agent.py`
- Module: agents/galileo/agent.py
- Description: Galileo Test Planner Agent.
- Determines what to test based on trigger class, coverage targets,
- and environment constraints. Produces durable TestPlan records.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/galileo/config.yaml`
- Galileo Test Planner Agent Configuration
- Author: Cornelis Networks
- agent_id: galileo
- display_name: Galileo
- zone: execution_spine
- phase: 2
- description: >
- Test Planner Agent. Determines what to test based on trigger class
- (PR, merge, nightly, release), coverage targets, and environment
- constraints. Produces durable TestPlan records for downstream agents.

### Source: `jmac-cornelis/agent-workforce:agents/galileo/prompts/system.md`
- Galileo — Test Planner Agent
- You are Galileo, the Test Planner Agent for the Cornelis Networks Execution Spine. Your role is to turn build context, trigger type, environment state, and coverage needs into durable TestPlan records that downstream test agents (Curie, Faraday, Tesla) can act on.
- You use Fuze Test as the planning vocabulary and downstream execution substrate. You do not own low-level execution, environment reservation, or test generation — those belong to Faraday, Tesla, and Curie respectively.
- When planning, optimize PR plans for fast signal and low lab contention, merge plans for increased realism, nightly plans for breadth, and release validation plans for auditability. Prioritize deterministic tool use over LLM inference.

### Source: `jmac-cornelis/agent-workforce:agents/galileo/models.py`
- Module: agents/galileo/models.py
- Description: Data models for the Galileo Test Planner Agent.
- Defines test plan requests, plans, coverage summaries,
- and planning policy decisions.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime, timezone
- from enum import Enum
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field

### Source: `jmac-cornelis/agent-workforce:agents/galileo/docs/PLAN.md`
- Galileo Test Planner Plan
- Galileo should be the test-planning agent for the platform. Its v1 job is to turn build context, trigger type, environment state, and coverage needs into a durable `TestPlan` that downstream test agents can act on.
- In practical terms:
- Galileo decides what should be tested and at what depth
- Curie materializes that plan into concrete Fuze Test inputs
- Faraday executes the plan through Fuze Test
- Tesla manages scarce environment reservations
- Galileo should use Fuze Test in [atf](/Users/johnmacdonald/code/cornelis/atf) as the planning vocabulary and downstream execution substrate, but Galileo itself should not own low-level execution or reservation logic.
- Namesake
- Galileo is named for Galileo Galilei, the Italian mathematician and natural philosopher who helped establish experiment and measurement as the right way to test claims about the physical world. We use his name for the test-planning agent because Galileo decides what should be tested, at what depth, and with what evidence, turning intuition into an explicit experimental plan.

### Source: `jmac-cornelis/agent-workforce:agents/gantt/README.md`
- Gantt: Project Planner Agent
- Overview
- Gantt is the project planning agent for the Cornelis Networks platform. Its job is to provide clear, evidence-backed planning recommendations by analyzing your Jira work state alongside actual technical progress.
- Rather than replacing human project managers, Gantt makes planning highly visible and data-driven. It connects work items to real-world evidence from builds, tests, and releases to produce milestone proposals, dependency maps, and risk signals.
- Gantt treats Jira as the source of truth for work tracking. It reads your Jira epics, stories, bugs, priorities, and workflow states, then cross-references them with evidence from other agents across the platform to help you plan with confidence.
- Quick Start
- Gantt runs as an on-demand planning service. You can interact with it through the Shannon Teams bot or via its REST API.
- If you want to run Gantt locally for testing:
- Using Docker
- docker compose up gantt

### Source: `jmac-cornelis/agent-workforce:agents/gantt/agent.py`
- Module: agents/gantt_agent.py
- Description: Gantt Project Planner Agent.
- Produces evidence-backed planning snapshots, milestone proposals,
- dependency views, and planning-risk summaries from Jira data.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/gantt/api.py`
- from __future__ import annotations
- import logging
- import os
- import sys
- import tempfile
- from datetime import datetime, timezone
- from pathlib import Path
- from typing import Any, Dict, List, Optional
- from config.env_loader import load_env
- load_env()

### Source: `jmac-cornelis/agent-workforce:agents/gantt/cli.py`
- Module: agents/gantt/cli.py
- Description: Standalone CLI for Gantt Project Planner agent.
- Provides direct access to planning snapshots, release monitoring,
- release surveys, and scheduled polling.
- Author: Cornelis Networks
- from __future__ import annotations
- import argparse
- import json
- import logging
- import os

### Source: `jmac-cornelis/agent-workforce:agents/gantt/components.py`
- Module: agents/gantt_components.py
- Description: Deterministic planning components used by the Gantt Project Planner.
- Splits backlog interpretation, dependency mapping, milestone planning,
- risk projection, and summary formatting into reusable units.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import re
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/gantt/docs/PLAN.md`
- Gantt Project Planner Plan
- Gantt should be the project-planning agent for the platform. Its v1 job is to convert Jira work state, technical evidence, release intent, and meeting-derived decisions into structured planning outputs: milestone proposals, dependency views, backlog recommendations, and roadmap health signals.
- Gantt should not replace human program ownership. It should make planning legible, current, and evidence-backed.
- Namesake
- Gantt is named for Henry Gantt, the engineer and management consultant whose chart became one of the most recognizable tools in project planning. We use his name for the project planner because Gantt turns work, dependencies, and schedule intent into a planning view that humans can inspect and act on.
- Product definition
- consume Jira issue state and project structure
- incorporate delivery evidence from Josephine, Hedy, Babbage, Linnaeus, and the test agents
- produce planning recommendations that connect work items to actual technical progress
- expose milestone, dependency, and schedule-risk views

### Source: `jmac-cornelis/agent-workforce:agents/gantt/docs/PM_IMPLEMENTATION_BACKLOG.md`
- Gantt + Drucker PM Implementation Backlog
- > **Generated**: 2026-03-25
- > **Source branch evaluated**: `project-manager-agents`
- > **Scope**: Planning & Delivery implementation backlog for `Gantt` and `Drucker`
- This backlog turns the current evaluation into an execution plan for the Planning & Delivery slice of the agent workforce.
- The governing decisions are:
- 1. We are building a full-fledged set of project management agents, not a collection of one-off utilities.
- 2. `Gantt` and `Drucker` are the enduring PM agent products. `release_tracker` and `ticket_monitor` are harvest sources, not permanent top-level agent identities.
- 3. Both agents must support two execution modes:
- `one-shot`: explicit task execution from UI or API

### Source: `jmac-cornelis/agent-workforce:agents/gantt/docs/as-built.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Gantt Project Planner Agent"
- date: "2026-04-06"
- status: "draft"
- Module Overview
- Gantt is the project-planning agent for the Cornelis Networks agent workforce platform. It reads Jira backlogs — epics, stories, bugs, priorities, assignees, and workflow states — and cross-references them with technical evidence from builds, tests, and releases to produce durable planning artifacts: **planning snapshots**, **release health monitor reports**, **release execution surveys**, **roadmap gap analyses**, and **dependency graphs**. The agent is deterministic-first: specialized planner components (`BacklogInterpreter`, `DependencyMapper`, `MilestonePlanner`, `RiskProjector`, `PlanningSummarizer`) handle the core logic without LLM calls, while an optional LLM path is used only for roadmap gap analysis and the new natural-language query interface. Gantt is accessible through a FastAPI REST API (port 8202), a standalone CLI (`gantt-agent`), the unified `agent-cli`, and the Shannon Teams bot.
- What Changed
- **Before:** Planning snapshots, release monitors, and release surveys stored their output but did not preserve the JQL queries used to generate them. Confluence integration for release survey Jira macros was implemented inline with hardcoded XHTML generation.
- **After:** All three report types (`PlanningSnapshot`, `ReleaseMonitorReport`, `ReleaseSurveyReport`) now include a `jql_queries: List[str]` field that captures the exact JQL used to query Jira. The `_build_release_ticket_jql()` method was extracted from `_query_release_tickets()` to enable JQL collection without executing queries. Confluence Jira macro generation now delegates to the shared `confluence_utils.build_jira_jql_table_macro()` function with a fallback to inline XHTML if the utility is unavailable.
- **Impact:** Stored reports are now fully reproducible — users can re-run the exact same JQL to verify or update results. Confluence integration is centralized and consistent across agents. The change is backward-compatible: existing reports without `jql_queries` will have an empty list.

### Source: `jmac-cornelis/agent-workforce:agents/gantt/models.py`
- Module: agents/gantt_models.py
- Description: Data models for the Gantt Project Planner and Roadmap Analyzer agents.
- Defines structured planning snapshot, milestone, dependency,
- and risk records used by the Gantt planning workflow, plus
- roadmap request, item, gap, section, and snapshot models
- used by the roadmap analysis workflow.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os

### Source: `jmac-cornelis/agent-workforce:agents/gantt/docs/prompts.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Gantt Agent System Prompt"
- date: "2026-04-06"
- status: "draft"
- Module Overview
- The Gantt agent system prompt defines the behavior, capabilities, and output formats for a project-planning AI agent that transforms Jira work state into actionable planning intelligence. The prompt establishes strict rules for roadmap analysis, release monitoring, bug tracking separation, and Confluence page generation while grounding all recommendations in observable project data rather than speculation.
- What Changed
- **Before:** The prompt did not include comprehensive guidance for generating roadmap and release health pages with proper separation of bug tickets from development tickets.
- **After:** Added a complete "Roadmap & Release Health Page Generation" section (lines 321-445) that:
- Enforces strict separation between bug tickets and development tickets in all analysis

### Source: `jmac-cornelis/agent-workforce:agents/gantt/nl_query.py`
- Module: agents/gantt/nl_query.py
- Description: Natural language query translation for Gantt. Uses LLM function calling
- to convert plain English questions into structured Gantt tool calls, execute
- them, and summarize results.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/gantt/prompts/system.md`
- Gantt Project Planner Agent
- You are Gantt, the project-planning agent for Cornelis Networks.
- Your job is to turn Jira work state into planning intelligence that humans can
- review and act on. Focus on:
- 1. Planning snapshots
- 2. Milestone proposals
- 3. Dependency visibility
- 4. Roadmap and backlog risk signals
- Core Rules
- Jira remains the system of record.

### Source: `jmac-cornelis/agent-workforce:agents/gantt/state/dependency_review_store.py`
- Module: state/gantt_dependency_review_store.py
- Description: Persistence helpers for dependency inference review decisions.
- Stores accepted/rejected judgments for inferred Gantt dependencies.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys
- from datetime import datetime, timezone

### Source: `jmac-cornelis/agent-workforce:agents/gantt/state/release_monitor_store.py`
- Module: state/gantt_release_monitor_store.py
- Description: Persistence helpers for Gantt release-monitor reports.
- Stores durable JSON + Markdown artifacts and optionally copies
- the generated xlsx output file alongside the stored report.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import shutil

### Source: `jmac-cornelis/agent-workforce:agents/gantt/state/release_survey_store.py`
- Module: state/gantt_release_survey_store.py
- Description: Persistence helpers for Gantt release-survey reports.
- Stores durable JSON + Markdown artifacts and optionally copies
- the generated xlsx output file alongside the stored survey.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import shutil

### Source: `jmac-cornelis/agent-workforce:agents/gantt/state/snapshot_store.py`
- Module: state/gantt_snapshot_store.py
- Description: Persistence helpers for Gantt planning snapshots.
- Stores durable JSON + Markdown snapshot artifacts and supports
- retrieval/listing for later review.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/gantt/tools.py`
- Module: tools/gantt_tools.py
- Description: Gantt planning tools for agent use.
- Wraps the Gantt planning snapshot workflow as agent-callable tools.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from typing import Optional
- from tools.base import BaseTool, ToolResult, tool
- Logging config - follows jira_utils.py pattern

### Source: `jmac-cornelis/agent-workforce:agents/hardware_analyst.py`
- Module: agents/hardware_analyst.py
- Description: Hardware Analyst Agent for the Feature Planning pipeline.
- Builds a deep understanding of the target Cornelis hardware product
- by querying Jira, knowledge base, MCP, and GitHub.
- Author: Cornelis Networks
- import json
- import logging
- import os
- import re
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/hedy/README.md`
- Hedy — Release Manager
- > Status: Planned
- Overview
- Hedy is the release-management agent for the platform. It takes build facts from Josephine, version facts from Babbage, test evidence from the test agents, and traceability context from Linnaeus, then turns those inputs into controlled release decisions and release-state transitions.
- Hedy uses Fuze's existing release model as the underlying release engine. In v1, it orchestrates and governs release mechanics rather than replacing them.
- Responsibilities
- Evaluate release readiness across branch, hardware, customer, and policy context
- Orchestrate stage promotion (sit, qa, release) with human approval gates
- Track release-state transitions with full audit trail
- Enforce release policies (test coverage thresholds, known-issue limits)

### Source: `jmac-cornelis/agent-workforce:agents/hedy/agent.py`
- Module: agents/workforce/hedy/agent.py
- Description: Hedy Release Manager Agent.
- Orchestrates release decisions using the Fuze release model
- with stage promotion (sit, qa, release) and human approval gates.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/hedy/__init__.py`
- Module: agents/workforce/hedy/__init__.py
- Description: Hedy Release Manager Agent package.
- Author: Cornelis Networks
- from agents.hedy.agent import HedyAgent
- __all__ = ['HedyAgent']

### Source: `jmac-cornelis/agent-workforce:agents/hedy/api.py`
- Module: agents/workforce/hedy/api.py
- Description: FastAPI router for the Hedy Release Manager Agent.
- Exposes release evaluation, promotion, blocking, deprecation,
- and summary endpoints.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter, HTTPException
- from typing import Any, Dict
- router = APIRouter(prefix='/v1/releases', tags=['hedy'])
- @router.post('/evaluate', response_model=Dict[str, Any])

### Source: `jmac-cornelis/agent-workforce:agents/hedy/config.yaml`
- Hedy Release Manager Agent Configuration
- Author: Cornelis Networks
- agent_id: hedy
- display_name: Hedy
- zone: execution_spine
- phase: 5
- description: >
- Release Manager Agent. Orchestrates release decisions using the Fuze
- release model with stage promotion (sit, qa, release) and human
- approval gates. Evaluates readiness from build, version, test, and

### Source: `jmac-cornelis/agent-workforce:agents/hedy/docs/PLAN.md`
- Hedy Release Manager Plan
- Hedy should be the release-management agent for the platform. Its v1 job is to take build facts from Josephine, version facts from Babbage, test evidence from the test agents, and traceability context from Linnaeus, then turn those inputs into controlled release decisions and release-state transitions.
- Hedy should use `fuze`'s existing release model as the underlying release engine where possible. In v1, Hedy should not replace `fuze` release mechanics; it should orchestrate and govern them.
- Product definition
- evaluate release readiness for a build across branch, hardware, customer, and policy context
- create release candidates and promotion requests
- drive release-state transitions through Fuze-compatible mechanisms
- produce durable release records, readiness summaries, and approval artifacts
- keep release decisions tied to exact build, version, test, and traceability evidence
- Non-goals for v1

### Source: `jmac-cornelis/agent-workforce:agents/hedy/models.py`
- Module: agents/workforce/hedy/models.py
- Description: Data models for the Hedy Release Manager Agent.
- Defines release candidates, decisions, readiness summaries,
- and promotion requests.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime, timezone
- from enum import Enum
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field

### Source: `jmac-cornelis/agent-workforce:agents/hedy/prompts/system.md`
- Hedy — Release Manager Agent
- You are Hedy, the Release Manager Agent for the Cornelis Networks Execution Spine. Your role is to evaluate release readiness, create release candidates, drive stage promotions through Fuze-compatible mechanisms, and enforce human approval gates for irreversible transitions.
- You use the existing Fuze release model (sit → qa → release) as the canonical state machine. You do not replace Babbage's version mapping or Linnaeus's traceability ownership. Production or customer-visible promotion always requires explicit human approval.
- Prioritize deterministic tool use over LLM inference. Every release decision must cite exact build, version, test, and traceability evidence. Blocked releases must record exact reasons.

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/README.md`
- Hemingway - Documentation Agent
- Overview
- Hemingway is the documentation agent for the Cornelis Networks platform. Named after Ernest Hemingway, it turns source changes, build and test facts, traceability context, release context, and meeting-derived clarifications into durable engineering and user-facing documentation.
- Hemingway does not generate prose detached from implementation truth. It produces documentation from authoritative system records - code, builds, tests, releases, and meeting decisions.
- Quick Start
- docker compose up hemingway
- uvicorn agents.hemingway.api:app --host 0.0.0.0 --port 8203
- What Hemingway Does
- Generates and maintains repo-level as-built documentation
- Updates user and engineering documentation when code, build, test, release, or meeting knowledge changes

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/__init__.py`
- Module: agents/hemingway/__init__.py
- Description: Hemingway documentation agent package.
- Lazy imports to avoid circular dependency with agents.base → tools.
- Author: Cornelis Networks
- _LAZY_MAP = {
- 'HemingwayDocumentationAgent': ('agents.hemingway.agent', 'HemingwayDocumentationAgent'),
- 'HypatiaDocumentationAgent': ('agents.hemingway.agent', 'HemingwayDocumentationAgent'),
- 'HemingwayRecordStore': ('agents.hemingway.state.record_store', 'HemingwayRecordStore'),
- 'HypatiaRecordStore': ('agents.hemingway.state.record_store', 'HemingwayRecordStore'),
- def __getattr__(name):

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/agent.py`
- Module: agents/hemingway/agent.py
- Description: Hemingway Documentation agent.
- Produces documentation-impact analysis, source-grounded internal
- documentation records, and review-gated publication plans for
- repo Markdown and Confluence targets.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import re

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/cli.py`
- Module: agents/hemingway/cli.py
- Description: Standalone CLI for Hemingway Documentation agent.
- Provides direct access to documentation generation, impact analysis,
- and review-gated publication to repo Markdown and Confluence.
- Author: Cornelis Networks
- from __future__ import annotations
- import argparse
- import json
- import logging
- import os

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/api.py`
- Module: agents/hemingway/api.py
- Description: Hemingway Documentation Agent REST API.
- FastAPI service exposing documentation generation, impact analysis,
- record retrieval, and review-gated publication.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- import tempfile

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/docs/PLAN.md`
- Hemingway Documentation Agent Plan
- Hemingway should be the documentation agent for the platform. Its v1 job is to turn source changes, build and test facts, traceability context, release context, and meeting-derived clarifications into durable engineering and user-facing documentation updates.
- Hemingway should not be a prose generator detached from implementation truth. It should produce documentation from authoritative system records.
- Product definition
- generate and maintain repo-level as-built documentation
- update user and engineering documentation from validated system facts
- propose documentation changes when code, build, test, release, or meeting knowledge changes
- publish approved docs to internal documentation targets
- keep documentation linked to builds, versions, and traceability records where useful
- Non-goals for v1

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/models.py`
- Module: agents/hemingway/models.py
- Description: Data models for the Hemingway Documentation agent.
- Defines documentation requests, impact records, candidate patches,
- durable document records, and publication records.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- import uuid

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/nl_query.py`
- Module: agents/hemingway/nl_query.py
- Description: Natural language query translation for Hemingway. Uses LLM function calling
- to convert plain English questions into structured documentation tool calls,
- execute them via Hemingway REST API, and summarize results.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/prompts/as-built-design.md`
- As-Built Design Prompt — The Chronicler
- You are The Chronicler — a documentation engineer who documents what was actually built, not what was planned.
- You will receive the actual source code of the module. Your output documents THAT code — its architecture, components, data flows, and design decisions. Write as if you are the author explaining the codebase to another engineer joining the team.
- CRITICAL RULES:
- The source files ARE the subject of the documentation. Describe what they do.
- Code-grounded: Every claim must be traceable to actual source code. Cite files, functions, structs, and constants by name.
- Include code snippets. Show, don't just tell.
- When documenting a directory, describe its current state (not changes). Each README stands alone.
- NEVER mention documentation generation, CI pipelines, or tooling that produced this request.
- NEVER describe the process by which this document was created.

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/prompts/system.md`
- Documentation Agent — The Archivist
- You are The Archivist, the documentation intelligence agent for the Cornelis Networks agent workforce. You produce source-grounded, validation-gated documentation.
- Your job is to turn authoritative engineering inputs into reviewable, publishable internal documentation updates. Focus on:
- 1. Documentation impact analysis
- 2. Source-grounded internal document generation
- 3. Validation and confidence reporting
- 4. Review-gated publication planning
- Write for the engineer who will maintain this code six months from now, when the original author has moved to another project. Your documentation is the bridge between "what does this code do?" and "why was it written this way?"
- Documentation Types
- `as_built` / `engineering_reference`: Architecture and design documentation for module directories. Grounded in actual source code, not aspirational. Uses 3-pass analysis: structure discovery → behavior tracing → synthesis.

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/prompts/traceability.md`
- Traceability Document Prompt — The Auditor
- You are The Auditor, generating a `release_note_support` or `traceability` document.
- Your task is to analyze requirements (Jira tickets, acceptance criteria, design docs), map them to implementation and test code, and produce a Requirements Traceability Matrix and Gap Analysis.
- Target Format
- Start with a YAML front matter block:
- title: "Traceability Report"
- date: "<YYYY-MM-DD>"
- status: "draft"
- Requirements Traceability Matrix format
- Your analysis must follow these steps before generating output:

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/prompts/user-guide.md`
- User Guide Prompt — The Librarian
- You are The Librarian, generating a `user_guide` or `how_to` document.
- Your task is to produce CLI-focused user documentation suitable for GitHub Pages (MkDocs Material).
- This documentation covers installation, commands, options, examples, and exit codes, structured as a man-page style reference.
- Target Format
- MkDocs Material compatible Markdown
- Section Structure
- Start with a YAML front matter block:
- title: "<Agent/Tool Name> User Guide"
- date: "<YYYY-MM-DD>"

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/tools.py`
- Module: agents/hemingway/tools.py
- Description: Hemingway documentation tools for agent use.
- Wraps the Hemingway documentation workflow as agent-callable tools.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from typing import Optional
- from tools.base import BaseTool, ToolResult, tool
- Logging config - follows jira_utils.py pattern

### Source: `jmac-cornelis/agent-workforce:agents/hemingway/state/record_store.py`
- Module: agents/hemingway/state/record_store.py
- Description: Persistence helpers for Hemingway documentation records.
- Stores durable JSON + Markdown artifacts plus publication history.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys
- from datetime import datetime

### Source: `jmac-cornelis/agent-workforce:agents/herodotus/README.md`
- Herodotus — Knowledge Capture
- > Status: Planned
- Overview
- Herodotus is the knowledge-capture agent for the platform. It ingests meeting transcripts and metadata, produces structured summaries, extracts decisions and action items, and preserves the human rationale that often gets lost between chat, meetings, tickets, and engineering work.
- Herodotus does not become a generic chatbot for meetings. It produces durable, reviewable records.
- Responsibilities
- Detect and ingest Microsoft Teams meeting transcripts and metadata
- Produce structured meeting summaries with speaker attribution
- Extract decisions, action items, and follow-ups
- Link captured knowledge to relevant Jira tickets and engineering context

### Source: `jmac-cornelis/agent-workforce:agents/herodotus/__init__.py`
- Module: agents/workforce/herodotus/__init__.py
- Description: Herodotus Knowledge Capture agent package.
- Author: Cornelis Networks
- from agents.herodotus.agent import HerodotusAgent
- __all__ = ['HerodotusAgent']

### Source: `jmac-cornelis/agent-workforce:agents/herodotus/agent.py`
- Module: agents/workforce/herodotus/agent.py
- Description: Herodotus Knowledge Capture agent.
- Ingests Teams meeting transcripts and produces structured
- summaries, decisions, and action items.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/herodotus/config.yaml`
- agent_id: herodotus
- agent_name: Herodotus Knowledge Capture
- zone: intelligence
- phase: 4
- description: >
- Ingests Teams meeting transcripts and produces structured summaries,
- decisions, and action items.
- temperature: 0.5
- max_tokens: 8192
- max_iterations: 10

### Source: `jmac-cornelis/agent-workforce:agents/herodotus/api.py`
- Module: agents/workforce/herodotus/api.py
- Description: FastAPI router for the Herodotus Knowledge Capture agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter
- router = APIRouter(prefix='/v1/meetings', tags=['herodotus'])
- @router.post('/ingest')
- async def ingest_meeting(meeting_id: str, transcript_ref: str):
- '''Ingest a meeting transcript and metadata.'''
- raise NotImplementedError('Herodotus API not yet implemented')

### Source: `jmac-cornelis/agent-workforce:agents/herodotus/prompts/system.md`
- Herodotus — Knowledge Capture Agent
- You are Herodotus, the Knowledge Capture agent for the Cornelis Networks Agent Workforce.
- You ingest Microsoft Teams meeting transcripts, produce structured technical summaries, extract decisions and action items, and preserve the human rationale that often gets lost between meetings, chat, and engineering work.
- Responsibilities
- Detect and ingest meeting transcripts and metadata
- Generate structured technical summaries
- Extract decisions, action items, open questions, and follow-up candidates
- Publish durable meeting summary records to the knowledge store
- Emit structured signals for Drucker, Gantt, Brooks, Hemingway, and humans
- Every summary must distinguish fact, decision, action, and unresolved question.

### Source: `jmac-cornelis/agent-workforce:agents/herodotus/models.py`
- Module: agents/workforce/herodotus/models.py
- Description: Pydantic models for the Herodotus Knowledge Capture agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class MeetingRecord(BaseModel):
- '''Record of an ingested meeting with transcript and metadata.'''
- meeting_id: str = Field(..., description='Teams meeting identifier')

### Source: `jmac-cornelis/agent-workforce:agents/herodotus/docs/PLAN.md`
- Herodotus Knowledge Capture Agent Plan
- Herodotus should be the knowledge-capture agent for the platform. Its v1 job is to ingest meeting transcripts and metadata, produce structured summaries, extract decisions and action items, and preserve the human rationale that often gets lost between chat, meetings, tickets, and engineering work.
- Herodotus should not become a generic chatbot for meetings. It should produce durable, reviewable records.
- Product definition
- detect and ingest Microsoft Teams meeting transcripts and metadata
- generate structured technical summaries
- extract decisions, action items, open questions, and follow-up candidates
- publish durable meeting summary records to an internal knowledge store
- emit structured signals that Drucker, Gantt, Brooks, Hemingway, and humans can consume
- Non-goals for v1

### Source: `jmac-cornelis/agent-workforce:agents/humphrey/README.md`
- Humphrey — Release Manager
- > Status: Planned
- Overview
- Humphrey is the release-management agent for the platform. It takes build facts from Josephine, version facts from Mercator, test evidence from the test agents, and traceability context from Berners-Lee, then turns those inputs into controlled release decisions and release-state transitions.
- Humphrey uses Fuze's existing release model as the underlying release engine. In v1, it orchestrates and governs release mechanics rather than replacing them.
- Responsibilities
- Evaluate release readiness across branch, hardware, customer, and policy context
- Orchestrate stage promotion (sit, qa, release) with human approval gates
- Track release-state transitions with full audit trail
- Enforce release policies (test coverage thresholds, known-issue limits)

### Source: `jmac-cornelis/agent-workforce:agents/humphrey/__init__.py`
- Module: agents/humphrey/__init__.py
- Description: Humphrey Release Manager Agent package.
- Author: Cornelis Networks
- from typing import Any
- __all__ = ['HumphreyAgent', 'HedyAgent']
- def __getattr__(name: str) -> Any:
- if name in ('HumphreyAgent', 'HedyAgent'):
- from agents.humphrey.agent import HumphreyAgent, HedyAgent
- if name == 'HumphreyAgent':
- return HumphreyAgent

### Source: `jmac-cornelis/agent-workforce:agents/humphrey/api.py`
- Module: agents/humphrey/api.py
- Description: FastAPI router for the Humphrey Release Manager Agent.
- Exposes release evaluation, promotion, blocking, deprecation,
- and summary endpoints.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter, HTTPException
- from typing import Any, Dict
- router = APIRouter(prefix='/v1/releases', tags=['humphrey'])
- @router.post('/evaluate', response_model=Dict[str, Any])

### Source: `jmac-cornelis/agent-workforce:agents/humphrey/config.yaml`
- Humphrey Release Manager Agent Configuration
- Author: Cornelis Networks
- agent_id: humphrey
- display_name: Humphrey
- zone: execution_spine
- phase: 5
- description: >
- Release Manager Agent. Orchestrates release decisions using the Fuze
- release model with stage promotion (sit, qa, release) and human
- approval gates. Evaluates readiness from build, version, test, and

### Source: `jmac-cornelis/agent-workforce:agents/humphrey/agent.py`
- Module: agents/humphrey/agent.py
- Description: Humphrey Release Manager Agent.
- Orchestrates release decisions using the Fuze release model
- with stage promotion (sit, qa, release) and human approval gates.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/humphrey/docs/PLAN.md`
- Humphrey Release Manager Plan
- Humphrey should be the release-management agent for the platform. Its v1 job is to take build facts from Josephine, version facts from Mercator, test evidence from the test agents, and traceability context from Berners-Lee, then turn those inputs into controlled release decisions and release-state transitions.
- Humphrey should use `fuze`'s existing release model as the underlying release engine where possible. In v1, Humphrey should not replace `fuze` release mechanics; it should orchestrate and govern them.
- Namesake
- Humphrey is named for Watts S. Humphrey, the software engineering pioneer at IBM and the SEI who helped define disciplined process, maturity models, and managed software quality. We use his name for the release manager because Humphrey gathers evidence, applies gates, and turns software readiness into a controlled release decision.
- Product definition
- evaluate release readiness for a build across branch, hardware, customer, and policy context
- create release candidates and promotion requests
- drive release-state transitions through Fuze-compatible mechanisms
- produce durable release records, readiness summaries, and approval artifacts

### Source: `jmac-cornelis/agent-workforce:agents/humphrey/prompts/system.md`
- Humphrey — Release Manager Agent
- You are Humphrey, the Release Manager Agent for the Cornelis Networks Execution Spine. Your role is to evaluate release readiness, create release candidates, drive stage promotions through Fuze-compatible mechanisms, and enforce human approval gates for irreversible transitions.
- You use the existing Fuze release model (sit → qa → release) as the canonical state machine. You do not replace Mercator's version mapping or Berners-Lee's traceability ownership. Production or customer-visible promotion always requires explicit human approval.
- Prioritize deterministic tool use over LLM inference. Every release decision must cite exact build, version, test, and traceability evidence. Blocked releases must record exact reasons.

### Source: `jmac-cornelis/agent-workforce:agents/humphrey/models.py`
- Module: agents/humphrey/models.py
- Description: Data models for the Humphrey Release Manager Agent.
- Defines release candidates, decisions, readiness summaries,
- and promotion requests.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime, timezone
- from enum import Enum
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field

### Source: `jmac-cornelis/agent-workforce:agents/jira_analyst.py`
- Module: agents/jira_analyst.py
- Description: Jira Analyst Agent for analyzing current Jira state.
- Examines existing releases, tickets, components, and workflows.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- from agents.base import BaseAgent, AgentConfig, AgentResponse
- from tools.jira_tools import JiraTools

### Source: `jmac-cornelis/agent-workforce:agents/josephine/README.md`
- Josephine — Build Agent
- > Status: Planned
- Overview
- Josephine is an internal API-driven build service built on top of a reusable Fuze core. It runs Fuze-compatible build and packaging workflows in a hosted environment while preserving existing build maps, package semantics, FuzeID behavior, and Fuze-compatible metadata and artifact lineage.
- Josephine is not a replacement for ATF, release promotion, or Jira/Bamboo workflow ownership in v1. It is the hosted build and package execution layer.
- Responsibilities
- Accept build jobs through an API
- Execute Fuze-compatible build and packaging workflows
- Produce build artifacts with proper FuzeID lineage
- Publish build metadata for consumption by downstream agents

### Source: `jmac-cornelis/agent-workforce:agents/josephine/agent.py`
- Module: agents/workforce/josephine/agent.py
- Description: Josephine Build & Package Agent.
- Accepts build jobs through an API, executes them on dedicated workers
- using the extracted fuze core, and publishes packages, logs, and
- provenance in a Fuze-compatible format.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/josephine/__init__.py`
- Module: agents/workforce/josephine/__init__.py
- Description: Josephine Build & Package Agent package.
- Author: Cornelis Networks
- from agents.josephine.agent import JosephineAgent
- __all__ = ['JosephineAgent']

### Source: `jmac-cornelis/agent-workforce:agents/josephine/config.yaml`
- Josephine Build & Package Agent Configuration
- Author: Cornelis Networks
- agent_id: josephine
- display_name: Josephine
- zone: execution_spine
- phase: 1
- description: >
- Build & Package Agent. Accepts build jobs through an API, executes them
- on dedicated workers using the extracted fuze core, and publishes packages,
- logs, and provenance in a Fuze-compatible format.

### Source: `jmac-cornelis/agent-workforce:agents/josephine/models.py`
- Module: agents/workforce/josephine/models.py
- Description: Data models for the Josephine Build & Package Agent.
- Defines build requests, results, records, and failure
- classification for the build execution pipeline.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime, timezone
- from enum import Enum
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field

### Source: `jmac-cornelis/agent-workforce:agents/josephine/api.py`
- Module: agents/workforce/josephine/api.py
- Description: FastAPI router for the Josephine Build & Package Agent.
- Exposes build job submission, status, artifact, cancel,
- and retry endpoints.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter, HTTPException
- from typing import Any, Dict
- from agents.josephine.models import BuildRequest, BuildRecord, BuildResult
- router = APIRouter(prefix='/v1/build-jobs', tags=['josephine'])

### Source: `jmac-cornelis/agent-workforce:agents/josephine/docs/PLAN.md`
- Josephine Build Agent Plan
- Josephine should be an internal API-driven build service built on top of a reusable `fuze` core. Its v1 job is to run `fuze`-compatible build and packaging workflows in a hosted environment while preserving existing build maps, package semantics, FuzeID behavior, and Fuze-compatible metadata and artifact lineage.
- Josephine is not a replacement for ATF, release promotion, or Jira/Bamboo workflow ownership in v1. It is the hosted build/package execution layer.
- Namesake
- Josephine is named for Josephine Cochrane, the American inventor who created the first commercially successful mechanical dishwasher after deciding that repetitive manual work should be done more reliably by a machine. We use her name for the build agent because Josephine takes labor-intensive, failure-prone build and packaging work and turns it into a dependable automated service with consistent outputs.
- Product definition
- Accept build jobs through an API.
- Execute those jobs on dedicated workers.
- Publish packages, logs, and provenance in a way existing Fuze consumers can still use.
- Preserve compatibility with current `fuze` build maps and core workflows.

### Source: `jmac-cornelis/agent-workforce:agents/josephine/prompts/system.md`
- Josephine — Build & Package Agent
- You are Josephine, the Build & Package Agent for the Cornelis Networks Execution Spine. Your role is to accept build jobs, execute them on dedicated workers using the fuze core, and publish packages, logs, and provenance in a Fuze-compatible format.
- You preserve existing build-map behavior, package semantics, FuzeID rules, and Fuze-compatible metadata lineage. You do not own release promotion, ATF execution, or local developer CLI workflows.
- When making decisions, prioritize deterministic tool use over LLM inference. Log every action and decision with full context for auditability. Classify failures accurately — distinguish retryable transient infrastructure failures from deterministic build errors.

### Source: `jmac-cornelis/agent-workforce:agents/linnaeus/README.md`
- Linnaeus — Traceability Agent
- > Status: Planned
- Overview
- Linnaeus is the traceability agent for the platform. It maintains exact, queryable relationships between requirements, Jira issues, commits, builds, test executions, releases, and external version mappings.
- Linnaeus is not a vague reporting layer. It is the system that establishes and serves relationship facts.
- Responsibilities
- Consume identity-bearing events from Jira, GitHub, Josephine, Faraday, Hedy, and Babbage
- Maintain a structured traceability graph linking requirements to releases
- Serve traceability queries for any agent or human
- Detect traceability gaps (untested commits, unlinked builds, orphaned requirements)

### Source: `jmac-cornelis/agent-workforce:agents/linnaeus/__init__.py`
- Module: agents/workforce/linnaeus/__init__.py
- Description: Linnaeus Traceability agent package.
- Author: Cornelis Networks
- from agents.linnaeus.agent import LinnaeusAgent
- __all__ = ['LinnaeusAgent']

### Source: `jmac-cornelis/agent-workforce:agents/linnaeus/config.yaml`
- agent_id: linnaeus
- agent_name: Linnaeus Traceability
- zone: intelligence
- phase: 3
- description: >
- Maintains exact queryable relationships between requirements, Jira issues,
- commits, builds, tests, releases, and external version mappings.
- temperature: 0.3
- max_tokens: 4096
- max_iterations: 10

### Source: `jmac-cornelis/agent-workforce:agents/linnaeus/api.py`
- Module: agents/workforce/linnaeus/api.py
- Description: FastAPI router for the Linnaeus Traceability agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from typing import Optional
- from fastapi import APIRouter
- from agents.linnaeus.models import TraceAssertion
- router = APIRouter(prefix='/v1/trace', tags=['linnaeus'])
- @router.post('/assert', response_model=TraceAssertion)
- async def assert_trace(source_type: str, source_id: str, target_type: str,

### Source: `jmac-cornelis/agent-workforce:agents/linnaeus/docs/PLAN.md`
- Linnaeus Traceability Agent Plan
- Linnaeus should be the traceability agent for the platform. Its v1 job is to maintain exact, queryable relationships between requirements, Jira issues, commits, builds, test executions, releases, and external version mappings.
- Linnaeus should not become a vague reporting layer. It should be the system that establishes and serves relationship facts.
- Product definition
- consume identity-bearing events from Jira, GitHub, Josephine, Faraday, Hedy, Babbage, and project artifacts
- resolve and persist exact links between technical and workflow records
- expose trace views that humans and other agents can query reliably
- push narrow, evidence-backed traceability updates back into Jira where useful
- make it possible to move from any key record to the related build, test, release, and issue context
- Non-goals for v1

### Source: `jmac-cornelis/agent-workforce:agents/linnaeus/agent.py`
- Module: agents/workforce/linnaeus/agent.py
- Description: Linnaeus Traceability agent.
- Maintains exact, queryable relationships between requirements,
- Jira issues, commits, builds, tests, releases, and versions.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/linnaeus/models.py`
- Module: agents/workforce/linnaeus/models.py
- Description: Pydantic models for the Linnaeus Traceability agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class TraceabilityRecord(BaseModel):
- '''A stored traceability record linking two system entities.'''
- record_id: str = Field(..., description='Unique traceability record identifier')

### Source: `jmac-cornelis/agent-workforce:agents/linnaeus/prompts/system.md`
- Linnaeus — Traceability Agent
- You are Linnaeus, the Traceability agent for the Cornelis Networks Agent Workforce.
- You maintain exact, queryable relationships between requirements, Jira issues, commits, builds, tests, releases, and external version mappings. You are the authoritative relationship graph.
- Responsibilities
- Consume identity-bearing events from Jira, GitHub, Josephine, Faraday, Hedy, and Babbage
- Resolve and persist exact links between technical and workflow records
- Expose trace views that humans and other agents can query reliably
- Push narrow, evidence-backed traceability updates back into Jira where useful
- Detect coverage gaps where traceability chains are incomplete
- Every stored relationship names the source record, target record, edge type, confidence, and evidence source.

### Source: `jmac-cornelis/agent-workforce:agents/linus/README.md`
- Linus — Code Review Agent
- > Status: Planned
- Overview
- Linus is the code-review agent for the platform. It evaluates pull requests against code-quality and review-policy rules, produces structured findings, surfaces likely correctness risks early, and emits clear signals to downstream agents when documentation, build, or test attention is warranted.
- Linus focuses on high-signal review findings tied to correctness, maintainability, and policy. It should not become a style bot or a generic lint wrapper.
- Responsibilities
- Consume GitHub pull request events and diff context
- Evaluate PRs against configurable policy profiles (kernel, embedded C++, Python)
- Produce structured code review findings with severity and confidence
- Emit cross-agent impact signals (e.g., "this PR affects API contracts")

### Source: `jmac-cornelis/agent-workforce:agents/linus/agent.py`
- Module: agents/workforce/linus/agent.py
- Description: Linus Code Review Agent.
- Evaluates PRs against policy profiles and emits structured
- findings and cross-agent impact signals.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/linus/__init__.py`
- Module: agents/workforce/linus/__init__.py
- Description: Linus Code Review Agent package.
- Author: Cornelis Networks
- from agents.linus.agent import LinusAgent
- __all__ = ['LinusAgent']

### Source: `jmac-cornelis/agent-workforce:agents/linus/api.py`
- Module: agents/workforce/linus/api.py
- Description: FastAPI router for the Linus Code Review Agent.
- Exposes PR review, summary, findings, and publish endpoints.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter, HTTPException
- from typing import Any, Dict
- from agents.linus.models import ReviewRequest
- router = APIRouter(prefix='/v1/reviews', tags=['linus'])
- @router.post('/pr', response_model=Dict[str, Any])

### Source: `jmac-cornelis/agent-workforce:agents/linus/docs/PLAN.md`
- Linus Code Review Agent Plan
- Linus should be the code-review agent for the platform. Its v1 job is to evaluate pull requests against code-quality and review-policy rules, produce structured findings, surface likely correctness risks early, and emit clear signals to downstream agents when documentation, build, or test attention is warranted.
- Linus should not become a style bot or a generic lint wrapper. It should focus on high-signal review findings tied to correctness, maintainability, and policy.
- Namesake
- Linus is named for Linus Torvalds, the creator of Linux and Git, two foundational systems shaped by practical engineering judgment, code review, and change control at scale. We use his name for the code-review agent because Linus is about evaluating changes rigorously, surfacing real risk early, and keeping the codebase healthy as it evolves.
- Product definition
- consume GitHub pull request events and diff context
- evaluate code changes against review-policy profiles
- produce structured findings, inline comments, and review summaries
- emit documentation-impact and test/build risk signals when warranted

### Source: `jmac-cornelis/agent-workforce:agents/linus/config.yaml`
- Linus Code Review Agent Configuration
- Author: Cornelis Networks
- agent_id: linus
- display_name: Linus
- zone: execution_spine
- phase: 5
- description: >
- Code Review Agent. Evaluates PRs against policy profiles (kernel,
- embedded C++, Python) and emits structured findings and cross-agent
- impact signals for documentation, build, and test attention.

### Source: `jmac-cornelis/agent-workforce:agents/linus/models.py`
- Module: agents/workforce/linus/models.py
- Description: Data models for the Linus Code Review Agent.
- Defines review requests, findings, summaries, and
- policy profiles.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime, timezone
- from enum import Enum
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field

### Source: `jmac-cornelis/agent-workforce:agents/linus/prompts/system.md`
- Linus — Code Review Agent
- You are Linus, the Code Review Agent for the Cornelis Networks Execution Spine. Your role is to evaluate pull requests against code-quality and review-policy rules, produce structured findings, surface correctness risks early, and emit signals to downstream agents when documentation, build, or test attention is warranted.
- You focus on high-signal review findings tied to correctness, maintainability, and policy — not style. Uncertain findings are marked as low-confidence, not stated as fact. You support kernel, embedded C++, and Python policy profiles.
- Prioritize deterministic tool use over LLM inference. Every finding must cite the code location, rule or reasoning, and severity. Suppress low-signal bulk commenting.

### Source: `jmac-cornelis/agent-workforce:agents/mercator/README.md`
- Mercator — Version Manager
- > Status: Planned
- Overview
- Mercator is the version-mapping agent for the platform. It connects internal build identity from Fuze with external release versions and maintains the lineage between the two. Josephine produces internal build IDs, Humphrey decides release intent, and Mercator maps between them as a durable record.
- Responsibilities
- Map internal Fuze build IDs to external customer-facing version strings
- Detect and prevent version mapping conflicts
- Maintain lineage and audit trail for all version assignments
- Serve version lookups for other agents (Humphrey, Berners-Lee, Hemingway)
- Track version progression across branches and release trains

### Source: `jmac-cornelis/agent-workforce:agents/mercator/__init__.py`
- Module: agents/mercator/__init__.py
- Description: Mercator Version Manager agent package.
- Author: Cornelis Networks
- from typing import Any
- __all__ = ['MercatorAgent', 'BabbageAgent']
- def __getattr__(name: str) -> Any:
- if name in ('MercatorAgent', 'BabbageAgent'):
- from agents.mercator.agent import MercatorAgent, BabbageAgent
- if name == 'MercatorAgent':
- return MercatorAgent

### Source: `jmac-cornelis/agent-workforce:agents/mercator/config.yaml`
- Mercator Version Manager Agent Configuration
- Cornelis Networks
- agent_id: mercator
- agent_name: Mercator Version Manager
- zone: intelligence
- phase: 3
- description: >
- Maps internal Fuze build IDs to external customer-facing release versions
- with conflict detection and lineage tracking.
- temperature: 0.3

### Source: `jmac-cornelis/agent-workforce:agents/mercator/agent.py`
- Module: agents/mercator/agent.py
- Description: Mercator Version Manager agent.
- Maps internal Fuze build IDs to external customer-facing release
- versions with conflict detection and lineage tracking.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/mercator/models.py`
- Module: agents/mercator/models.py
- Description: Pydantic models for the Mercator Version Manager agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class VersionMappingRequest(BaseModel):
- '''Request to map an internal build ID to an external version.'''
- build_id: str = Field(..., description='Internal Fuze build identifier (FuzeID)')

### Source: `jmac-cornelis/agent-workforce:agents/mercator/api.py`
- Module: agents/mercator/api.py
- Description: FastAPI router for the Mercator Version Manager agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter
- from agents.mercator.models import (
- VersionMappingRequest,
- VersionMappingRecord,
- router = APIRouter(prefix='/v1/version-mappings', tags=['mercator'])
- @router.post('/', response_model=VersionMappingRecord)

### Source: `jmac-cornelis/agent-workforce:agents/mercator/prompts/system.md`
- Mercator — Version Manager Agent
- You are Mercator, the Version Manager agent for the Cornelis Networks Agent Workforce.
- You map internal Fuze build identities (FuzeID) to external customer-facing release versions. You maintain deterministic version lineage, detect mapping conflicts, and preserve compatibility and supersession records.
- Responsibilities
- Map internal build IDs to external version proposals
- Support forward and reverse version lookups
- Detect and surface version collisions and ambiguity
- Record replacement and supersession relationships
- Require confirmation for risky or ambiguous mappings
- One internal build ID may map to one or more scoped external versions only if policy explicitly allows target-specific variation.

### Source: `jmac-cornelis/agent-workforce:agents/mercator/docs/PLAN.md`
- Mercator Version Manager Plan
- Mercator should be the version-mapping agent for the platform. Its v1 job is to connect internal build identity from `fuze` with external release versions and maintain the lineage between the two.
- In practical terms:
- Josephine produces the internal build identity
- Humphrey decides release intent and scope
- Mercator maps internal build IDs to external versions and preserves that mapping as a durable record
- Mercator should not replace `fuze`'s internal identity model. It should build a controlled mapping layer on top of it.
- Namesake
- Mercator is named for Gerardus Mercator, the Flemish cartographer whose maps became a standard way to navigate between places and coordinate systems. We use his name for the version manager because Mercator maps one identity space to another: internal build identities, external versions, and the lineage between them.
- Product definition

### Source: `jmac-cornelis/agent-workforce:agents/nightingale/__init__.py`
- Module: agents/workforce/nightingale/__init__.py
- Description: Nightingale Bug Investigation agent package.
- Author: Cornelis Networks
- from agents.nightingale.agent import NightingaleAgent
- __all__ = ['NightingaleAgent']

### Source: `jmac-cornelis/agent-workforce:agents/nightingale/README.md`
- Nightingale — Bug Investigation
- > Status: Planned
- Overview
- Nightingale is the bug-investigation agent for the platform. It reacts to Jira bug reports, qualifies the report, assembles technical context, determines whether the issue is reproducible, and coordinates targeted reproduction work until the bug is either reproduced, blocked on missing data, or clearly triaged for humans.
- Nightingale turns vague bug reports into actionable technical evidence.
- Responsibilities
- React quickly to new or updated Jira bug reports
- Qualify bug reports (completeness, severity, reproducibility signals)
- Assemble technical context from builds, tests, releases, and traceability
- Determine reproduction feasibility and coordinate targeted reproduction

### Source: `jmac-cornelis/agent-workforce:agents/nightingale/config.yaml`
- agent_id: nightingale
- agent_name: Nightingale Bug Investigation
- zone: intelligence
- phase: 5
- description: >
- Reacts to Jira bugs, assembles build/test/release context, drives targeted
- reproduction, and produces investigation summaries.
- temperature: 0.3
- max_tokens: 8192
- max_iterations: 15

### Source: `jmac-cornelis/agent-workforce:agents/nightingale/docs/PLAN.md`
- Nightingale Bug Triage, Analysis, and Reproduction Plan
- Nightingale should be the bug-investigation agent for the platform. Its v1 job is to react to Jira bug reports, qualify the report, assemble technical context, determine whether the issue is reproducible, and coordinate targeted reproduction work until the bug is either reproduced, blocked on missing data, or clearly triaged for humans.
- Nightingale should not replace Jira workflow ownership, release decisions, or traceability ownership. It should turn vague bug reports into actionable technical evidence.
- Namesake
- Nightingale is named for Florence Nightingale, the pioneering nurse and statistician who used observation, evidence, and disciplined record-keeping to improve outcomes in complex systems. We use her name for the bug-investigation agent because Nightingale starts with symptoms, gathers evidence, and turns confusion into an actionable diagnosis.
- Product definition
- react quickly to new or updated Jira bug reports
- gather build, test, release, and traceability context for the reported issue
- identify missing information and request it explicitly
- create and drive targeted reproduction attempts

### Source: `jmac-cornelis/agent-workforce:agents/nightingale/api.py`
- Module: agents/workforce/nightingale/api.py
- Description: FastAPI router for the Nightingale Bug Investigation agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter
- from agents.nightingale.models import BugInvestigationRequest
- router = APIRouter(prefix='/v1/bugs', tags=['nightingale'])
- @router.post('/investigate')
- async def investigate_bug(request: BugInvestigationRequest):
- '''Start a bug investigation.'''

### Source: `jmac-cornelis/agent-workforce:agents/nightingale/agent.py`
- Module: agents/workforce/nightingale/agent.py
- Description: Nightingale Bug Investigation agent.
- Reacts to Jira bugs, assembles build/test/release context,
- drives targeted reproduction, and produces investigation summaries.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/nightingale/prompts/system.md`
- Nightingale — Bug Investigation Agent
- You are Nightingale, the Bug Investigation agent for the Cornelis Networks Agent Workforce.
- You react to Jira bug reports, qualify the report, assemble technical context, determine whether the issue is reproducible, and coordinate targeted reproduction work until the bug is reproduced, blocked on missing data, or triaged for humans.
- Responsibilities
- React quickly to new or updated Jira bug reports
- Gather build, test, release, and traceability context
- Identify missing information and request it explicitly
- Create and drive targeted reproduction attempts
- Produce durable investigation records and failure signatures
- Never claim reproduction without a durable reproduction record.

### Source: `jmac-cornelis/agent-workforce:agents/nightingale/models.py`
- Module: agents/workforce/nightingale/models.py
- Description: Pydantic models for the Nightingale Bug Investigation agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class BugInvestigationRequest(BaseModel):
- '''Request to investigate a Jira bug report.'''
- jira_key: str = Field(..., description='Jira issue key for the bug')

### Source: `jmac-cornelis/agent-workforce:agents/orchestrator.py`
- Module: agents/orchestrator.py
- Description: Release Planning Orchestrator Agent.
- Coordinates the end-to-end release planning workflow.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- from dataclasses import dataclass, field
- from agents.base import BaseAgent, AgentConfig, AgentResponse

### Source: `jmac-cornelis/agent-workforce:agents/planning_agent.py`
- Module: agents/planning_agent.py
- Description: Planning Agent for creating release structures.
- Maps roadmap items to Jira ticket hierarchy.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- from dataclasses import dataclass, field
- from agents.base import BaseAgent, AgentConfig, AgentResponse

### Source: `jmac-cornelis/agent-workforce:agents/pliny/README.md`
- Pliny — Knowledge Capture
- > Status: Planned
- Overview
- Pliny is the knowledge-capture agent for the platform. It ingests meeting transcripts and metadata, produces structured summaries, extracts decisions and action items, and preserves the human rationale that often gets lost between chat, meetings, tickets, and engineering work.
- Pliny does not become a generic chatbot for meetings. It produces durable, reviewable records.
- Responsibilities
- Detect and ingest Microsoft Teams meeting transcripts and metadata
- Produce structured meeting summaries with speaker attribution
- Extract decisions, action items, and follow-ups
- Link captured knowledge to relevant Jira tickets and engineering context

### Source: `jmac-cornelis/agent-workforce:agents/pliny/agent.py`
- Module: agents/pliny/agent.py
- Description: Pliny Knowledge Capture agent.
- Ingests Teams meeting transcripts and produces structured
- summaries, decisions, and action items.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/pliny/api.py`
- Module: agents/pliny/api.py
- Description: FastAPI router for the Pliny Knowledge Capture agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter
- router = APIRouter(prefix='/v1/meetings', tags=['pliny'])
- @router.post('/ingest')
- async def ingest_meeting(meeting_id: str, transcript_ref: str):
- '''Ingest a meeting transcript and metadata.'''
- raise NotImplementedError('Pliny API not yet implemented')

### Source: `jmac-cornelis/agent-workforce:agents/pliny/__init__.py`
- Module: agents/pliny/__init__.py
- Description: Pliny Knowledge Capture agent package.
- Author: Cornelis Networks
- from typing import Any
- __all__ = ['PlinyAgent', 'HerodotusAgent']
- def __getattr__(name: str) -> Any:
- if name in ('PlinyAgent', 'HerodotusAgent'):
- from agents.pliny.agent import PlinyAgent, HerodotusAgent
- if name == 'PlinyAgent':
- return PlinyAgent

### Source: `jmac-cornelis/agent-workforce:agents/pliny/config.yaml`
- agent_id: pliny
- agent_name: Pliny Knowledge Capture
- zone: intelligence
- phase: 4
- description: >
- Ingests Teams meeting transcripts and produces structured summaries,
- decisions, and action items.
- temperature: 0.5
- max_tokens: 8192
- max_iterations: 10

### Source: `jmac-cornelis/agent-workforce:agents/pliny/docs/PLAN.md`
- Pliny Knowledge Capture Agent Plan
- Pliny should be the knowledge-capture agent for the platform. Its v1 job is to ingest meeting transcripts and metadata, produce structured summaries, extract decisions and action items, and preserve the human rationale that often gets lost between chat, meetings, tickets, and engineering work.
- Pliny should not become a generic chatbot for meetings. It should produce durable, reviewable records.
- Namesake
- Pliny is named for Pliny the Younger, the Roman lawyer, administrator, and letter-writer whose surviving correspondence preserved events, decisions, and first-hand observations with unusual clarity. We use his name for the knowledge-capture agent because Pliny turns ephemeral meetings into durable records of what happened, what was decided, and what needs follow-up.
- Product definition
- detect and ingest Microsoft Teams meeting transcripts and metadata
- generate structured technical summaries
- extract decisions, action items, open questions, and follow-up candidates
- publish durable meeting summary records to an internal knowledge store

### Source: `jmac-cornelis/agent-workforce:agents/pliny/prompts/system.md`
- Pliny — Knowledge Capture Agent
- You are Pliny, the Knowledge Capture agent for the Cornelis Networks Agent Workforce.
- You ingest Microsoft Teams meeting transcripts, produce structured technical summaries, extract decisions and action items, and preserve the human rationale that often gets lost between meetings, chat, and engineering work.
- Responsibilities
- Detect and ingest meeting transcripts and metadata
- Generate structured technical summaries
- Extract decisions, action items, open questions, and follow-up candidates
- Publish durable meeting summary records to the knowledge store
- Emit structured signals for Drucker, Gantt, Shackleton, Hemingway, and humans
- Every summary must distinguish fact, decision, action, and unresolved question.

### Source: `jmac-cornelis/agent-workforce:agents/pliny/models.py`
- Module: agents/pliny/models.py
- Description: Pydantic models for the Pliny Knowledge Capture agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class MeetingRecord(BaseModel):
- '''Record of an ingested meeting with transcript and metadata.'''
- meeting_id: str = Field(..., description='Teams meeting identifier')

### Source: `jmac-cornelis/agent-workforce:agents/pm_runtime.py`
- from __future__ import annotations
- import logging
- import os
- import sys
- from typing import Any, Dict, Iterable, List, Optional
- import requests
- from config.env_loader import resolve_dry_run
- log = logging.getLogger(os.path.basename(sys.argv[0]))
- def normalize_csv_list(value: List[str] | str | None) -> List[str]:
- Normalize a list or comma-separated string into a clean string list.

### Source: `jmac-cornelis/agent-workforce:agents/research_agent.py`
- Module: agents/research_agent.py
- Description: Research Agent for the Feature Planning pipeline.
- Gathers comprehensive technical information about a new feature
- from web search, Cornelis MCP, local knowledge base, and
- user-provided documents.
- Author: Cornelis Networks
- import json
- import logging
- import os
- import re

### Source: `jmac-cornelis/agent-workforce:agents/rename_registry.py`
- Module: agents/rename_registry.py
- Description: Canonical agent rename registry and alias helpers for the local
- rename transition.
- Author: Cornelis Networks
- from __future__ import annotations
- from typing import Dict, Optional
- AGENT_RENAMES: Dict[str, Dict[str, str]] = {
- 'hypatia': {
- 'canonical': 'hemingway',
- 'display_name': 'Hemingway',

### Source: `jmac-cornelis/agent-workforce:agents/review_agent.py`
- Module: agents/review_agent.py
- Description: Review Agent for human-in-the-loop approval workflow.
- Presents plans for review and executes approved changes.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- import tempfile
- from datetime import datetime, timezone
- from typing import Any, Callable, Dict, List, Optional

### Source: `jmac-cornelis/agent-workforce:agents/scoping_agent.py`
- Module: agents/scoping_agent.py
- Description: Scoping Agent for the Feature Planning pipeline.
- Acts as an embedded SW/FW engineering expert to define and scope
- all software/firmware work required for a new hardware feature.
- Author: Cornelis Networks
- import json
- import logging
- import os
- import re
- import sys

### Source: `jmac-cornelis/agent-workforce:agents/shackleton/README.md`
- Shackleton — Delivery Manager
- > Status: Planned
- Overview
- Shackleton is the delivery-management agent for the platform. It monitors execution against plan, detects schedule risk and coordination failures early, and produces operational delivery summaries for humans. Gantt plans; Shackleton watches delivery reality and flags drift, blockage, and risk.
- Responsibilities
- Monitor work-in-flight against milestones and release targets
- Detect schedule risk from blocked dependencies, stale work, and velocity changes
- Produce operational delivery summaries and status reports
- Flag coordination failures between teams or agents
- Track delivery metrics over time for trend analysis

### Source: `jmac-cornelis/agent-workforce:agents/shackleton/agent.py`
- Module: agents/shackleton/agent.py
- Description: Shackleton Delivery Manager agent.
- Monitors execution against plan, detects schedule risk and
- coordination failures, produces forecasts and escalation prompts.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/shackleton/__init__.py`
- Module: agents/shackleton/__init__.py
- Description: Shackleton Delivery Manager agent package.
- Author: Cornelis Networks
- from typing import Any
- __all__ = ['ShackletonAgent', 'BrooksAgent']
- def __getattr__(name: str) -> Any:
- if name in ('ShackletonAgent', 'BrooksAgent'):
- from agents.shackleton.agent import ShackletonAgent, BrooksAgent
- if name == 'ShackletonAgent':
- return ShackletonAgent

### Source: `jmac-cornelis/agent-workforce:agents/shackleton/config.yaml`
- agent_id: shackleton
- agent_name: Shackleton Delivery Manager
- zone: planning
- phase: 6
- description: >
- Monitors execution against plan, detects schedule risk and coordination
- failures, produces forecasts and escalation prompts.
- temperature: 0.3
- max_tokens: 4096
- max_iterations: 10

### Source: `jmac-cornelis/agent-workforce:agents/shackleton/docs/PLAN.md`
- Shackleton Delivery Manager Plan
- Shackleton should be the delivery-management agent for the platform. Its v1 job is to monitor execution against plan, detect schedule risk and coordination failure early, and produce operational delivery summaries for humans.
- Shackleton should not own project planning itself. Gantt plans; Shackleton watches delivery reality and flags drift, blockage, and risk.
- Namesake
- Shackleton is named for Sir Ernest Shackleton, the Antarctic explorer remembered for leadership under uncertainty, setbacks, and changing conditions. We use his name for the delivery manager because Shackleton's job is not to invent the plan but to keep the team moving through real-world risk, slippage, and coordination trouble.
- Product definition
- monitor work-in-flight against milestones and release targets
- correlate project status with technical evidence from builds, tests, releases, and traceability
- surface delivery risk, slip probability, blocked handoffs, and missing approvals
- make status reporting fast, current, and evidence-backed

### Source: `jmac-cornelis/agent-workforce:agents/shackleton/api.py`
- Module: agents/shackleton/api.py
- Description: FastAPI router for the Shackleton Delivery Manager agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter
- router = APIRouter(prefix='/v1/delivery', tags=['shackleton'])
- @router.post('/snapshot')
- async def create_delivery_snapshot(project_key: str):
- '''Create a delivery snapshot combining Jira and technical evidence.'''
- raise NotImplementedError('Shackleton API not yet implemented')

### Source: `jmac-cornelis/agent-workforce:agents/shackleton/models.py`
- Module: agents/shackleton/models.py
- Description: Pydantic models for the Shackleton Delivery Manager agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class DeliverySnapshot(BaseModel):
- '''Point-in-time delivery status combining Jira and technical evidence.'''
- snapshot_id: str = Field(..., description='Unique snapshot identifier')

### Source: `jmac-cornelis/agent-workforce:agents/shackleton/prompts/system.md`
- Shackleton — Delivery Manager Agent
- You are Shackleton, the Delivery Manager agent for the Cornelis Networks Agent Workforce.
- You monitor execution against plan, detect schedule risk and coordination failure early, and produce operational delivery summaries for humans. Gantt plans; you watch delivery reality and flag drift, blockage, and risk.
- Responsibilities
- Monitor work-in-flight against milestones and release targets
- Correlate project status with technical evidence from builds, tests, releases, and traceability
- Surface delivery risk, slip probability, blocked handoffs, and missing approvals
- Make status reporting fast, current, and evidence-backed
- Status claims must always be tied to observable evidence.
- "On track" requires both work-state and technical-state support.

### Source: `jmac-cornelis/agent-workforce:agents/shannon/README.md`
- Shannon — Communications Agent
- Overview
- Shannon is the single Microsoft Teams bot that serves as the human interface for all domain agents in the Cornelis Networks Agent Workforce. Named after Claude Shannon, the father of information theory.
- One deployment, all channels. Shannon receives messages from Teams channels, routes commands to the correct agent API, renders responses as Adaptive Cards, manages approval workflows, and logs every interaction for audit.
- Shannon is not a dumb proxy. It owns command parsing, routing, response rendering, approval lifecycle management, conversation threading, rate limiting, error handling, and audit logging.
- Quick Start
- Podman (production)
- podman run -d --name shannon -p 8200:8200 \
- --env-file deploy/env/shared.env \
- --env-file deploy/env/teams.env \

### Source: `jmac-cornelis/agent-workforce:agents/shannon/agent.py`
- Module: agents/workforce/shannon/agent.py
- Description: Shannon Communications agent.
- Single Teams bot serving all agent channels. Routes commands,
- manages approvals, posts notifications, and logs all
- human-agent interactions.
- Author: Cornelis Networks
- from __future__ import annotations
- import asyncio
- import json
- import logging

### Source: `jmac-cornelis/agent-workforce:agents/shannon/__init__.py`
- Module: agents/workforce/shannon/__init__.py
- Description: Shannon Communications agent package.
- Author: Cornelis Networks
- from agents.shannon.agent import ShannonAgent
- from agents.shannon.graph_client import TeamsGraphClient, GraphAPIError
- from agents.shannon.registry import ChannelRegistry, ChannelMapping
- from agents.shannon import cards
- __all__ = [
- 'ShannonAgent',
- 'TeamsGraphClient',

### Source: `jmac-cornelis/agent-workforce:agents/shannon/cli.py`
- Module: agents/workforce/shannon/cli.py
- Description: CLI for testing Shannon — render cards, post to Teams, discover channels.
- Author: Cornelis Networks
- from __future__ import annotations
- import argparse
- import asyncio
- import json
- import sys
- from typing import Any, Dict
- from agents.shannon import cards

### Source: `jmac-cornelis/agent-workforce:agents/shannon/api.py`
- Module: agents/workforce/shannon/api.py
- Description: FastAPI router for the Shannon Communications agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter
- from agents.shannon.models import NotificationRequest
- router = APIRouter(prefix='/v1/bot', tags=['shannon'])
- @router.post('/notify')
- async def notify_channel(request: NotificationRequest):
- '''Agent posts activity notification to its channel.'''

### Source: `jmac-cornelis/agent-workforce:agents/shannon/cards.py`
- Module: agents/workforce/shannon/cards.py
- Description: Adaptive Card templates for Teams notifications.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime, timezone
- from typing import Any, Dict, List, Optional
- _CARD_SCHEMA = 'http://adaptivecards.io/schemas/adaptive-card.json'
- _CARD_VERSION = '1.4'
- _SEVERITY_COLORS: Dict[str, str] = {
- 'critical': 'attention',

### Source: `jmac-cornelis/agent-workforce:agents/shannon/config.yaml`
- agent_id: shannon
- agent_name: Shannon Communications
- zone: service_infrastructure
- phase: 0
- description: >
- Single Teams bot serving all agent channels. Routes commands, manages
- approvals, posts notifications, and logs all human-agent interactions.
- temperature: 0.1
- max_tokens: 2048
- max_iterations: 10

### Source: `jmac-cornelis/agent-workforce:agents/shannon/docs/PLAN.md`
- Shannon Communications Agent Plan
- Shannon is the communications service agent — the single Microsoft Teams bot that serves as the human interface for all 15 domain agents in the Cornelis Networks Agent Workforce. Named after Claude Shannon, the father of information theory.
- One deployment, 15+ channels. Shannon receives messages from all agent channels, routes commands to the correct agent API, manages conversation threads and state, handles approval workflows with timeouts and escalation, posts activity notifications and error alerts, and tracks every interaction for audit.
- Shannon is not a dumb proxy. It owns:
- Command parsing, routing, and response rendering
- Approval lifecycle management (request, post card, track response, timeout, escalate)
- Conversation threading and deduplication
- Rate limiting and error handling
- Audit logging of all human-agent interactions
- Shannon has its own operational channel (`#agent-shannon`) where operators monitor bot health, message throughput, routing errors, and issue meta-commands.

### Source: `jmac-cornelis/agent-workforce:agents/shannon/docs/TEAMS_BOT_FRAMEWORK.md`
- Teams Bot Framework Specification
- [Back to AI Agent Workforce](README.md)
- > **This is the technical specification for [Shannon](../../agents/SHANNON_COMMUNICATIONS_AGENT_PLAN.md), the communications service agent.** Shannon is the single Teams bot that serves as the unified human interface for all 16 AI agents in the Cornelis Networks Agent Workforce. Named after Claude Shannon, father of information theory.
- Table of Contents
- 1. [Overview](#1-overview)
- 2. [Architecture](#2-architecture)
- 3. [Agent Registry](#3-agent-registry)
- 4. [Message Types](#4-message-types)
- 5. [Standard Commands](#5-standard-commands)
- 6. [Adaptive Card Templates](#6-adaptive-card-templates)

### Source: `jmac-cornelis/agent-workforce:agents/shannon/docs/as-built.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Shannon — Communications Agent"
- date: "2026-04-06"
- status: "draft"
- Module Overview
- Shannon is the single Microsoft Teams bot that serves as the unified human interface for all domain agents in the Cornelis Networks Agent Workforce. Named after Claude Shannon, the father of information theory, it receives messages from Teams channels, routes commands to the correct agent API, renders responses as Adaptive Cards, manages approval workflows, and logs every interaction for audit. Shannon is not a proxy—it owns command parsing, routing, response rendering, approval lifecycle management, conversation threading, rate limiting, error handling, and audit logging.
- What Changed
- **Before:** Shannon was a planned service with a full Bot Framework SDK integration, approval workflows, and LLM-based free-text query interpretation.
- **After:** Shannon is implemented as a lightweight, deterministic routing service with:
- Microsoft Graph API integration (not Bot Framework SDK)

### Source: `jmac-cornelis/agent-workforce:agents/shannon/docs/deployment-plan.md`
- Shannon Deployment Plan — Company-Wide Rollout
- Overview
- Shannon is the communications agent for the Cornelis AI agent workforce.
- It provides a bidirectional interface between Microsoft Teams and the agent
- platform using zero-cost Teams integration mechanisms (no Azure Bot Service
- subscription required).
- **Architecture summary:**
- | Direction | Mechanism | Cost |
- |---|---|---|
- | Users → Shannon | Teams Outgoing Webhook (HMAC-verified) | Free |

### Source: `jmac-cornelis/agent-workforce:agents/shannon/docs/teams-setup.md`
- Shannon Teams Setup
- This document describes the first Shannon deployment target for this repo:
- 1. A dedicated `#agent-shannon` standard channel exists in the `Agent Workforce` team.
- 2. A Teams Outgoing Webhook called Shannon is installed in that team with no Azure subscription requirement.
- 3. Shannon can receive channel messages when `@mentioned`.
- 4. Shannon can reply in-thread inside `#agent-shannon`.
- Recommended v1 interaction model
- Use one Teams Outgoing Webhook named Shannon.
- Create `#agent-shannon` as a standard channel.
- Require users to `@mention` Shannon in the channel.

### Source: `jmac-cornelis/agent-workforce:agents/shannon/docs/config.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Shannon Configuration"
- date: "2026-04-06"
- status: "draft"
- Module Overview
- The Shannon configuration module defines the agent registry and Teams application manifest for the Cornelis agent workforce. It serves as the single source of truth for agent metadata, command routing, API endpoints, and Teams bot integration. The registry (`agent_registry.yaml`) catalogs four agents (Shannon, Drucker, Gantt, Hemingway) with their capabilities, while the Teams manifest template (`teams-app-manifest.template.json`) configures the Shannon bot for Microsoft Teams deployment.
- What Changed
- **Before:** The agent registry used two-space indentation and quoted string values throughout the YAML structure.
- **After:** The registry now uses consistent unquoted strings (except where special characters require quoting) and standardized indentation. The Gantt agent gained a `notify_shannon: true` flag.
- **Impact:**

### Source: `jmac-cornelis/agent-workforce:agents/shannon/docs/service.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Shannon — Teams Communications Agent"
- date: "2026-04-06"
- status: "draft"
- Module Overview
- Shannon is a FastAPI-based Microsoft Teams bot service that acts as the unified communications surface for the Cornelis agent workforce. It routes user commands from Teams channels to registered agent APIs, renders responses as Adaptive Cards, posts notifications to Teams channels, and dispatches direct messages and emails to users via Microsoft Graph API. Shannon maintains a registry of agent-to-channel mappings, tracks conversation references for threaded replies, and audits all routing decisions for observability.
- What Changed
- **Before:** Shannon posted notifications only to Teams channels via incoming webhooks or Bot Framework.
- **After:** Shannon now dispatches notifications to individual users via Teams DM and email using the new `NotificationRouter` and Microsoft Graph API integration.
- **Impact:**

### Source: `jmac-cornelis/agent-workforce:agents/shannon/graph_client.py`
- Module: agents/workforce/shannon/graph_client.py
- Description: Microsoft Graph API client for Teams messaging.
- Uses OAuth2 client credentials flow with Azure AD app registration.
- All HTTP calls are async via aiohttp.
- Author: Cornelis Networks
- from __future__ import annotations
- import asyncio
- import json
- import logging
- import os

### Source: `jmac-cornelis/agent-workforce:agents/shannon/models.py`
- Module: agents/workforce/shannon/models.py
- Description: Pydantic models for the Shannon Communications agent.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field
- class AgentRegistryEntry(BaseModel):
- '''Registry entry mapping a Teams channel to an agent.'''
- agent_id: str = Field(..., description='Agent identifier')

### Source: `jmac-cornelis/agent-workforce:agents/shannon/prompts/system.md`
- Shannon — Communications Agent
- You are Shannon, the Communications agent for the Cornelis Networks Agent Workforce. Named after Claude Shannon, the father of information theory.
- You are the single Microsoft Teams bot that serves as the human interface for all 15 domain agents. One deployment, 15+ channels.
- Responsibilities
- Receive messages from all agent channels and route commands to the correct agent API
- Manage conversation threads and state
- Handle approval workflows end-to-end: request, post card, track response, timeout, escalate
- Post activity notifications and error alerts
- Track every interaction for audit with user identity and correlation ID
- You do not own domain logic — you route to agents that do.

### Source: `jmac-cornelis/agent-workforce:agents/shannon/registry.py`
- Module: agents/workforce/shannon/registry.py
- Description: Channel registry — maps agent names to Teams team/channel IDs.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from dataclasses import dataclass, field
- from pathlib import Path
- from typing import Any, Dict, List, Optional

### Source: `jmac-cornelis/agent-workforce:agents/shannon/state_store.py`
- Module: state/shannon_state_store.py
- Description: Persistence helpers for the Shannon Teams bot service.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import sys
- from collections import Counter
- from datetime import datetime, timedelta, timezone

### Source: `jmac-cornelis/agent-workforce:agents/shannon/service.py`
- Module: shannon/service.py
- Description: Core Shannon service logic for Teams command handling and
- notification posting.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- import requests

### Source: `jmac-cornelis/agent-workforce:agents/tesla/README.md`
- Tesla — Test Environment Manager
- > Status: Planned
- Overview
- Tesla is the shared service that exposes lab and mock-environment state to the test agents and manages reservations for scarce test resources. It sits in front of Fuze Test so Ada, Curie, and Faraday can make reservation-aware decisions before invoking test execution.
- In the test pipeline: Ada decides what environment is needed, Curie may refine that into runtime constraints, Tesla decides whether the environment is available and reserves it, and Faraday uses the reserved location and runtime context to execute.
- Responsibilities
- Maintain a real-time inventory of HIL lab environments and mock environments
- Match test requirements to available environment capabilities
- Manage reservations with time-bounded leases and automatic cleanup
- Monitor environment health and flag degraded or offline resources

### Source: `jmac-cornelis/agent-workforce:agents/tesla/__init__.py`
- Module: agents/workforce/tesla/__init__.py
- Description: Tesla Environment Manager Agent package.
- Author: Cornelis Networks
- from agents.tesla.agent import TeslaAgent
- __all__ = ['TeslaAgent']

### Source: `jmac-cornelis/agent-workforce:agents/tesla/agent.py`
- Module: agents/workforce/tesla/agent.py
- Description: Tesla Environment Manager Agent.
- Manages lab and mock-environment reservations for the test
- agents, preventing conflicting use of scarce resources.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:agents/tesla/api.py`
- Module: agents/workforce/tesla/api.py
- Description: FastAPI router for the Tesla Environment Manager Agent.
- Exposes environment listing, reservation, heartbeat, release,
- and quarantine endpoints.
- Author: Cornelis Networks
- from __future__ import annotations
- from fastapi import APIRouter, HTTPException
- from typing import Any, Dict, List
- from agents.tesla.models import ReservationRequest, Environment
- router = APIRouter(prefix='/v1', tags=['tesla'])

### Source: `jmac-cornelis/agent-workforce:agents/tesla/config.yaml`
- Tesla Environment Manager Agent Configuration
- Author: Cornelis Networks
- agent_id: tesla
- display_name: Tesla
- zone: execution_spine
- phase: 2
- description: >
- Environment Manager Agent. Manages lab and mock-environment reservations
- for the test agents, preventing conflicting use of scarce DUT or lab
- partitions. Exposes health, capability, and utilization data.

### Source: `jmac-cornelis/agent-workforce:agents/tesla/docs/PLAN.md`
- Tesla Test Environment Manager Plan
- Tesla should be the shared service that exposes lab and mock-environment state to the test agents and manages reservations for scarce test resources. Its v1 job is not to replace Fuze Test, but to sit in front of it so Ada, Curie, and Faraday can make reservation-aware decisions before invoking Fuze Test in [atf](/Users/johnmacdonald/code/cornelis/atf).
- In practical terms:
- Ada decides what kind of environment is needed
- Curie may refine that into executable runtime constraints
- Tesla decides whether that environment is available and reserves it
- Faraday then uses the reserved location, DUT filters, and runtime context to execute the test cycle
- Namesake
- Tesla is named for Nikola Tesla, the inventor and systems builder whose work on electrical power and control made complex infrastructure usable at scale. We use his name for the environment manager because Tesla coordinates scarce shared infrastructure, keeps it available, and makes the rest of the test system possible.
- Product definition

### Source: `jmac-cornelis/agent-workforce:agents/vision_analyzer.py`
- Module: agents/vision_analyzer.py
- Description: Vision Analyzer Agent for analyzing roadmap slides and images.
- Extracts release information from visual documents.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- from agents.base import BaseAgent, AgentConfig, AgentResponse
- from tools.vision_tools import VisionTools

### Source: `jmac-cornelis/agent-workforce:agents/tesla/models.py`
- Module: agents/workforce/tesla/models.py
- Description: Data models for the Tesla Environment Manager Agent.
- Defines environments, reservations, reservation requests,
- and health status records.
- Author: Cornelis Networks
- from __future__ import annotations
- from datetime import datetime, timezone
- from enum import Enum
- from typing import Any, Dict, List, Optional
- from pydantic import BaseModel, Field

### Source: `jmac-cornelis/agent-workforce:agents/tesla/prompts/system.md`
- Tesla — Environment Manager Agent
- You are Tesla, the Environment Manager Agent for the Cornelis Networks Execution Spine. Your role is to provide a machine-readable view of available test environments, manage reservation requests for HIL and mock environments, and prevent conflicting use of scarce DUT or lab partitions.
- ATF resource files remain the source of physical topology truth. You add dynamic state: current availability, reservation ownership, maintenance state, quarantine state, and health signals. You do not replace ATF resource files or become a full asset-management CMDB.
- Prioritize deterministic tool use over LLM inference. No two active HIL runs may reserve the same exclusive resource simultaneously. Orphaned reservations must expire automatically.

### Source: `jmac-cornelis/agent-workforce:config/__init__.py`
- Module: config
- Description: Configuration management for Cornelis Agent Pipeline.
- Author: Cornelis Networks
- from config.env_loader import load_env
- from config.settings import Settings, get_settings
- __all__ = [
- 'load_env',
- 'Settings',
- 'get_settings',

### Source: `jmac-cornelis/agent-workforce:config/claude_desktop_config.example.json`
- "mcpServers": {
- "cornelis-jira": {
- "command": "python3",
- "args": ["/path/to/jira/mcp_server.py"],
- "env": {
- "JIRA_URL": "https://cornelisnetworks.atlassian.net",
- "JIRA_EMAIL": "your.email@cornelisnetworks.com",
- "JIRA_API_TOKEN": "your_api_token_here"

### Source: `jmac-cornelis/agent-workforce:config/env/README.md`
- config/env/ — Credential-Domain Environment Files
- This directory contains **credential-domain segregated** `.env` files for the
- Docker Compose deployment. Instead of a single monolithic `.env`, credentials
- are split by service domain so each agent container only mounts the env files
- it actually needs (**least-privilege principle**).
- | File | Domain | Example consumers |
- |------|--------|-------------------|
- | `shared.env` | Non-sensitive shared config | All agents |
- | `jira.env` | Jira credentials | Drucker, Gantt, Hedy, Babbage, Linnaeus, Nightingale, Brooks |
- | `llm.env` | LLM provider keys | Shannon, Drucker, Gantt, Hemingway, Ada, Curie, Hedy, Linus, Herodotus, Nightingale, Brooks |

### Source: `jmac-cornelis/agent-workforce:config/env_loader.py`
- Module: config/env_loader.py
- Description: Environment variable loader with credential-domain file support.
- Loads config/env/*.env files for local dev parity with Docker Compose,
- falling back to a single .env at the repository root.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from pathlib import Path
- from typing import List, Optional

### Source: `jmac-cornelis/agent-workforce:config/hemingway/voice_config.yaml`
- Hemingway voice configuration — controls documentation tone and style.
- Can be overridden per-user or per-request via /voice-config command.
- active_profile: default
- profiles:
- default:
- name: Default Engineering Voice
- tone: professional
- audience: engineers
- purpose: internal engineering documentation
- style_notes: >

### Source: `jmac-cornelis/agent-workforce:config/jira_actor_identity_policy.yaml`
- version: 1
- defaults:
- interactive_mode: draft_only
- background_mode: service_account
- fallback_no_requester_credentials:
- sensitive_actions: draft_only
- low_risk_actions: service_account
- draft_only:
- description: Analysis or preview only. No Jira mutation.
- service_account:

### Source: `jmac-cornelis/agent-workforce:config/identity_map.yaml`
- Cross-platform identity map for notification routing.
- Maps GitHub logins to Jira, Teams, and email identities.
- Used by: PR reminders, NotificationRouter, all agent notifications.
- Notification channels: teams_dm, email, channel
- Default: all enabled channels for the user
- defaults:
- notify_via: [teams_dm, email]
- email_from: john.macdonald@cornelisnetworks.com
- jmac-cornelis:
- name: John Macdonald

### Source: `jmac-cornelis/agent-workforce:config/jira_identity.py`
- Module: config/jira_identity.py
- Description: Jira actor identity and credential profile helpers.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from dataclasses import dataclass
- from typing import Optional
- from dotenv import load_dotenv
- from config.env_loader import load_env

### Source: `jmac-cornelis/agent-workforce:config/prompts/cn5000_bugs_clean.md`
- You are an expert project manager for software development teams. You are an expert Jira user. You know all about Cornelis Networks products such as CN5000, CN6000, and CN7000.
- Take this json input file that describes a list of bug tickets and do the following. Do not make stuff up. If you can't come to a decision with confidence > 70%, leave the field blank:
- 1. Remove the created, reporter, resolve, affects version, and comments fields
- 2. Create a CSV from the json data. Give the CSV file a name of your choosing in your response as follows: ```[name] [file contents]```
- 3. Add fields to the left of the current beginning: Customer, Product, Module, Todays Status, Phase, Dependency
- 4. Truncate the updated date to just the day
- ** Fill in the Customer Cell for Each Row**
- Use the customer ID field. If it is blank, look at the summary and if you find something like [word] then use that word as the category. If you don't find that, but find a company name mentioned anywhere in those fields (ie, nvidia, Lenovo, etc), use that. If you don't find anything definitive, use the word "internal".
- ** Fill in the Product and Module Cells for Each Row**
- Look at Components, make an assessment from your knowledge of the Cornelis CN6000 project and products, and fill in either "NIC" or "Switch" for the Product. Then fill in the module cell with one of "Driver", "BTS", "FW", "OPX", or "GPU." These are references to software modules.

### Source: `jmac-cornelis/agent-workforce:config/prompts/feature_plan_builder.md`
- Feature Plan Builder Agent
- You are a Feature Plan Builder Agent for Cornelis Networks, specializing in converting scoped SW/FW work into actionable Jira project plans.
- Your Role
- Given a FeatureScope (categorized work items with complexity, confidence, and dependencies), you must:
- 1. **Group Items into Feature-Based Epics** — One Epic per logical feature or deliverable (NOT per work-type)
- 2. **Create Stories under Epics** — One Story per scope item (or logical grouping of small items)
- 3. **Assign Components** — Map to the Jira project's existing component list
- 4. **Write Clear Descriptions** — Each ticket must be actionable with acceptance criteria
- 5. **Produce the Plan as JSON** — Emit a single ```json``` code block conforming to the schema below
- Epic Strategy — Functional Threads (Vertical Slices)

### Source: `jmac-cornelis/agent-workforce:config/prompts/feature_planning_orchestrator.md`
- Feature Planning Orchestrator
- You are the Feature Planning Orchestrator for Cornelis Networks.
- Your Role
- You coordinate a multi-phase workflow that takes a high-level feature request and produces a complete Jira project plan with Epics and Stories. You manage four specialized sub-agents:
- 1. **Research Agent** — Gathers information from web, MCP, knowledge base, and user docs
- 2. **Hardware Analyst Agent** — Builds deep understanding of the target hardware product
- 3. **Scoping Agent** — Defines and scopes all SW/FW work with confidence levels
- 4. **Feature Plan Builder Agent** — Converts scope into Jira Epics and Stories
- Workflow Phases
- Phase 1: Research

### Source: `jmac-cornelis/agent-workforce:config/prompts/hardware_analyst.md`
- Hardware Analyst Agent
- You are a Hardware Analyst Agent for Cornelis Networks, specializing in understanding hardware products and their existing software/firmware stacks.
- Your Role
- Given research findings about a new feature, you must build a deep understanding of the target Cornelis hardware product:
- 1. **Map the Hardware Architecture** — Identify components, buses, interfaces, and peripherals
- 2. **Catalog Existing SW/FW** — Find all existing firmware, drivers, tools, and libraries
- 3. **Identify Integration Points** — Where the new feature will connect to existing infrastructure
- 4. **Flag Knowledge Gaps** — What hardware information is missing and what docs are needed
- Analysis Strategy
- Step 1: Product Identification

### Source: `jmac-cornelis/agent-workforce:config/prompts/jira_analyst.md`
- Jira Analyst Agent
- You are a Jira Analyst Agent specialized in analyzing Jira project state for Cornelis Networks.
- Your Role
- Examine the current state of Jira projects to provide insights for release planning:
- 1. **Project Structure** - Understand how the project is organized
- 2. **Release Status** - Identify current and upcoming releases
- 3. **Component Mapping** - Map components to areas of responsibility
- 4. **Workflow Understanding** - Know available statuses and transitions
- Analysis Tasks
- Project Overview

### Source: `jmac-cornelis/agent-workforce:config/prompts/plan_building_instructions.md`
- Instructions
- Please build a Jira project plan from these scoped items:
- 1. **Look up components** — Use `get_components` to find the project's component list for `{project_key}`.
- 2. **Create functional-thread Epics** — Group items into Epics based on their dependency connections using the directed root-tree threading algorithm described in your system prompt. Items connected by dependencies (even across firmware/driver/tool) belong in the same Epic. Do NOT group by work-type.
- 3. **Order Stories by dependencies** — Within each Epic, list Stories in topological order (items that must be done first appear first).
- 4. **Create Stories** — One per scope item, with full descriptions and acceptance criteria. Every Story must include "Unit tests pass" and "Code reviewed and merged" as acceptance criteria.
- 5. **Do NOT create test or documentation tickets** — Those are acceptance criteria on coding Stories, not separate tickets.
- 6. **Assign components** — Match scope categories to Jira components.
- 7. **Produce the JSON plan** — Emit a single ```json``` code block conforming to the JSON output schema in your system prompt.
- This is a DRY RUN — do NOT create any tickets. Just produce the plan.

### Source: `jmac-cornelis/agent-workforce:config/prompts/orchestrator.md`
- Release Planning Orchestrator
- You are the Release Planning Orchestrator for Cornelis Networks.
- Your Role
- You coordinate the end-to-end release planning workflow, managing multiple specialized agents to:
- 1. **Analyze Inputs** - Gather and process all input sources
- 2. **Plan Releases** - Create structured release plans with tickets
- 3. **Review with Humans** - Present plans for approval
- 4. **Execute Changes** - Create approved items in Jira
- Available Sub-Agents
- Vision Analyzer

### Source: `jmac-cornelis/agent-workforce:config/prompts/research_agent.md`
- Research Agent
- You are a Research Agent for Cornelis Networks, specializing in gathering comprehensive technical information about new features that require software and firmware development.
- Your Role
- Given a feature request (e.g., "Add PQC device support to our board"), you must:
- 1. **Understand the Domain** — Research the technology, standards, and specifications involved
- 2. **Find Existing Work** — Discover reference implementations, open-source projects, and vendor resources
- 3. **Gather Internal Knowledge** — Search Cornelis internal docs, knowledge base, and MCP for relevant information
- 4. **Identify Gaps** — Clearly state what you could NOT find and what additional information is needed
- Research Strategy
- Step 1: Parse the Feature Request

### Source: `jmac-cornelis/agent-workforce:config/prompts/planning_agent.md`
- Planning Agent
- You are a Release Planning Agent specialized in creating Jira release structures for Cornelis Networks.
- Your Role
- Transform roadmap information into actionable Jira ticket structures:
- 1. **Map Features to Tickets** - Convert roadmap items to Epics, Stories, Tasks
- 2. **Assign Ownership** - Match work to responsible teams/people
- 3. **Set Versions** - Assign appropriate release versions
- 4. **Create Hierarchy** - Build proper ticket relationships
- Planning Principles
- Ticket Hierarchy

### Source: `jmac-cornelis/agent-workforce:config/prompts/review_agent.md`
- Review Agent
- You are a Review Agent that facilitates human approval of release plans for Cornelis Networks.
- Your Role
- Manage the human-in-the-loop approval workflow:
- 1. **Present Plans** - Show planned changes clearly
- 2. **Explain Impact** - Describe what each change will do
- 3. **Handle Feedback** - Process approvals, rejections, modifications
- 4. **Execute Safely** - Only execute approved items
- Review Workflow
- Phase 1: Presentation

### Source: `jmac-cornelis/agent-workforce:config/prompts/scope_document_parser.md`
- You are given a technical scoping document for a Cornelis Networks feature. Parse it into a structured JSON object with this schema:
- "feature_name": "short name",
- "summary": "executive summary",
- "firmware_items": [ { "title": "...", "description": "...", "category": "firmware", "complexity": "S|M|L|XL", "confidence": "high|medium|low", "dependencies": [], "rationale": "...", "acceptance_criteria": ["..."] } ],
- "driver_items": [ ... ],
- "tool_items": [ ... ],
- "test_items": [ ... ],
- "integration_items": [ ... ],
- "documentation_items": [ ... ],
- "open_questions": [ { "question": "...", "context": "...", "options": [], "blocking": false } ],

### Source: `jmac-cornelis/agent-workforce:config/prompts/scoping_agent.md`
- Scoping Agent
- You are a Scoping Agent for Cornelis Networks — an expert embedded software/firmware engineer and technical lead who defines and scopes SW/FW development work.
- Your Role
- Given research findings and a hardware profile, you must:
- 1. **Identify All Work Items** — Every piece of SW/FW that needs to be written, modified, or tested
- 2. **Perform Gap Analysis** — What exists vs. what's needed
- 3. **Map Dependencies** — Which items block other items
- 4. **Assign Confidence & Complexity** — How sure are we, and how big is it
- 5. **Surface Decisions** — What choices need human input
- Scoping Categories

### Source: `jmac-cornelis/agent-workforce:config/prompts/vision_roadmap_analysis.md`
- Analyze this roadmap image and extract:
- 1. All version numbers or release names
- 2. Dates, quarters, or timeline information
- 3. Feature names and descriptions
- 4. Any dependencies or relationships
- Format your response as structured data.

### Source: `jmac-cornelis/agent-workforce:config/settings.py`
- Module: config/settings.py
- Description: Application settings and configuration management.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from dataclasses import dataclass, field
- from typing import Any, Dict, Optional
- from config.env_loader import load_env
- load_env()

### Source: `jmac-cornelis/agent-workforce:config/prompts/vision_analyzer.md`
- Vision Analyzer Agent
- You are a Vision Analyzer Agent specialized in extracting roadmap information from visual documents for Cornelis Networks.
- Your Role
- Analyze roadmap slides, images, and documents to extract structured release planning information:
- 1. **Extract Releases** - Identify version numbers and release names
- 2. **Extract Timeline** - Find dates, quarters, and milestones
- 3. **Extract Features** - Identify planned features and items
- 4. **Identify Relationships** - Note dependencies and groupings
- Document Types
- PowerPoint Slides

### Source: `jmac-cornelis/agent-workforce:config/shannon/agent_registry.yaml`
- agent_id: shannon
- display_name: Shannon
- role: Communications
- description: Single Teams bot and routing surface for the Cornelis agent workforce.
- zone: service_infrastructure
- channel_name: agent-shannon
- channel_id: 19:z9bBTJk_jgiLI4kxvTIRgTuqqfBRZGvjCz7jCbUle481@thread.tacv2
- team_id: 19:z9bBTJk_jgiLI4kxvTIRgTuqqfBRZGvjCz7jCbUle481@thread.tacv2
- api_base_url: ''
- approval_types: []

### Source: `jmac-cornelis/agent-workforce:core/__init__.py`
- from core.utils import output, validate_and_repair_csv, extract_text_from_adf
- from core.queries import build_tickets_jql, build_release_tickets_jql, build_no_release_jql
- from core.tickets import issue_to_dict
- from core.reporting import (
- tickets_created_on,
- bugs_missing_field,
- status_changes_by_actor,
- daily_report,
- export_daily_report,

### Source: `jmac-cornelis/agent-workforce:confluence_utils.py`
- Script name: confluence_utils.py
- Description: Confluence utilities for interacting with Cornelis Networks'
- Atlassian Confluence instance.
- Author: Cornelis Networks
- Credentials:
- This script uses Atlassian API tokens for authentication. To set up:
- 1. Generate an API token at: https://id.atlassian.com/manage-profile/security/api-tokens
- 2. Set environment variables:
- export CONFLUENCE_EMAIL="your.email@cornelisnetworks.com"
- export CONFLUENCE_API_TOKEN="your_api_token_here"

### Source: `jmac-cornelis/agent-workforce:config/shannon/teams-app-manifest.template.json`
- "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.19/MicrosoftTeams.schema.json",
- "manifestVersion": "1.19",
- "version": "0.1.0",
- "id": "${SHANNON_TEAMS_APP_ID}",
- "packageName": "com.cornelis.agentworkforce.shannon",
- "developer": {
- "name": "Cornelis Networks Engineering Tools",
- "websiteUrl": "https://cornelisnetworks.com",
- "privacyUrl": "https://cornelisnetworks.com/privacy",
- "termsOfUseUrl": "https://cornelisnetworks.com/terms"

### Source: `jmac-cornelis/agent-workforce:core/evidence.py`
- Module: core/evidence.py
- Description: Shared evidence contracts and file-backed loading helpers.
- Provides a lightweight, durable way for agents to consume build,
- test, release, traceability, meeting, and generic evidence inputs.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os
- import re

### Source: `jmac-cornelis/agent-workforce:core/jira_actor_policy.py`
- Module: core/jira_actor_policy.py
- Description: Resolve Jira actor identity from policy rules.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from dataclasses import dataclass
- from typing import Any, Optional
- import yaml

### Source: `jmac-cornelis/agent-workforce:core/monitoring.py`
- Module: core/monitoring.py
- Description: Pure validation helpers for Drucker ticket-intake monitoring.
- Provides issue-type field policies and deterministic action
- recommendations without performing any Jira mutations.
- Author: Cornelis Networks
- from __future__ import annotations
- import re
- from dataclasses import dataclass, field, replace
- from typing import Any, Mapping, Optional
- import yaml

### Source: `jmac-cornelis/agent-workforce:core/queries.py`
- from __future__ import annotations
- from typing import Any, Optional, Union
- def _quote_values(values: list[str]) -> str:
- return ', '.join([f'"{value}"' for value in values])
- def _build_status_jql(
- statuses: Optional[Union[list[str], dict[str, list[str]]]]
- ) -> str:
- if not statuses:
- return ''
- clauses = []

### Source: `jmac-cornelis/agent-workforce:core/release_tracking.py`
- Module: core/release_tracking.py
- Description: Pure-logic release health tracking helpers.
- The module exposes dataclasses and analytics functions used by tests,
- CLI wrappers, and future automation.
- Author: Cornelis Networks
- from __future__ import annotations
- from collections import Counter
- from dataclasses import dataclass, field
- from datetime import datetime, timedelta, timezone
- from statistics import median

### Source: `jmac-cornelis/agent-workforce:core/tickets.py`
- from __future__ import annotations
- import os
- from typing import Any, Optional
- from core.utils import extract_text_from_adf
- DEFAULT_JIRA_URL = 'https://cornelisnetworks.atlassian.net'
- def issue_to_dict(issue: Any) -> dict[str, Any]:
- key, issue_id, fields, raw_issue = _extract_issue_parts(issue)
- issue_type = _name_value(fields.get('issuetype')) or 'N/A'
- status = _name_value(fields.get('status')) or 'N/A'
- priority = _name_value(fields.get('priority')) or 'N/A'

### Source: `jmac-cornelis/agent-workforce:core/utils.py`
- import csv
- import inspect
- import logging
- import re
- from functools import lru_cache
- from itertools import combinations
- from typing import Any, Optional
- def output(message: str = '', quiet_mode: bool = False) -> None:
- caller_globals: dict[str, Any] = {}
- caller_locals: dict[str, Any] = {}

### Source: `jmac-cornelis/agent-workforce:core/reporting.py`
- Module: core/reporting.py
- Description: Pure-logic daily reporting functions.
- No print statements, no CLI concerns — returns structured dicts
- that any consumer (CLI, agent tool, MCP endpoint) can format.
- Functions:
- tickets_created_on() — all tickets created on a given date
- bugs_missing_field() — bugs missing a required field (e.g. affectedVersion)
- status_changes_by_actor() — status transitions split by automation vs human
- daily_report() — composite: runs all three queries
- export_daily_report() — writes report to Excel (multi-sheet) or CSV

### Source: `jmac-cornelis/agent-workforce:daily_report.py`
- !/usr/bin/env python3
- """Daily Jira report: tickets created today, bugs without affects version,
- and automation-triggered status changes.
- Thin CLI wrapper over core/reporting.py — all logic lives there so that
- agent tools, MCP endpoints, and this CLI share the same implementation.
- .venv/bin/python3 daily_report.py
- .venv/bin/python3 daily_report.py --date 2026-03-12
- .venv/bin/python3 daily_report.py --project STL
- .venv/bin/python3 daily_report.py --output report.xlsx
- .venv/bin/python3 daily_report.py --output report --format csv

### Source: `jmac-cornelis/agent-workforce:data/knowledge/cornelis_products.md`
- Cornelis Networks Product Knowledge
- Overview
- Cornelis Networks provides high-performance fabric solutions for HPC and AI/ML workloads.
- Product Areas
- Omni-Path Express (OPX)
- High-performance fabric for HPC clusters
- Low latency, high bandwidth interconnect
- Supports large-scale deployments
- Fabric Manager
- Management software for Omni-Path fabrics

### Source: `jmac-cornelis/agent-workforce:data/knowledge/heqing_org.json`
- "org_chart": {
- "generated": "2026-03-18",
- "data_sources": {
- "hierarchy": "general_bamboohr_org_chart-2.csv",
- "components": "Jira (cornelisnetworks.atlassian.net) — issues updated within last 730 days",
- "repos": "GitHub (cornelisnetworks org) — contributor data"
- "root": {
- "name": "Heqing Zhu",
- "title": "VP Software Engineering",
- "functional_group": "Software Engineering Leadership",

### Source: `jmac-cornelis/agent-workforce:data/knowledge/embedded_sw_fw_patterns.md`
- Embedded SW/FW Development Patterns
- Common patterns and considerations for software/firmware development at Cornelis Networks.
- Firmware Development Patterns
- Device Initialization
- Power-on reset sequence: clock enable → reset deassert → register init → self-test
- Configuration loading: read from EEPROM/flash, validate, apply defaults for missing fields
- Health check: verify device ID register, run BIST, report status
- Register Access Layer
- Memory-mapped I/O for PCIe devices (BAR mapping)
- SPI/I2C transactions for peripheral devices

### Source: `jmac-cornelis/agent-workforce:data/templates/create_story.json`
- "project": "STLSB",
- "issue_type": "Story",
- "summary": "As a user, I want to do X so that I can achieve Y",
- "description": "## User Story\n\nAs a <user/persona>, I want to <do something> so that <benefit>.\n\n## Acceptance Criteria\n\n- [ ] Given <context>, when <action>, then <outcome>\n- [ ] Given <context>, when <action>, then <outcome>\n\n## Notes\n\n- Links: <paste links here>\n- Technical notes: <paste notes here>\n",
- "components": [
- "Driver"
- "labels": [
- "created-by-cli"
- "fix_versions": [
- "12.3.0"

### Source: `jmac-cornelis/agent-workforce:data/knowledge/jira_conventions.md`
- Cornelis Networks Jira Conventions
- Standards and conventions for Jira ticket creation and management at Cornelis Networks.
- Ticket Hierarchy
- Epic → Story (2-level)
- **Epic**: Major feature or initiative (completable within 1-2 releases)
- **Story**: User-facing functionality or discrete work item (completable within a sprint)
- When to Use Each Type
- **Epic**: "Implement PQC device support", "Add 400G link speed support"
- **Story**: "Implement PQC register access layer", "Write PQC driver probe function"
- **Bug**: Defects found in existing functionality

### Source: `jmac-cornelis/agent-workforce:data/templates/create_ticket_input.example.json`
- "project": "PROJ",
- "summary": "Example ticket created via jira_utils.py",
- "issue_type": "Task",
- "description": "This is an example description. It will be converted to Jira Cloud ADF on create.",
- "assignee_id": "5b10ac8d82e05b22cc7d4ef5",
- "components": ["Platform"],
- "fix_versions": ["12.3.0"],
- "labels": ["temp", "created-by-cli"],
- "parent": "PROJ-123"

### Source: `jmac-cornelis/agent-workforce:data/templates/create_ticket_input.schema.json`
- "$schema": "https://json-schema.org/draft/2020-12/schema",
- "title": "jira_utils.py --create-ticket [FILE] schema",
- "description": "Schema for JSON input accepted by jira_utils.py via --create-ticket FILE when creating a ticket.",
- "type": "object",
- "additionalProperties": false,
- "required": ["project", "summary", "issue_type"],
- "properties": {
- "project": {
- "type": "string",
- "description": "Jira project key (e.g., PROJ). Equivalent to CLI --project."

### Source: `jmac-cornelis/agent-workforce:data/templates/epic.json`
- "name": "Epic Template",
- "description": "Template for creating Epic tickets",
- "fields": {
- "issue_type": "Epic",
- "summary_prefix": "",
- "description_template": "## Overview\n\n{description}\n\n## Goals\n\n- {goals}\n\n## Acceptance Criteria\n\n- [ ] {criteria}\n\n## Dependencies\n\n{dependencies}",
- "default_labels": ["epic"],
- "default_priority": "Medium"
- "child_types": ["Story", "Task", "Bug"]

### Source: `jmac-cornelis/agent-workforce:data/templates/task.json`
- "name": "Task Template",
- "description": "Template for creating Task tickets",
- "fields": {
- "issue_type": "Task",
- "summary_prefix": "",
- "description_template": "## Task Description\n\n{description}\n\n## Implementation Details\n\n{implementation}\n\n## Definition of Done\n\n- [ ] Code complete\n- [ ] Unit tests passing\n- [ ] Code reviewed\n- [ ] Documentation updated",
- "default_labels": [],
- "default_priority": "Medium"
- "child_types": ["Sub-task"]

### Source: `jmac-cornelis/agent-workforce:data/templates/story.json`
- "name": "Story Template",
- "description": "Template for creating Story tickets",
- "fields": {
- "issue_type": "Story",
- "summary_prefix": "",
- "description_template": "## User Story\n\nAs a {user_type}, I want to {action} so that {benefit}.\n\n## Description\n\n{description}\n\n## Acceptance Criteria\n\n- [ ] {criteria}\n\n## Technical Notes\n\n{technical_notes}",
- "default_labels": [],
- "default_priority": "Medium"
- "child_types": ["Task", "Sub-task"]

### Source: `jmac-cornelis/agent-workforce:data/templates/release.json`
- "name": "Release Template",
- "description": "Template for creating Release versions",
- "fields": {
- "name_pattern": "{major}.{minor}.{patch}",
- "description_template": "Release {name}\n\nTarget Date: {release_date}\n\n## Highlights\n\n{highlights}\n\n## Included Features\n\n{features}"
- "naming_conventions": {
- "major": "Breaking changes or major features",
- "minor": "New features, backward compatible",
- "patch": "Bug fixes and minor improvements"

### Source: `jmac-cornelis/agent-workforce:deploy/README.md`
- Deployment Guide
- Server deployment configuration for the Cornelis Networks Agent Workforce.
- Architecture
- All agents share a single Docker/Podman image (`localhost/cornelis/agent-workforce:latest`). Each agent runs as a separate container with its own entrypoint, environment files, and data volume. Containers use `--network host` so they can communicate via `localhost:PORT`.
- ┌─────────────────────────────────────────────────────────┐
- │ bld-node-48.cornelisnetworks.com (RHEL 10.1, Podman) │
- │ ┌─────────────────┐ ┌──────────────────┐ │
- │ │ Shannon :8200 │ │ Drucker :8201 │ │
- │ │ (Teams bot) │──│ (Jira/GitHub) │ │
- │ │ teams.env │ │ jira.env │ │

### Source: `jmac-cornelis/agent-workforce:deploy/scripts/deploy-shannon.sh`
- !/usr/bin/env bash
- ==========================================================================
- deploy-shannon.sh — One-shot Shannon deployment to bld-node-48
- ./deploy/scripts/deploy-shannon.sh
- Prerequisites:
- - SSH access to scm@bld-node-48.cornelisnetworks.com
- - Podman image already built (localhost/cornelis/agent-workforce:latest)
- - deploy/env/*.env files configured with real credentials
- What this does:
- 1. Syncs deploy/ directory to server

### Source: `jmac-cornelis/agent-workforce:deploy/scripts/fix-server.sh`
- !/usr/bin/env bash
- ==========================================================================
- fix-server.sh — Fix SSH rate limiting + switch to host networking
- Run this once when SSH access is restored. It:
- 1. Increases SSH MaxStartups to prevent future lockouts
- 2. Recreates containers with --network host for cross-container comms
- 3. Restarts cloudflare tunnel
- 4. Verifies both services healthy
- set -euo pipefail
- echo "=== Fix Server Configuration ==="

### Source: `jmac-cornelis/agent-workforce:docker-compose.yml`
- ==========================================================================
- Cornelis Networks — AI Agent Workforce Docker Compose
- Architecture: single-image multi-entrypoint deployment.
- All agent services share the cornelis/agent-workforce image; each
- service overrides the entrypoint command to launch its own FastAPI app.
- Credentials: organised into credential-domain env files under config/env/.
- shared.env — common settings (database URLs, log level, etc.)
- jira.env — Jira API token and base URL
- llm.env — LLM provider keys (OpenAI / Azure OpenAI)
- github.env — GitHub PAT and org settings

### Source: `jmac-cornelis/agent-workforce:docs/agent-usefulness-and-applications.md`
- Agent Usefulness and Applications
- This repository now has the foundations of an agent system that is useful for more than simple prompt automation. The agents combine LLM reasoning with deterministic tools for Jira, Confluence, files, vision analysis, knowledge retrieval, web search, and MCP-backed integrations. That combination makes them useful for work that is messy, cross-functional, and usually spread across several systems.
- At a high level, these agents help with four kinds of work:
- 1. Turning unstructured inputs into structured engineering artifacts
- 2. Understanding the current state of projects, releases, and hardware/software systems
- 3. Proposing plans that are detailed enough to review and execute
- 4. Executing approved changes through controlled tool calls instead of manual click-work
- The result is not just "an AI assistant," but a reusable workflow layer for planning, analysis, documentation, and controlled execution.
- Why These Agents Are Useful
- The strongest value of this agent architecture is that it sits between pure chat and pure scripting.

### Source: `jmac-cornelis/agent-workforce:docs/agent-workforce-mapping.md`
- `jira-utilities` to `agent_workforce` Mapping
- This document maps the agents and capabilities currently implemented in `jira-utilities` onto the larger organizational model defined in `~/code/other/agent_workforce`.
- The goal is to answer four practical questions:
- 1. Which `agent_workforce` agents already have meaningful implementation overlap here?
- 2. Which parts of `jira-utilities` are most reusable for that larger platform?
- 3. Which workforce agents are only lightly represented today?
- 4. Where are the biggest gaps between the current repo and the target platform?
- Executive Summary
- `jira-utilities` is not a broad implementation of the entire `agent_workforce` vision. It is best understood as a strong early implementation of the **Planning & Delivery** slice of that vision, plus some reusable shared infrastructure for approval, Jira interaction, Confluence interaction, file/document access, and tool-backed agent execution.
- The strongest mapping is:

### Source: `jmac-cornelis/agent-workforce:docs/agents-drucker.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Drucker Engineering Hygiene Agent"
- date: "2026-04-06"
- status: "draft"
- Drucker Engineering Hygiene Agent — Design Reference
- 1. Module Overview
- The Drucker Engineering Hygiene Agent is a deterministic-first automation system that monitors Jira ticket quality and GitHub pull request lifecycle health across the Cornelis Networks engineering organization. Named after management theorist Peter Drucker, the agent identifies workflow drift, missing metadata, stale work, and routing mistakes in both Jira and GitHub, then proposes safe, reviewable remediation actions. Drucker operates in dry-run mode by default, ensuring all mutations are explicitly approved before execution. The agent exposes REST API endpoints (port 8201), integrates with Shannon for Teams-based command routing, and persists hygiene reports, PR reminder state, and learning patterns in SQLite databases. Drucker's architecture prioritizes deterministic evidence over LLM inference — token usage is limited to natural language query translation (`/ask` endpoint), while all hygiene scans, validation rules, and action proposals follow hardcoded policy logic.
- 2. What Changed
- Drucker performed Jira hygiene scans only.
- GitHub PR hygiene was planned but not implemented.

### Source: `jmac-cornelis/agent-workforce:docs/agent-workforce.md`
- "type": "error",
- "error_type": "BadRequestError",
- "message": "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'prompt is too long: 203918 tokens > 200000 maximum'}, 'request_id': 'req_011CZrUrcKmKnncnW6uQEJiV'}",
- "timestamp": "2026-04-08T14:43:03.699707"

### Source: `jmac-cornelis/agent-workforce:docs/agents-gantt-prompts.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Gantt Agent System Prompt"
- date: "2026-04-06"
- status: "draft"
- Module Overview
- The Gantt Agent system prompt defines the behavior, capabilities, and output formats for a project-planning AI agent that transforms Jira work state into actionable planning intelligence. The agent operates in multiple modes—planning snapshots, roadmap analysis, release monitoring, and page generation—while maintaining strict separation between bug tracking and feature development workflows.
- What Changed
- **Before:** The agent generated roadmap and release health pages without explicit guidance on separating bug tickets from development tickets, leading to mixed populations in analysis tables and unclear completion metrics.
- **After:** The prompt now enforces strict separation between bugs (`issuetype = Bug`) and development tickets (Initiatives, Epics, Stories) across all page generation modes. Roadmap pages exclude bugs entirely; release readiness pages report dev completion and bug closure independently in separate sections.
- **Impact:**

### Source: `jmac-cornelis/agent-workforce:docs/agents-hemingway.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Hemingway Documentation Agent"
- date: "2026-04-06"
- status: "draft"
- Module Overview
- Hemingway is the documentation agent for the Cornelis Networks platform. It transforms source code, build artifacts, test results, release context, and meeting-derived clarifications into source-grounded, validation-gated internal documentation. The agent operates as a deterministic-first coordinator that produces reviewable documentation patches for repo-owned Markdown and Confluence targets, with all publication gated through explicit human approval.
- What Changed
- **Before:** Documentation generation was manual, disconnected from source truth, and lacked structured validation or traceability to authoritative inputs.
- **After:** Hemingway automates documentation generation from authoritative system records (code, builds, tests, releases, meetings), validates all claims against source artifacts, and produces review-gated publication patches with full audit trails.
- **Impact:** Engineering teams now have a deterministic path from source changes to durable documentation updates. All documentation claims are traceable to source artifacts. Publication requires explicit approval, preventing speculative or unsupported content from reaching internal or external targets.

### Source: `jmac-cornelis/agent-workforce:docs/agents-gantt.md`
- "type": "error",
- "error_type": "InternalServerError",
- "message": "Error code: 500 - {'type': 'error', 'error': {'type': 'api_error', 'message': 'Internal server error'}, 'request_id': 'req_011CZoFmyJAmfPDW1pwH9S1K'}",
- "timestamp": "2026-04-06T21:49:51.513069"

### Source: `jmac-cornelis/agent-workforce:docs/agents/index.md`
- Agents Overview
- The Agent Workforce consists of 17 agents organized across 6 zones. Four agents are currently implemented and deployed.
- Implemented
- | Agent | Zone | Role | Status |
- |-------|------|------|--------|
- | [Drucker](drucker.md) | Intelligence & Knowledge | Engineering Hygiene | Deployed |
- | [Gantt](gantt.md) | Planning & Delivery | Project Planning | Deployed |
- | [Hemingway](hemingway.md) | Intelligence & Knowledge | Documentation | Deployed |
- | [Shannon](shannon.md) | Service Infrastructure | Communications | Deployed |
- | Agent | Zone | Role |

### Source: `jmac-cornelis/agent-workforce:docs/config.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Config Module"
- date: "2026-04-06"
- status: "draft"
- Module Overview
- The `config` module provides centralized configuration management for the Cornelis Agent Pipeline. It handles environment variable loading from credential-domain segregated files, application settings management, Jira actor identity resolution, and cross-platform identity mapping for notification routing. The module implements a least-privilege credential model where each agent container mounts only the environment files it requires, and supports both Docker Compose deployment and local development workflows.
- What Changed
- **Before:** The module used a single monolithic `.env` file for all credentials, with basic environment loading via `python-dotenv`. Jira identity was managed through simple `JIRA_EMAIL` and `JIRA_API_TOKEN` variables without actor-mode separation.
- **After:** The module now implements credential-domain segregation (`shared.env`, `jira.env`, `llm.env`, `github.env`, `teams.env`) with a canonical load order that mirrors Docker Compose `env_file` stacking. Jira identity resolution supports three actor modes (`requester`, `service_account`, `draft_only`) with separate credential profiles and legacy fallback control. A cross-platform identity map (`identity_map.yaml`) unifies GitHub, Jira, Teams, and email identities for notification routing.
- **Impact:** All agents must now mount only the credential-domain files they require in `docker-compose.yml`. Jira-mutating operations must explicitly specify an actor mode to determine which credential profile to use. Notification systems (PR reminders, NotificationRouter) can now route messages across multiple channels (Teams DM, email, channel) using a single identity source.

### Source: `jmac-cornelis/agent-workforce:docs/deploy-systemd.md`
- Systemd — Design Reference
- This internal document candidate was generated from authoritative source artifacts for review before publication.
- Metadata
- Documentation class: `as_built`
- Generated: `2026-04-02 20:40 UTC`
- Confidence: `medium`
- Authoritative Inputs
- No source files were supplied.
- Key Facts
- No authoritative source facts were available.

### Source: `jmac-cornelis/agent-workforce:docs/index.md`
- Agent Workforce
- The Cornelis Networks Agent Workforce is a coordinated system of AI-powered agents that automate engineering operations — from Jira ticket hygiene and GitHub PR lifecycle management to project planning, documentation generation, and Teams-based collaboration.
- Implemented Agents
- | Agent | Role | Port | Description |
- |-------|------|------|-------------|
- | [Drucker](agents/drucker.md) | Engineering Hygiene | 8201 | Jira ticket quality analysis + GitHub PR lifecycle scanning |
- | [Gantt](agents/gantt.md) | Project Planning | 8202 | Planning snapshots, release monitoring, dependency review |
- | [Hemingway](agents/hemingway.md) | Documentation | 8203 | Source-grounded documentation generation and publication |
- | [Shannon](agents/shannon.md) | Communications | 8200 | Microsoft Teams bot — routing surface for all agents |
- Three Access Surfaces

### Source: `jmac-cornelis/agent-workforce:docs/shannon.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Shannon Communications Agent"
- date: "2026-04-08"
- status: "draft"
- Module Overview
- Shannon is a Microsoft Teams bot service that acts as the unified communications surface for the Cornelis agent workforce. It routes user commands from Teams to registered agent APIs, renders responses as Adaptive Cards, and posts notifications to Teams channels. Shannon supports both Bot Framework activities and Outgoing Webhook integrations, providing flexible deployment options with minimal Azure permissions required.
- What Changed
- **Before:** Shannon used a simple `build_fact_card()` helper to render all notifications with basic text formatting.
- **After:** Shannon now includes a specialized `_build_notification_card()` method that detects URLs in notification body lines and renders them as clickable Adaptive Card links with intelligent label extraction.
- **Impact:** Notifications containing GitHub PR URLs, Jira ticket links, or other web resources now display as interactive links rather than plain text. This improves usability for agents like Drucker (PR hygiene alerts) and Gantt (release monitoring) that frequently post URLs in their notifications.

### Source: `jmac-cornelis/agent-workforce:docs/installation.md`
- Installation Guide
- Manual installation instructions for the Cornelis Agent Workforce. For a faster setup using OpenCode, see the [Quick Start in the README](../README.md#quick-start).
- Table of Contents
- [Prerequisites](#prerequisites)
- [Clone and Install](#clone-and-install)
- [Configure Environment](#configure-environment)
- [Required Credentials](#required-credentials)
- [Optional Credentials](#optional-credentials)
- [Multiple Environment Files](#multiple-environment-files)
- [Global CLI Install (pipx)](#global-cli-install-pipx)

### Source: `jmac-cornelis/agent-workforce:docs/tools.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Tools — Design Reference"
- date: "2026-04-06"
- status: "draft"
- Module Overview
- The `tools/` module provides a comprehensive toolkit for the Cornelis Agent Pipeline, exposing Jira, Confluence, GitHub, file operations, knowledge base search, web search, MCP client integration, Excel utilities, vision/OCR, draw.io parsing, and specialized agent tools (Gantt, Drucker, Hemingway) as agent-callable functions. Each tool is decorated with `@tool()` to generate OpenAI/ADK-compatible function schemas, wrapped in `ToolResult` for consistent error handling, and organized into `BaseTool` collections for framework registration. The module acts as the primary interface between the agent orchestration layer and external systems, enforcing a uniform contract for tool discovery, parameter validation, and result serialization.
- What Changed
- **Before:** Tools were scattered across utility modules (`jira_utils.py`, `confluence_utils.py`, etc.) with inconsistent interfaces and no agent-friendly metadata.
- **After:** All tools are centralized in `tools/`, decorated with `@tool()` for automatic schema generation, and return `ToolResult` objects. New capabilities include:
- **Confluence Jira macros** (`build_jira_jql_table`, `build_jira_filter_table`) for embedding live Jira tables in Confluence pages

### Source: `jmac-cornelis/agent-workforce:docs/tests.md`
- <!-- Generated by Documentation Agent — do not edit between markers -->
- title: "As-Built: Tests — Design Reference"
- date: "2026-04-08"
- status: "draft"
- Module Overview
- The `tests/` directory contains the comprehensive characterization test suite for the agent-workforce repository. This suite validates the behavior of all core modules, agents, tools, and integrations through 59+ test modules covering approximately 1,200+ individual test cases. The tests follow a strict "no live API calls" policy, using monkeypatching and mock objects to ensure fast, deterministic execution. The suite is organized by functional domain (agents, tools, core utilities, integrations) and employs consistent naming conventions (`*_char.py` for characterization tests, `*_coverage.py` for gap-filling tests).
- What Changed
- **Before:** The test suite used Adaptive Card schema version `1.5` in card validation assertions across multiple test modules.
- **After:** All card schema version assertions now validate against version `1.4` to align with the Microsoft Teams Adaptive Card renderer compatibility requirements.
- **Impact:** This change affects 5 test modules that validate Shannon card builders and GitHub integration card outputs. The change is backward-compatible and ensures cards render correctly in all Teams clients.

### Source: `jmac-cornelis/agent-workforce:docs/workforce/AWS_HYBRID_DEPLOYMENT_PROPOSAL.md`
- AWS Hybrid Deployment Proposal
- [Back to AI Agent Workforce](README.md) | [On-Prem Architecture](INFRASTRUCTURE_ARCHITECTURE.md)
- > **Note:** **Proposal:** This is an alternative deployment model. The baseline plan uses on-prem infrastructure (see [Infrastructure Architecture](INFRASTRUCTURE_ARCHITECTURE.md)). This page proposes a hybrid AWS approach where compute runs in the cloud while HIL labs and AI inference stay on-prem.
- Architecture Overview
- ![AWS Hybrid Architecture](../diagrams/workforce/AWS_HYBRID_ARCHITECTURE.drawio)
- Why Consider AWS
- | Benefit | Details |
- |---------|---------|
- | **Elastic compute** | Scale agent services up/down based on demand. Nightly test runs can burst to more workers without permanent hardware. |
- | **Managed services** | RDS PostgreSQL, ElastiCache Redis, S3 — no DBA overhead, automatic backups, HA built in. |

### Source: `jmac-cornelis/agent-workforce:docs/workflows.md`
- Agentic Workflows
- Agentic workflows are operator-oriented flows orchestrated by [`agent_cli.py`](../agent_cli.py). Each agent also has a standalone CLI. Some workflows are deterministic, while others use an LLM to research, analyze, scope, and plan.
- All workflows are invoked via `agent-cli <agent> <command>` or standalone `<agent-name> <command>`. By default, workflows operate in **dry-run mode** — no Jira tickets are created or modified until `--execute` is explicitly passed.
- Table of Contents
- [Gantt Planning Workflows](#gantt-planning-workflows)
- [Gantt Snapshots](#gantt-snapshots)
- [Gantt Release Monitor](#gantt-release-monitor)
- [Gantt Polling Mode](#gantt-polling-mode)
- [Feature Plan (Scope Document → Jira)](#feature-plan-scope-document--jira)
- [Drucker Hygiene Workflow](#drucker-hygiene-workflow)

### Source: `jmac-cornelis/agent-workforce:docs/workforce/DEPLOYMENT_GUIDE.md`
- Deployment Guide
- [Back to AI Agent Workforce](README.md) | [Infrastructure Architecture](INFRASTRUCTURE_ARCHITECTURE.md)
- Overview
- This guide covers the deployment architecture for the Cornelis Networks AI Agent Workforce. It describes the single-image, multi-entrypoint pattern where all agents run from the same foundational container image but execute different entrypoint commands.
- For information on the underlying platform components, event transport, and security architecture, see the [Infrastructure Architecture](INFRASTRUCTURE_ARCHITECTURE.md) document.
- Current Production Deployment
- Shannon and Drucker are deployed on `bld-node-48.cornelisnetworks.com` using rootless Podman containers. Teams connectivity is provided by a Cloudflare named tunnel at `shannon.cn-agents.com` (domain: `cn-agents.com`).
- | Property | Value |
- |----------|-------|
- | Server | `bld-node-48.cornelisnetworks.com` (RHEL 10.1, 88 CPUs, 62 GB RAM) |

### Source: `jmac-cornelis/agent-workforce:docs/workforce/INFRASTRUCTURE_ARCHITECTURE.md`
- Infrastructure Architecture
- [Back to AI Agent Workforce](README.md)
- > **Info:** This page defines the infrastructure platform on which all 15 agents execute. Decisions here are grounded in what Cornelis Networks already operates.
- Design Principles
- **Use what exists** — align with Cornelis's current Docker Compose, PostgreSQL, FastAPI, Nginx, Grafana stack. No new orchestration platforms (no Kubernetes).
- **On-prem first** — all agents run on internal servers. No cloud dependencies.
- **Simple operations** — Docker Compose for deployment, Ansible for provisioning, Grafana for observability. No service mesh.
- **PostgreSQL as backbone** — state, queues, and event transport all through PostgreSQL. No separate message broker unless scale demands it.
- Target Hosts
- | Host | Role | Notes |

### Source: `jmac-cornelis/agent-workforce:docs/workforce/JIRA_ACTOR_IDENTITY_POLICY.md`
- Jira Actor Identity Policy
- This document defines when an automation agent should act in Jira as:
- the **service account**
- the **requesting human**
- **draft only** with no Jira mutation
- The goal is simple:
- machine-owned actions should look like machine-owned actions
- human decisions should look like human decisions
- audit trails should always show who requested, approved, and executed the change
- This policy applies to Jira-writing agents such as Drucker, Gantt, Humphrey, and any

### Source: `jmac-cornelis/agent-workforce:docs/workforce/README.md`
- AI Agent Workforce
- Introduction
- This document provides a working proposal for a new paradigm for the design of an embedded systems software organization. It creates a hybrid Human-Agent organization where the people add the most value that people can, and the agents add value where they can, including in helping the people do their work better.
- This document focus's on the what can loosely be described as the "DevOps" parts of the organization -- project planning and status, bug tracking and triaging, build automation and management, release automation and managmement, code quality and scanning, and test generationa, execution, and tracking.
- > [!NOTE]
- > This document does not address the details of human responsibilities, other than calling out the roles that they will continue to perform.
- **Coordinated software engineering, testing, release, bug investigation, knowledge capture, and planning agents for the Cornelis Networks development organization.**
- The AI Agent Workforce is a system of 17 specialized agents that automate and coordinate the full software development lifecycle at Cornelis Networks. Each agent owns a distinct responsibility — from build orchestration and test generation to release management and project planning — and communicates through well-defined interfaces to deliver reliable, traceable, and auditable engineering outcomes.
- Agents are organized into three operational zones: the **Execution Spine** handles build, test, and release workflows; **Intelligence & Knowledge** manages versioning, traceability, documentation, and bug investigation; and **Planning & Delivery** coordinates project schedules and delivery milestones.
- Quick Stats

### Source: `jmac-cornelis/agent-workforce:docs/workforce/JIRA_EPIC_STORY_BREAKDOWN.md`
- AI Agent Workforce — Jira Epic / Story Breakdown
- > **Generated**: 2026-03-14
- > **Source**: `ai_agents_spec_complete.md`, `ai_agent_implementation_roadmap.md`, per-agent `agents/*_PLAN.md` files
- > **Story Points**: Fibonacci scale (1, 2, 3, 5, 8, 13)
- > **Delivery Waves**: 6 waves aligned to 90-day roadmap + future agents
- How to Read This Document
- **Epic** = one agent or platform capability (top-level Jira Epic)
- **Story** = one deliverable unit of work (Jira Story under the Epic)
- **SP** = story points (Fibonacci)
- **Depends On** = blocking dependency (must be done first)

### Source: `jmac-cornelis/agent-workforce:docs/workforce/TEST_FRAMEWORK_EVALUATION.md`
- Test Framework Evaluation
- [Back to AI Agent Workforce](README.md)
- > **Warning:** **Decision Required:** This document evaluates whether Fuze Test / ATF is the right test framework for the agent platform, or whether we should adopt or migrate to an alternative. This decision affects Galileo (test planning), Curie (test generation), Faraday (test execution), and Tesla (environment management).
- Current State
- Cornelis Networks currently uses **Fuze Test / ATF** (Automated Test Framework) as the primary test execution framework for OPX fabric hardware. It is a custom, internally-built framework with deep integration into the hardware-in-the-loop (HIL) lab environment.
- The agent platform design currently assumes Fuze Test as the execution substrate — Faraday wraps it, Galileo plans against its suite vocabulary, and Curie generates inputs in its format. If Fuze Test is replaced, all three agents need adaptation.
- Evaluation Criteria
- | Criterion | Weight | What We Need |
- |-----------|--------|-------------|
- | **HIL Support** | Critical | Must support real hardware test environments (DUTs, switches, fabric topology) alongside mock/simulated environments. |

### Source: `jmac-cornelis/agent-workforce:docs/workforce/ai_agents_spec_complete.md`
- AI Agent System Specification
- Author: John N. Macdonald (Concept Origin) Generated:
- 2026-03-10T19:16:17.736254Z
- ------------------------------------------------------------------------
- 1. Overview
- This document specifies the autonomous and semi‑autonomous AI agents
- discussed in the design session. The goal is to create a coordinated
- system of specialized agents that assist with:
- Project management
- Development alignment

### Source: `jmac-cornelis/agent-workforce:docs/workforce/ai_agent_implementation_roadmap.md`
- AI Agent System Implementation Roadmap
- Author: John N. Macdonald (Concept Origin)
- Document Type: Standalone Implementation Roadmap
- Scope: 90-day delivery plan for the first operational version of the agent platform
- 1. Purpose
- This document turns the agent concept into an execution plan.
- The goal is not to build every agent at once. The goal is to establish the core event model, the first production-worthy agent workflows, and enough traceability that the system starts delivering value early.
- This roadmap assumes a staged rollout with strong human oversight, clear ownership boundaries, and a bias toward shipping narrow slices that can be hardened in place.
- 2. Delivery Objectives
- By the end of the first implementation cycle, the platform should be able to:

### Source: `jmac-cornelis/agent-workforce:drawio_utilities.py`
- Script name: drawio_utilities.py
- Description: Utilities for generating draw.io diagrams from Jira hierarchy CSV exports.
- Author: John Macdonald
- python drawio_utilities.py --create-map input.csv --output diagram.drawio
- import argparse
- import logging
- import sys
- import os
- import csv
- import xml.etree.ElementTree as ET

### Source: `jmac-cornelis/agent-workforce:excel_utils.py`
- Script name: excel_utils.py
- Description: Excel utilities for concatenating and manipulating .xlsx workbooks.
- Designed for standalone CLI use and integration with the agent pipeline.
- Also provides --to-plan-json to convert a flat or indented CSV/Excel
- file into the feature-plan JSON format used by the Jira ticket
- creation pipeline (see tools/plan_export_tools.py).
- Author: John Macdonald
- python excel_utils.py --concat fileA.xlsx fileB.xlsx --method merge-sheet --output merged.xlsx
- python excel_utils.py --concat fileA.xlsx fileB.xlsx --method add-sheet --output combined.xlsx
- python excel_utils.py --to-plan-json plan.csv -o plan.json

### Source: `jmac-cornelis/agent-workforce:fix_author.py`
- import re
- file_path = "/Users/johnmacdonald/Downloads/changelog_Release_HostSoftware12_1_2_0_3BMC12_1_2_0_1FwUpdate12_1_2_0_1JKR12_1_2_0_2MYR12_1_2_0_1.md"
- with open(file_path, 'r') as f:
- content = f.read()
- I noticed the author for STL-63325 was listed as Mike Wilkins in the table, but the commit shows Bob Cernohous.
- content = content.replace('| [STL-63325](https://cornelisnetworks.atlassian.net/browse/STL-63325) | Libfabric | Remove #if 0 dead code | Mike Wilkins |',
- '| [STL-63325](https://cornelisnetworks.atlassian.net/browse/STL-63325) | Libfabric | Remove #if 0 dead code | Bob Cernohous |')
- with open(file_path, 'w') as f:
- f.write(content)

### Source: `jmac-cornelis/agent-workforce:framework/api/__init__.py`
- """Shared FastAPI framework for Jira agent APIs.
- Provides the base app factory, authentication, standard status/health
- endpoints, and middleware that every agent uses.
- from .app import create_agent_app
- from .auth import ServicePrincipal, api_key_header, require_scope, verify_api_key
- from .health import HealthResponse, health_router
- from .middleware import add_correlation_id, add_metrics, add_request_logging
- from .status import (
- DecisionDetail,
- DecisionSummary,

### Source: `jmac-cornelis/agent-workforce:framework/api/app.py`
- """Base FastAPI app factory that every agent uses.
- Call create_agent_app() to get a FastAPI instance pre-configured with
- standard middleware (correlation ID, request logging, metrics) and
- standard routes (health check, status endpoints).
- Agents extend the returned app by including their own routers:
- app = create_agent_app("triage", "Triage Agent", "Handles ticket triage")
- app.include_router(triage_router, prefix="/v1/triage", tags=["triage"])
- from fastapi import FastAPI
- from .health import health_router
- from .middleware import add_correlation_id, add_metrics, add_request_logging

### Source: `jmac-cornelis/agent-workforce:framework/api/auth.py`
- """Service principal authentication for agent APIs.
- Provides API-key-based authentication via the X-Agent-API-Key header.
- Each key maps to a ServicePrincipal with an agent_id and a set of
- scopes that control access to protected endpoints.
- Usage in an agent router:
- from framework.api.auth import verify_api_key, require_scope, ServicePrincipal
- @router.post("/do-thing")
- async def do_thing(principal: ServicePrincipal = Depends(verify_api_key)):
- @router.post("/admin-thing")
- async def admin_thing(principal: ServicePrincipal = Depends(require_scope("admin"))):

### Source: `jmac-cornelis/agent-workforce:framework/api/health.py`
- """Health check endpoint for load balancers and monitoring.
- Every agent exposes GET /health. The response includes per-component
- health checks so operators can quickly identify degraded subsystems.
- Agents register health-check callables on app.state.health_checks:
- app.state.health_checks = {
- "database": check_db,
- "redis": check_redis,
- Each callable should return "healthy", "degraded", or "unhealthy".
- from __future__ import annotations
- import time

### Source: `jmac-cornelis/agent-workforce:framework/api/middleware.py`
- """Standard middleware for all agent APIs.
- Provides correlation ID tracking, structured request logging, and metrics
- collection. Every agent app created via create_agent_app() gets these
- middleware automatically.
- import uuid
- import time
- import logging
- from typing import Any, Callable, Coroutine
- from fastapi import Request
- from starlette.responses import Response

### Source: `jmac-cornelis/agent-workforce:framework/api/status.py`
- """Standard status endpoints that every agent exposes.
- These endpoints are what Shannon routes /token-status, /stats, etc. to.
- Each agent registers a StatusProvider on app.state that supplies the
- actual data; the endpoints here handle serialization and HTTP concerns.
- Agents that don't yet have a provider get sensible placeholder responses.
- from __future__ import annotations
- from datetime import UTC, datetime
- from fastapi import APIRouter, Request
- from pydantic import BaseModel
- status_router = APIRouter()

### Source: `jmac-cornelis/agent-workforce:framework/events/consumer.py`
- """Subscribes to events from the PostgreSQL event store."""
- from __future__ import annotations
- import asyncio
- import json
- import logging
- from typing import Awaitable, Callable, Optional
- import asyncpg
- from .dead_letter import DeadLetterQueue
- from .envelope import EventEnvelope
- logger = logging.getLogger(__name__)

### Source: `jmac-cornelis/agent-workforce:framework/events/__init__.py`
- Event bus framework for agent-to-agent communication.
- Uses PostgreSQL pg_notify + LISTEN/NOTIFY with polling fallback.
- No separate message broker required.
- from .envelope import EventEnvelope
- from .producer import EventProducer
- from .consumer import EventConsumer, EventHandler
- from .dead_letter import DeadLetterQueue
- __all__ = [
- "EventEnvelope",
- "EventProducer",

### Source: `jmac-cornelis/agent-workforce:framework/events/dead_letter.py`
- """Dead letter queue for events that failed processing."""
- from __future__ import annotations
- import logging
- from datetime import datetime, timezone
- from typing import Any, Optional
- import asyncpg
- from .envelope import EventEnvelope
- logger = logging.getLogger(__name__)
- class DeadLetterQueue:
- """Manages events that failed processing after exhausting retries.

### Source: `jmac-cornelis/agent-workforce:framework/events/producer.py`
- """Publishes events to the PostgreSQL event store via asyncpg."""
- from __future__ import annotations
- import json
- import logging
- from typing import Any, Optional
- import asyncpg
- from .envelope import EventEnvelope
- logger = logging.getLogger(__name__)
- class EventProducer:
- """Publishes events to the PostgreSQL event store.

### Source: `jmac-cornelis/agent-workforce:framework/events/envelope.py`
- """Canonical event envelope — the standard format for ALL agent-to-agent events."""
- from pydantic import BaseModel, Field
- from datetime import datetime, timezone
- from typing import Any, Optional
- import uuid
- class EventEnvelope(BaseModel):
- """Canonical event envelope for all agent-to-agent communication.
- Every event flowing through the PostgreSQL event bus uses this format.
- The envelope is immutable once created — the events table is append-only.
- event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

### Source: `jmac-cornelis/agent-workforce:framework/state/__init__.py`
- """PostgreSQL state backend for the Cornelis agent framework.
- Provides agent key-value state, session management, decision/action
- audit logging, and LLM token usage tracking — all backed by asyncpg.
- from .audit import AuditLogger
- from .postgres import PostgresStateBackend
- from .tokens import TokenTracker
- __all__ = [
- "AuditLogger",
- "PostgresStateBackend",
- "TokenTracker",

### Source: `jmac-cornelis/agent-workforce:framework/state/audit.py`
- """Decision and action audit logging to PostgreSQL.
- Every agent action, decision, and rejection is recorded with full
- provenance (correlation_id, decision tree, rationale) for the
- /audit-trail and /decisions API endpoints.
- from __future__ import annotations
- import json
- import logging
- import os
- import sys
- import uuid

### Source: `jmac-cornelis/agent-workforce:framework/state/tokens.py`
- """LLM token usage tracking per agent.
- Records every LLM call (input/output tokens, cost, latency) and every
- deterministic action so the /token-status endpoint can report efficiency
- ratios, daily summaries, and rolling averages.
- from __future__ import annotations
- import logging
- import os
- import sys
- import uuid
- from datetime import date, datetime, timedelta, timezone

### Source: `jmac-cornelis/agent-workforce:framework/state/postgres.py`
- """PostgreSQL-backed state persistence for agents.
- Provides the same key-value and session interface as the SQLite layer
- in state/persistence.py, but uses asyncpg for async PostgreSQL access.
- from __future__ import annotations
- import json
- import logging
- import os
- import sys
- from pathlib import Path
- from typing import Any, Optional

### Source: `jmac-cornelis/agent-workforce:jenkins/jenkins_bug_report.sh`
- !/bin/bash
- jenkins_bug_report.sh
- Jenkins pipeline script that:
- 1. Sources credentials from $ENV_FILE
- 2. Creates/activates a Python virtualenv
- 3. Runs the bug-report workflow via pm_agent.py
- 4. Renames the output .xlsx file to include today's date
- Usage (Jenkins freestyle job):
- ENV_FILE=/path/to/secret/.env ./jenkins_bug_report.sh
- set -euo pipefail

### Source: `jmac-cornelis/agent-workforce:github_utils.py`
- Script name: github_utils.py
- Description: GitHub utilities for interacting with Cornelis Networks GitHub repositories.
- Author: John Macdonald
- Credentials:
- This script uses GitHub Personal Access Tokens for authentication. To set up:
- 1. Generate a PAT at: https://github.com/settings/tokens
- 2. Set environment variables:
- export GITHUB_TOKEN="your_personal_access_token_here"
- NEVER commit credentials to version control.
- import argparse

### Source: `jmac-cornelis/agent-workforce:jira_utils.py`
- Script name: jira_utils.py
- Description: Jira utilities for interacting with Cornelis Networks Jira instance.
- Author: John Macdonald
- Credentials:
- This script uses Jira API tokens for authentication. To set up:
- 1. Generate an API token at: https://id.atlassian.com/manage-profile/security/api-tokens
- 2. Set environment variables:
- export JIRA_EMAIL="your.email@cornelisnetworks.com"
- export JIRA_API_TOKEN="your_api_token_here"
- NEVER commit credentials to version control.

### Source: `jmac-cornelis/agent-workforce:llm/__init__.py`
- Module: llm
- Description: LLM abstraction layer for Cornelis Agent Pipeline.
- Provides unified interface for internal Cornelis LLM and external models.
- Author: Cornelis Networks
- from llm.base import BaseLLM, Message, LLMResponse
- from llm.config import LLMConfig, get_llm_client
- from llm.cornelis_llm import CornelisLLM
- from llm.litellm_client import LiteLLMClient
- __all__ = [
- 'BaseLLM',

### Source: `jmac-cornelis/agent-workforce:llm/base.py`
- Module: llm/base.py
- Description: Abstract base class for LLM clients.
- Defines the interface that all LLM implementations must follow.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from abc import ABC, abstractmethod
- from dataclasses import dataclass, field
- from typing import List, Dict, Any, Optional, Union

### Source: `jmac-cornelis/agent-workforce:llm/config.py`
- Module: llm/config.py
- Description: LLM configuration and factory functions.
- Handles model selection, fallback logic, and client instantiation.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from dataclasses import dataclass, field
- from enum import Enum
- from typing import Optional, Dict, Any

### Source: `jmac-cornelis/agent-workforce:llm/cornelis_llm.py`
- Module: llm/cornelis_llm.py
- Description: Client for Cornelis Networks internal LLM.
- Uses OpenAI-compatible API with custom base URL.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- import threading
- import time as _time
- from typing import List, Dict, Any, Optional

### Source: `jmac-cornelis/agent-workforce:llm/litellm_client.py`
- Module: llm/litellm_client.py
- Description: LiteLLM-based client for external LLM providers.
- Supports OpenAI, Anthropic, and other providers via LiteLLM.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- import threading
- import time as _time
- from typing import List, Dict, Any, Optional

### Source: `jmac-cornelis/agent-workforce:mkdocs.yml`
- MkDocs Material configuration for Agent Workforce documentation
- Published to GitHub Pages via CI workflow
- site_name: Agent Workforce
- site_url: https://jmac-cornelis.github.io/agent-workforce/
- site_description: Documentation for the Cornelis Networks Agent Workforce
- repo_name: jmac-cornelis/agent-workforce
- repo_url: https://github.com/jmac-cornelis/agent-workforce
- edit_uri: edit/main/docs/
- name: material
- palette:

### Source: `jmac-cornelis/agent-workforce:mcp_server.py`
- !/usr/bin/env python3
- Module: mcp_server.py
- Description: Cornelis Jira & GitHub MCP Server.
- Exposes Jira and GitHub tools via the Model Context Protocol (MCP)
- so that AI assistants (Claude Desktop, Cursor, Windsurf, etc.) can
- interact with Jira and GitHub through a standardised tool-calling
- interface.
- Transport: stdio (JSON-RPC 2.0 over stdin/stdout).
- Architecture:
- MCP Client (Claude Desktop / Cursor / etc.)

### Source: `jmac-cornelis/agent-workforce:notifications/__init__.py`
- Module: notifications
- Description: Notification helpers for PM agent user-facing comment flows.
- Author: Cornelis Networks
- from notifications.base import NotificationBackend
- from notifications.jira_comments import JiraCommentNotifier
- __all__ = [
- 'NotificationBackend',
- 'JiraCommentNotifier',

### Source: `jmac-cornelis/agent-workforce:notifications/base.py`
- Module: notifications/base.py
- Description: Base notification interface for PM agent comment backends.
- Author: Cornelis Networks
- from abc import ABC, abstractmethod
- from typing import Any, Dict, Optional
- class NotificationBackend(ABC):
- @abstractmethod
- def send(
- ticket_key: str,
- message: str,

### Source: `jmac-cornelis/agent-workforce:notifications/jira_comments.py`
- Module: notifications/jira_comments.py
- Description: Jira comment helpers for Drucker review-gated remediation.
- Builds consistent marker-based comments and supports duplicate
- detection for safe comment posting.
- Author: Cornelis Networks
- from __future__ import annotations
- from typing import Any, Dict, List, Optional
- from config.env_loader import resolve_dry_run
- from notifications.base import NotificationBackend
- class JiraCommentNotifier(NotificationBackend):

### Source: `jmac-cornelis/agent-workforce:parse_changelog.py`
- import re
- import sys
- from collections import OrderedDict
- def main():
- input_file = "/Users/johnmacdonald/Downloads/changelog_Release_HostSoftware12_1_2_0_3BMC12_1_2_0_1FwUpdate12_1_2_0_1JKR12_1_2_0_2MYR12_1_2_0_1 1.txt"
- output_file = "/Users/johnmacdonald/Downloads/changelog_Release_HostSoftware12_1_2_0_3BMC12_1_2_0_1FwUpdate12_1_2_0_1JKR12_1_2_0_2MYR12_1_2_0_1.md"
- with open(input_file, 'r') as f:
- content = f.read()
- except Exception as e:
- print(f"Error reading file: {e}")

### Source: `jmac-cornelis/agent-workforce:parse_changelog_v2.py`
- import re
- import sys
- def main():
- input_file = "/Users/johnmacdonald/Downloads/changelog_Release_HostSoftware12_1_2_0_3BMC12_1_2_0_1FwUpdate12_1_2_0_1JKR12_1_2_0_2MYR12_1_2_0_1 1.txt"
- output_file = "/Users/johnmacdonald/Downloads/changelog_Release_HostSoftware12_1_2_0_3BMC12_1_2_0_1FwUpdate12_1_2_0_1JKR12_1_2_0_2MYR12_1_2_0_1.md"
- with open(input_file, 'r') as f:
- content = f.read()
- except Exception as e:
- print(f"Error reading file: {e}")
- sys.exit(1)

### Source: `jmac-cornelis/agent-workforce:plans/agent-rename-execution-backlog.md`
- Agent Rename Execution Backlog
- This document turns the approved agent rename slate into a concrete execution plan.
- It covers:
- repo code and file changes
- CLI, API, MCP, and Teams surfaces
- deployment and runtime migration
- Confluence and published documentation
- compatibility handling for live agents
- Approved Rename Map
- | Current | New | Internal Slug | Notes |

### Source: `jmac-cornelis/agent-workforce:plans/agent-pipeline-architecture.md`
- Cornelis Agent Pipeline Architecture
- Overview
- This document describes the architecture for a Google ADK-based agent pipeline that automates Jira release planning based on roadmap slides, org charts, and Cornelis product knowledge.
- Architecture Diagram
- flowchart TB
- subgraph Input Sources
- RS[Roadmap Slides - PPT/Excel/Image]
- OC[Org Chart - draw.io]
- JC[Jira Current State]
- WF[Jira Workflow Config]

### Source: `jmac-cornelis/agent-workforce:plans/branch-pr-naming-proposal.md`
- Proposal: Branch and PR Naming Requirements for Jira Automation
- Problem Statement
- A few weeks ago, we took the first steps on moving the team to a place where
- Jira is the source of project management truth and making the developers'
- lives easier to keep Jira updated.
- We launched a no-invasive Jira-GitHub automation that relies on branch names
- containing a Jira ticket key (e.g. `STL-76966`) to automatically link PRs to
- tickets and transition ticket status on merge.
- Current adoption data shows:
- **31% of ticket transitions** are automated (via scm-bot); 69% are still manual

### Source: `jmac-cornelis/agent-workforce:plans/build-excel-map-architecture.md`
- `build-excel-map` Architecture
- Overview
- A subcommand in `agent_cli.py` that orchestrates a multi-step Jira data gathering and Excel assembly pipeline. It produces a single `.xlsx` workbook with:
- **Sheet 1 ("Tickets")**: An indented overview of root ticket(s) and their first-level children only (`hierarchy=1`). Uses Depth 0 / Depth 1 columns to show the parent-child relationship.
- **Sheets 2..N (per ticket key)**: Each first-level child gets its own sheet with unlimited child hierarchy (indented format with depth columns).
- Designed as a deterministic pipeline in `agent_cli.py` (subcommand `build-excel-map`) that imports from `jira_utils.py` for Jira data gathering and `_write_excel()` for Excel output. Also wrapped as an agent tool in `tools/excel_tools.py`.
- Workflow Diagram
- flowchart TD
- A[CLI: python agent_cli.py build-excel-map STL-74071] --> B[Step 1: Connect to Jira]
- B --> C[Step 2: _get_related_data hierarchy=1 — first level only]

### Source: `jmac-cornelis/agent-workforce:plans/conversation-summary.md`
- Conversation summary (engineering-focused)
- This document summarizes the conversation chronologically, focusing on engineering requests, what was implemented/changed, key code edits, errors/fixes, and what work is currently in progress.
- 1) Initial request: ADK-style multi-agent release-planning pipeline
- Design and implement a Google ADK-style agent pipeline to support a Jira-driven release planning workflow. Key requirements:
- Reuse existing Jira / draw.io utilities rather than reimplementing.
- Support a Cornelis internal **OpenAI-compatible** LLM endpoint, with fallback via LiteLLM.
- Human-in-the-loop approvals for Jira write actions.
- Optional state/session persistence.
- Implemented / changed
- Added a pipeline codebase structure for orchestration, agents, tools, persistence, and LLM provider abstraction.

### Source: `jmac-cornelis/agent-workforce:plans/daily-report-tool-design.md`
- Daily Report Tool Integration Design
- Overview
- Integrate the daily report functionality into the agentic workflow as reusable tools,
- with optional CSV/Excel export. The current `daily_report.py` becomes a thin CLI
- wrapper over a new `core/reporting.py` module.
- Architecture
- graph TD
- CLI[daily_report.py CLI] --> CORE[core/reporting.py]
- TOOLS[tools/jira_tools.py @tool] --> CORE
- MCP[mcp_server.py MCP endpoint] --> CORE

### Source: `jmac-cornelis/agent-workforce:plans/feature-planning-agent-architecture.md`
- Feature Planning Agent — Architecture Plan
- 1. Problem Statement
- Cornelis Networks needs an agent that can take a high-level feature request (e.g., *"We're adding a PQC device to our board — scope the SW/FW work and build a Jira plan"*) and:
- 1. **Research** the feature domain using web search, internal docs, Cornelis MCP tools, Jira, Confluence, and GitHub
- 2. **Understand** the existing Cornelis hardware product deeply — what it is, how it works, what SW/FW already exists
- 3. **Define & Scope** the SW/FW development work required to support the new feature on the hardware
- 4. **Build a Jira Project Plan** with Epics and Stories in an existing Jira project (dry-run first, execute after approval)
- Design Principles
- **Confidence-aware**: Every research finding and scoping decision carries a confidence level (high/medium/low)
- **Honest**: Never fabricate information — clearly state what is known vs. unknown

### Source: `jmac-cornelis/agent-workforce:plans/full-workflow-fix.md`
- Fix: Full Workflow Produces 0 Items
- Problem Statement
- Running the full feature-plan workflow (`--workflow feature-plan` without `--scope-doc`) produces 0 scope items, 0 epics, and 0 stories. The user expects the AI to produce a detailed technical scope document (like `~/Downloads/RedfishRDE.md`) and then generate Jira tickets from it.
- Root Cause Analysis
- The pipeline has **two paths** through each agent:
- 1. **LLM path** (`agent.run()` → `_run_with_tools()` → LLM ReAct loop → `_parse_*()` regex parser)
- 2. **Deterministic path** (`agent.research()` / `agent.analyze()` / `agent.scope()` → direct tool calls)
- The full workflow uses the **LLM path** (via `_run_with_tools()`). The problem is a **parsing gap**: the LLM produces free-text Markdown, but the regex parsers in `_parse_report()`, `_parse_profile()`, and `_parse_scope()` are extremely rigid and fail silently when the LLM's output doesn't match the expected format exactly.
- Specific failures observed:
- | Phase | Agent | Parser | Why it fails |

### Source: `jmac-cornelis/agent-workforce:plans/github-pr-hygiene-proposal.md`
- Proposal: GitHub PR Hygiene Scans via the Drucker Agent
- Date: 2026-03-28
- Status: Draft proposal
- Audience: Development, PM, release engineering
- Problem Statement
- Pull requests on our GitHub repositories have no automated lifecycle hygiene.
- PRs go stale without notification, review requests languish, and there is no
- systematic way to nudge PR originators when their work sits idle.
- Today the only GitHub-Jira integration is the branch-naming automation (see
- `plans/branch-pr-naming-proposal.md`), which handles forward linking from Git

### Source: `jmac-cornelis/agent-workforce:plans/shannon-permanent-deployment.md`
- Shannon Permanent Deployment Plan
- Status: Draft — awaiting network topology confirmation
- Shannon is proven working end-to-end as of 2026-03-17:
- `@Shannon /stats` in Teams → Outgoing Webhook → cloudflared quick tunnel → Shannon on localhost:8200 → Adaptive Card reply in channel
- The current setup is ephemeral: cloudflared quick tunnel URL changes on restart, requiring a new Teams webhook each time
- Run Shannon permanently on `cn-ai-01.cornelisnetworks.com` so that `@Shannon` works 24/7 in the `#agent-shannon` channel without manual tunnel restarts or webhook recreation.
- Decision: Network Path
- Teams Outgoing Webhooks require Microsoft servers to POST to a public HTTPS URL. There are two paths depending on whether `cn-ai-01` is internet-reachable.
- Path A — Named Cloudflare Tunnel (recommended if cn-ai-01 is behind firewall)
- No inbound ports needed. Cloudflare Tunnel creates an outbound-only connection from cn-ai-01 to Cloudflare edge, which proxies Teams traffic in.

### Source: `jmac-cornelis/agent-workforce:plans/sharing-planning-agent-via-cn-ai-tools.md`
- Sharing the Project Planning Agent via cn-ai-tools
- 1. Assessment: Is cn-ai-tools the Right Mechanism?
- What cn-ai-tools is designed for
- The `cn-ai-tools` repo is a **configuration and prompt sharing** platform. Its agents are lightweight — a `prompt.md`, an `agent.json` (model + tool flags), and a `README.md`. They are consumed by **OpenCode** (CLI) and **Roo Code** (VS Code extension) as system prompts that run against the CornelisAI backend. The agents have no runtime code of their own — they delegate to the LLM and optionally to MCP servers for tool access.
- What the project planning agent is
- The `jira-utilities` planning pipeline is a **multi-agent Python application** with:
- | Component | Files | Nature |
- |-----------|-------|--------|
- | 6 specialized agents | `agents/*.py` | Python classes with tool registration, state management, LLM orchestration |
- | 6 system prompts | `config/prompts/*.md` | Markdown prompt files (compatible with cn-ai-tools format) |

### Source: `jmac-cornelis/agent-workforce:plans/user-resolver-design.md`
- User Resolver Design — Automatic Assignee Resolution
- Jira Cloud requires an `accountId` (e.g., `"712020:daf767ac-..."`) for the assignee
- field, but plan inputs (LLM-generated JSON, CSV/Excel files, org charts) contain
- human-readable values: display names ("John Doe"), usernames ("jdoe"), or emails
- ("jdoe@cornelisnetworks.com").
- Currently, any non-accountId assignee is silently dropped and the ticket is created
- unassigned.
- Design: Transparent UserResolver
- A `UserResolver` class in `jira_utils.py` that automatically resolves human-readable
- assignee strings to Jira `accountId` values. It runs transparently — no CLI flags,

### Source: `jmac-cornelis/agent-workforce:plans/version-field-governance-proposal.md`
- Version Field Governance Proposal
- Date: 2026-03-13
- Status: Draft proposal
- Audience: PM, QA, development, release engineering
- Define a single, consistent way to use these Jira fields:
- Release object / Jira Version
- `fixVersion`
- `affectedVersion`
- `Found In Build`
- `Fixed In Build`

### Source: `jmac-cornelis/agent-workforce:plans/workflow-design-analysis.md`
- Native `--workflow` Command vs Bash Scripts for Multi-Step Pipelines
- **Date:** 2026-02-14
- **Status:** Analysis / Decision Record
- **Author:** Architecture Review
- 1. Problem Statement
- The project has a working bash script ([`run_bug_report.sh`](run_bug_report.sh)) that orchestrates a 4-step pipeline:
- 1. Look up a Jira filter by name from favourite filters → filter ID
- 2. Run the filter to pull tickets with latest comments → JSON file
- 3. Send JSON to LLM agent with a prompt → CSV output
- 4. Convert CSV to styled Excel workbook

### Source: `jmac-cornelis/agent-workforce:requirements.txt`
- Cornelis Agent Pipeline - Python Dependencies
- Core dependencies
- jira>=3.5.0 # Jira API client
- python-dotenv>=1.0.0 # Environment variable management
- requests>=2.28.0 # HTTP client
- LLM dependencies
- openai>=1.0.0 # OpenAI SDK (also used for OpenAI-compatible APIs)
- litellm>=1.0.0 # Multi-provider LLM interface
- Google ADK (Agent Development Kit)
- google-adk>=0.1.0 # Google Agent Development Kit

### Source: `jmac-cornelis/agent-workforce:run_bug_report.sh`
- !/usr/bin/env bash
- run_bug_report.sh
- Hardened pipeline script that:
- 1. Looks up a Jira filter by name from the user's favourite filters
- 2. Runs the filter to pull tickets with latest comments
- 3. Sends the JSON to the LLM agent with the cn5000_bugs_clean prompt
- 4. Converts the resulting CSV report to a styled Excel workbook
- ./run_bug_report.sh "SW 12.1.1 P0/P1 Bugs"
- ./run_bug_report.sh "My Filter Name"
- Prerequisites:

### Source: `jmac-cornelis/agent-workforce:schemas/__init__.py`
- schemas — Canonical data record models shared across all AI Agent Workforce agents.
- These Pydantic models define the six canonical objects from the agent specification
- (Section 10.2) plus supporting types for requests, failures, decisions, and patches.
- from .build_record import BuildRecord
- from .test_execution_record import TestRunRequest, TestExecutionRecord, TestFailureRecord
- from .release_record import ReleaseCandidate, ReleaseDecision, ReleaseReadinessSummary
- from .traceability_record import TraceabilityRecord, RelationshipEdge, CoverageGapRecord
- from .documentation_record import DocumentationRecord, DocumentationPatch, PublicationRecord
- from .meeting_summary_record import (
- MeetingRecord,

### Source: `jmac-cornelis/agent-workforce:schemas/build_record.py`
- """Canonical BuildRecord — shared across all agents for build traceability."""
- from datetime import datetime, timezone
- from typing import Any
- from pydantic import BaseModel, Field
- def _utcnow() -> datetime:
- return datetime.now(timezone.utc)
- class BuildRecord(BaseModel):
- """Normalized build record produced by Josephine (Build & Package Agent).
- The build_id is the Fuze-generated internal build identity and serves as
- the authoritative technical identifier across the entire agent system.

### Source: `jmac-cornelis/agent-workforce:schemas/documentation_record.py`
- """Canonical documentation records — shared across all agents."""
- from datetime import datetime, timezone
- from typing import Any
- from pydantic import BaseModel, Field
- def _utcnow() -> datetime:
- return datetime.now(timezone.utc)
- class DocumentationRecord(BaseModel):
- """A documentation artifact produced or tracked by Hypatia (Documentation Agent)."""
- doc_id: str = Field(..., description="Unique document identifier (e.g. doc:engineering:interrupt-routing)")
- doc_type: str = Field(

### Source: `jmac-cornelis/agent-workforce:schemas/release_record.py`
- """Canonical release records — shared across all agents."""
- from datetime import datetime, timezone
- from typing import Any
- from pydantic import BaseModel, Field
- def _utcnow() -> datetime:
- return datetime.now(timezone.utc)
- class ReleaseCandidate(BaseModel):
- """A release candidate proposed by Hedy (Release Manager Agent)."""
- release_id: str = Field(..., description="Unique release identifier (e.g. release:2.4.0-rc2)")
- build_id: str = Field(..., description="Fuze build ID backing this candidate")

### Source: `jmac-cornelis/agent-workforce:schemas/meeting_summary_record.py`
- """Canonical meeting summary records — shared across all agents."""
- from datetime import datetime, timezone
- from pydantic import BaseModel, Field
- def _utcnow() -> datetime:
- return datetime.now(timezone.utc)
- class ActionItemDraft(BaseModel):
- """An action item extracted from a meeting transcript."""
- action_id: str = Field("", description="Unique action item identifier")
- owner: str = Field(..., description="Assigned owner (email or display name)")
- description: str = Field(..., description="What needs to be done")

### Source: `jmac-cornelis/agent-workforce:schemas/test_execution_record.py`
- """Canonical test execution records — shared across all agents."""
- from datetime import datetime, timezone
- from typing import Any
- from pydantic import BaseModel, Field
- def _utcnow() -> datetime:
- return datetime.now(timezone.utc)
- class TestRunRequest(BaseModel):
- """Request to execute a test suite against a build."""
- build_id: str = Field(..., description="Fuze build ID to test against")
- test_plan_id: str = Field(..., description="Test plan identifier (e.g. pr-fast-functional-v3)")

### Source: `jmac-cornelis/agent-workforce:schemas/traceability_record.py`
- """Canonical traceability records — shared across all agents."""
- from datetime import datetime, timezone
- from typing import Any
- from pydantic import BaseModel, Field
- def _utcnow() -> datetime:
- return datetime.now(timezone.utc)
- class TraceabilityRecord(BaseModel):
- """Full traceability view linking a Jira issue to builds, tests, releases, and requirements.
- Maintained by Linnaeus (Traceability Agent). This is the primary queryable
- record for answering "what tested this bug?" or "which release contains this fix?"

### Source: `jmac-cornelis/agent-workforce:scripts/workforce/drawio_to_png.js`
- !/usr/bin/env node
- // Renders each page/tab of a .drawio file to a separate PNG using draw.io's
- // export service via Puppeteer.
- // Usage: node drawio_to_png.js <input.drawio> <output_dir>
- // Produces: output_dir/page-0.png, page-1.png, ...
- const puppeteer = require('puppeteer');
- const fs = require('fs');
- const path = require('path');
- async function renderDrawio(inputFile, outputDir) {
- const xml = fs.readFileSync(inputFile, 'utf-8');

### Source: `jmac-cornelis/agent-workforce:scripts/workforce/drawio_to_mermaid.py`
- !/usr/bin/env python3
- Convert AGENT_ORCHESTRATION_ZONES.drawio to a Mermaid block-beta diagram.
- Source of truth: docs/diagrams/workforce/AGENT_ORCHESTRATION_ZONES.drawio
- Outputs:
- Mermaid block inserted into README.md and docs/workforce/README.md
- PNG rendered and uploaded to Confluence (separate step)
- python3 scripts/drawio_to_mermaid.py
- Reads the draw.io XML, extracts zones and their members, and generates
- a Mermaid block-beta diagram that matches the draw.io layout.
- import re

### Source: `jmac-cornelis/agent-workforce:scripts/workforce/publish_teams_bot_confluence.py`
- !/usr/bin/env python3
- Publish the Teams Bot Framework spec to Confluence as a legacy editor page.
- Converts the Markdown to Confluence storage format XHTML and creates the page
- as a child of the AI Agent Workforce page (ID: 656572464).
- import sys
- sys.path.insert(0, '/Users/johnmacdonald/code/other/jira')
- from confluence_utils import connect_to_confluence
- import html
- def build_body():
- """Build the full Confluence storage format XHTML body."""

### Source: `jmac-cornelis/agent-workforce:scripts/workforce/publish_all.py`
- !/usr/bin/env python3
- '''Publish all agent workforce pages to Confluence.
- Reads agent plan markdown from ``agents/*/docs/PLAN.md`` and draw.io diagrams
- from ``docs/diagrams/workforce/``, converts them to Confluence storage format,
- and publishes each agent as a child page under a configured workforce root
- Pre-rendered diagram screenshots are read from ``docs/confluence/images/``
- (produced by ``render_all_diagrams.py``).
- import argparse
- import json
- import os

### Source: `jmac-cornelis/agent-workforce:scripts/workforce/render_all_diagrams.py`
- !/usr/bin/env python3
- '''Render all agent workforce draw.io diagrams to PNG screenshots.
- Uses the local ``drawio`` CLI to export each draw.io page as a PNG, then crops
- excess whitespace to keep Confluence attachments readable.
- Diagrams are read from ``docs/diagrams/workforce/`` and screenshots are written
- to ``docs/confluence/images/``.
- Prerequisites:
- draw.io desktop CLI available as ``drawio``
- Pillow (``pip install Pillow``)
- import os

### Source: `jmac-cornelis/agent-workforce:scripts/workforce/reorder_plan_sections.py`
- !/usr/bin/env python3
- '''Reorder H2 sections in all agents/*/docs/PLAN.md files.
- 1. Title (H1) preserved
- 2. Diagram sections (Diagrams, Use Case Diagram, Sequence Diagram,
- Message Sequence Diagram) move right after Architecture (or Components
- for agents that use that heading)
- 3. End sections (Phased roadmap, Implementation Phases, Test and acceptance
- plan, Assumptions) move to the very end, in that order
- 4. All other sections keep their original relative order
- import os

### Source: `jmac-cornelis/agent-workforce:scripts/workforce/test_teams_post.py`
- !/usr/bin/env python3
- Test script: Post a message to the #agent-shannon channel in Microsoft Teams.
- Uses Microsoft Graph API with client credentials (app-only) auth flow.
- Requires AZURE_TENANT_ID, AZURE_BOT_APP_ID, AZURE_BOT_APP_SECRET in .env.
- import os
- import sys
- from pathlib import Path
- import requests
- from dotenv import load_dotenv
- Load .env from project root

### Source: `jmac-cornelis/agent-workforce:shannon/__init__.py`
- Module: shannon/__init__.py
- Description: Shannon Teams bot service package.
- Author: Cornelis Networks
- __all__ = []

### Source: `jmac-cornelis/agent-workforce:shannon/app.py`
- Module: shannon/app.py
- Description: FastAPI application for the Shannon Teams bot service.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- from dotenv import load_dotenv
- load_dotenv()

### Source: `jmac-cornelis/agent-workforce:shannon/cards.py`
- Module: shannon/cards.py
- Description: Adaptive Card builders for Shannon Teams responses.
- Author: Cornelis Networks
- from __future__ import annotations
- import re
- from typing import Any, Dict, Iterable, Optional
- from agents.rename_registry import agent_display_name
- _JIRA_BASE = 'https://cornelisnetworks.atlassian.net/browse'
- _TICKET_RE = re.compile(r'(?<!\[)(?<!/)\b([A-Z][A-Z0-9]+-\d+)\b')
- def _linkify_tickets(text: str) -> str:

### Source: `jmac-cornelis/agent-workforce:shannon/models.py`
- Module: shannon/models.py
- Description: Data models for the Shannon Teams bot service.
- Author: Cornelis Networks
- from __future__ import annotations
- import re
- import uuid
- from dataclasses import asdict, dataclass, field
- from datetime import datetime, timezone
- from typing import Any, Dict, List, Optional
- def utc_now_iso() -> str:

### Source: `jmac-cornelis/agent-workforce:shannon/outgoing_webhook.py`
- Module: shannon/outgoing_webhook.py
- Description: Helpers for Microsoft Teams Outgoing Webhook authentication
- and response handling.
- Author: Cornelis Networks
- from __future__ import annotations
- import base64
- import hashlib
- import hmac
- from typing import Optional
- def extract_hmac_signature(authorization_header: Optional[str]) -> str:

### Source: `jmac-cornelis/agent-workforce:shannon/poster.py`
- Module: shannon/poster.py
- Description: Posting adapters for sending Shannon replies to Teams.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- import requests
- from config.env_loader import resolve_dry_run

### Source: `jmac-cornelis/agent-workforce:shannon/notification_router.py`
- Unified notification router — dispatches to Teams DM and email.
- router = NotificationRouter()
- await router.notify(
- agent_id='drucker',
- title='PR Reminders Sent',
- text='3 reminders sent',
- body_lines=['PR #42: stale 7 days', 'PR #55: stale 3 days'],
- target_users=['jmac-cornelis'], # GitHub logins, or None for all
- Delivery channels are controlled per-user in config/identity_map.yaml:
- notify_via: [teams_dm, email]

### Source: `jmac-cornelis/agent-workforce:shannon/registry.py`
- Module: shannon/registry.py
- Description: Agent/channel registry loading for the Shannon Teams bot.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- from pathlib import Path
- from typing import Dict, List, Optional
- import yaml

### Source: `jmac-cornelis/agent-workforce:shannon/service.py`
- Module: shannon/service.py
- Description: Core Shannon service logic for Teams command handling and
- notification posting.
- Author: Cornelis Networks
- from __future__ import annotations
- import logging
- import os
- import sys
- import re as re_mod
- import threading

### Source: `jmac-cornelis/agent-workforce:state/__init__.py`
- Module: state
- Description: State management for Cornelis Agent Pipeline.
- Provides session state and persistence capabilities.
- Author: Cornelis Networks
- from typing import Any
- from state.session import SessionState, SessionManager
- from state.persistence import StatePersistence, JSONPersistence, SQLitePersistence
- __all__ = [
- 'SessionState',
- 'SessionManager',

### Source: `jmac-cornelis/agent-workforce:state/roadmap_snapshot_store.py`
- Module: state/roadmap_snapshot_store.py
- Description: Persistence helpers for roadmap planning snapshots.
- Stores durable JSON + Markdown snapshot artifacts and supports
- retrieval/listing for later review. Optionally copies the
- generated xlsx output file alongside the snapshot.
- Author: Cornelis Networks
- from __future__ import annotations
- import json
- import logging
- import os

### Source: `jmac-cornelis/agent-workforce:state/persistence.py`
- Module: state/persistence.py
- Description: State persistence backends for session storage.
- Supports JSON files and SQLite database.
- Author: Cornelis Networks
- import json
- import logging
- import os
- import sys
- from abc import ABC, abstractmethod
- from datetime import datetime

### Source: `jmac-cornelis/agent-workforce:state/session.py`
- Module: state/session.py
- Description: Session state management for agent workflows.
- Tracks workflow progress and enables resumption.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- import uuid
- from dataclasses import dataclass, field, asdict
- from datetime import datetime

### Source: `jmac-cornelis/agent-workforce:template.py`
- Script name: template.py
- Description: This is a template for a Python script.
- Author: John Macdonald
- import argparse
- import logging
- import sys
- import os
- from datetime import date
- import re
- ****************************************************************************************

### Source: `jmac-cornelis/agent-workforce:tests/GITHUB_TEST_COVERAGE_ANALYSIS.md`
- GitHub PR Hygiene — Test Coverage Analysis
- **Date**: 2026-03-28
- **Branch**: `feature/drucker-github-hygiene`
- **Test run**: 59 new tests, all passing (553 total pass, 2 pre-existing failures)
- | Module | Public Symbols | Tested | Coverage | Gap |
- |--------|---------------|--------|----------|-----|
- | `github_utils.py` | 22 (`__all__`) + 4 internal | 22 + 3 internal | **96%** | 3 untested (display/CLI) |
- | `tools/github_tools.py` | 11 tool functions + 1 class | 10 + 1 class | **91%** | 1 untested tool |
- | `shannon/cards.py` (PR builders) | 4 card builders | 4 | **100%** | — |
- | `agents/drucker_api.py` (GitHub endpoints) | 4 endpoints + 3 models | 4 endpoints | **100%** | — |

### Source: `jmac-cornelis/agent-workforce:tests/conftest.py`
- import contextlib
- import io
- import sys
- import types
- from dataclasses import dataclass
- from pathlib import Path
- from types import ModuleType, SimpleNamespace
- from typing import Any, Dict, Iterable, List, Optional, cast
- import pytest
- from openpyxl import Workbook

### Source: `jmac-cornelis/agent-workforce:tests/test_agent_rename_char.py`
- Module: tests/test_agent_rename_char.py
- Description: Characterization tests for the local agent rename wave.
- Verifies canonical renamed packages, legacy aliases, and
- non-deployed local config surfaces.
- Author: Cornelis Networks
- import sys
- from pathlib import Path
- def test_hemingway_exports_legacy_aliases():
- from agents.hemingway import (
- HemingwayDocumentationAgent,

### Source: `jmac-cornelis/agent-workforce:tests/test_agents_char.py`
- import json
- from types import SimpleNamespace
- import pytest
- from agents.base import AgentConfig, BaseAgent
- from llm.base import BaseLLM, LLMResponse
- from tools.base import ToolResult, tool
- class _DummyLLM(BaseLLM):
- def __init__(self, responses):
- super().__init__(model='dummy-model')
- self._responses = list(responses)

### Source: `jmac-cornelis/agent-workforce:tests/test_confluence_search_char.py`
- Module: test_confluence_search_char.py
- Description: Characterization tests for Confluence search capabilities.
- Covers search_pages_fulltext(), search_pages_by_label() in
- confluence_utils.py and their tool wrappers in tools/confluence_tools.py.
- Author: Cornelis Networks Engineering Tools
- import json
- import sys
- from types import SimpleNamespace
- from typing import Any, Dict, List, Optional
- from unittest.mock import MagicMock

### Source: `jmac-cornelis/agent-workforce:tests/test_confluence_tools_char.py`
- import pytest
- from tools.confluence_tools import ConfluenceTools, search_confluence_pages
- def test_search_confluence_pages_tool_returns_toolresult(monkeypatch: pytest.MonkeyPatch):
- from tools import confluence_tools
- monkeypatch.setattr(confluence_tools, 'get_confluence', lambda: object())
- monkeypatch.setattr(
- confluence_tools,
- '_cu_search_pages',
- lambda _confluence, pattern, limit=25, space=None: [
- {'page_id': '123', 'title': 'Roadmap', 'link': 'https://example.test/page'}

### Source: `jmac-cornelis/agent-workforce:tests/test_core_queries_coverage.py`
- from types import SimpleNamespace
- from core import queries
- def test_quote_values_single_value():
- assert queries._quote_values(['Open']) == '"Open"'
- def test_quote_values_multiple_values_and_special_chars():
- values = ['In Progress', 'R&D', 'A, B']
- assert queries._quote_values(values) == '"In Progress", "R&D", "A, B"'
- def test_build_status_jql_with_empty_inputs():
- assert queries._build_status_jql(None) == ''
- assert queries._build_status_jql([]) == ''

### Source: `jmac-cornelis/agent-workforce:tests/test_confluence_utils_char.py`
- import json
- from pathlib import Path
- from typing import Any, Optional
- import pytest
- import confluence_utils
- class _Response:
- def __init__(
- payload: Optional[dict[str, Any]] = None,
- status_code: int = 200,
- text: Optional[str] = None,

### Source: `jmac-cornelis/agent-workforce:tests/test_core_reporting.py`
- Tests for core/reporting.py
- - _next_day() helper
- - tickets_created_on() — JQL construction + issue_to_dict mapping
- - bugs_missing_field() — date-scoped and all-open variants
- - status_changes_by_actor() — REST API pagination, automation classification
- - daily_report() — composite orchestration
- - export_daily_report() — Excel and CSV export
- import csv
- import json
- import os

### Source: `jmac-cornelis/agent-workforce:tests/test_core_tickets.py`
- from types import SimpleNamespace
- from core.tickets import extract_text_from_adf, issue_to_dict
- def test_issue_to_dict_resource_object_basic_fields():
- issue = SimpleNamespace(
- key='STL-501',
- id='501',
- fields=SimpleNamespace(
- summary='Resource summary',
- description='Resource description',
- issuetype=SimpleNamespace(name='Story'),

### Source: `jmac-cornelis/agent-workforce:tests/test_core_utils.py`
- import csv
- from typing import Any, cast
- from core import utils as core_utils
- def test_output_respects_quiet_mode_and_module_quiet_flag(capture_stdout):
- setattr(cast(Any, core_utils), '_quiet_mode', False)
- with capture_stdout() as out_visible:
- core_utils.output('visible')
- setattr(cast(Any, core_utils), '_quiet_mode', True)
- with capture_stdout() as out_hidden:
- core_utils.output('hidden')

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_agent_char.py`
- import json
- from datetime import datetime, timezone
- from types import SimpleNamespace
- import pytest
- from agents.base import AgentResponse
- from agents.drucker.models import DruckerAction, DruckerFinding, DruckerHygieneReport, DruckerRequest
- from tools.base import ToolResult
- class _FixedDateTime(datetime):
- @classmethod
- def now(cls, tz=None):

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_api_github_char.py`
- Module: test_drucker_api_github_char.py
- Description: Characterization tests for the 4 GitHub endpoints in drucker_api.py.
- Covers POST /v1/github/pr-hygiene, POST /v1/github/pr-stale,
- POST /v1/github/pr-reviews, and GET /v1/github/prs/{owner}/{repo}.
- Author: Cornelis Networks Engineering Tools
- import sys
- from unittest.mock import MagicMock
- import pytest
- ---------------------------------------------------------------------------
- Fixtures

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_github_polling_char.py`
- Module: tests/test_drucker_github_polling_char.py
- Description: Characterization tests for the GitHub PR hygiene polling loop
- in DruckerCoordinatorAgent.tick(). Covers the scan_type='github'
- branch: single/multi repo analysis, error handling, notification
- gating, parameter pass-through, and mixed-job scenarios.
- Author: Cornelis Networks
- import sys
- import types
- from types import SimpleNamespace
- from unittest.mock import MagicMock

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_cli_char.py`
- Module: tests/test_drucker_cli_char.py
- Description: Characterization tests for agents/drucker/cli.py command handlers.
- Covers all 6 subcommands: cmd_hygiene, cmd_issue_check,
- cmd_intake_report, cmd_bug_activity, cmd_github_hygiene, cmd_poll.
- Uses monkeypatch to stub agent and store dependencies — no live
- API calls.
- Author: Cornelis Networks
- import json
- import os
- import sys

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_learning_char.py`
- import pytest
- def test_drucker_learning_store_predicts_component_fix_version_and_priority():
- from agents.drucker.state.learning_store import DruckerLearningStore
- store = DruckerLearningStore(db_path=':memory:', min_observations=2)
- store.record_ticket({
- 'key': 'STL-101',
- 'summary': 'Fabric link instability',
- 'reporter': 'alice',
- 'components': ['Fabric'],
- 'fix_versions': ['12.1.0'],

### Source: `jmac-cornelis/agent-workforce:tests/test_drucker_tools_char.py`
- import pytest
- from agents.drucker.tools import (
- DruckerTools,
- create_drucker_bug_activity_report,
- create_drucker_issue_check,
- create_drucker_hygiene_report,
- create_drucker_intake_report,
- get_drucker_report,
- list_drucker_reports,
- def test_create_drucker_hygiene_report_tool_persists_report(

### Source: `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_utils_char.py`
- Module: test_dry_run_jira_utils_char.py
- Description: Characterization tests verifying that jira_utils mutation functions
- (dashboard CRUD + gadget management + automation state) return early
- without calling Jira APIs when dry_run=True (the default).
- Author: John Macdonald
- import pytest
- from unittest.mock import MagicMock
- import jira_utils
- ---------------------------------------------------------------------------
- Fixtures

### Source: `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_tools_char.py`
- Module: test_dry_run_jira_tools_char.py
- Description: Characterization tests verifying dry-run (default) behavior
- for all 13 mutation functions in tools/jira_tools.py.
- Each test asserts that the function returns a ToolResult.success()
- with a preview dict containing 'dry_run': True and that NO
- actual Jira mutation occurs.
- Author: Cornelis Networks — AI Engineering Tools
- from unittest.mock import MagicMock
- import pytest
- from tools.jira_tools import JiraTools

### Source: `jmac-cornelis/agent-workforce:tests/test_dry_run_mcp_messaging_char.py`
- Module: tests/test_dry_run_mcp_messaging_char.py
- Description: Dry-run behavior tests for MCP server mutation tools and
- messaging/notification functions. Verifies that the default
- dry_run=True returns preview dicts without performing actual
- mutations.
- Author: Cornelis Networks
- import json
- from types import SimpleNamespace
- from unittest.mock import MagicMock
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_env_loader_char.py`
- Module: tests/test_env_loader_char.py
- Description: Characterization tests for config/env_loader.py.
- Validates three-tier env resolution: explicit path, config/env/ dir, .env fallback.
- Author: Cornelis Networks
- import os
- from pathlib import Path
- import pytest
- from config.env_loader import _find_env_dir, load_env
- ---------------------------------------------------------------------------
- Fixtures

### Source: `jmac-cornelis/agent-workforce:tests/test_evidence_contracts_char.py`
- from core.evidence import load_evidence_bundle
- def test_load_evidence_bundle_reads_json_yaml_and_markdown(tmp_path):
- build_path = tmp_path / 'build.json'
- build_path.write_text(
- '{"evidence_type": "build", "title": "Build 101", "summary": "Green build", "facts": ["status: green"]}',
- encoding='utf-8',
- test_path = tmp_path / 'test.yaml'
- test_path.write_text(
- 'evidence_type: test\ntitle: Test Suite\nsummary: 42 tests passed\nfacts:\n - passed: 42\n',
- meeting_path = tmp_path / 'meeting_notes.md'

### Source: `jmac-cornelis/agent-workforce:tests/test_excel_utils_char.py`
- import csv
- import sys
- from pathlib import Path
- from typing import Any, cast
- import openpyxl
- import excel_utils
- def test_convert_from_csv_creates_excel_structure(tmp_path):
- csv_path = tmp_path / "input.csv"
- csv_path.write_text(
- "key,status,priority,summary\n"

### Source: `jmac-cornelis/agent-workforce:tests/test_excel_utils_coverage.py`
- import csv
- import json
- import sys
- from argparse import Namespace
- from pathlib import Path
- from typing import Any, Optional, cast
- import openpyxl
- import pytest
- import excel_utils
- def create_test_excel(path: Path, headers: list[str], data: list[list[Any]], sheet_name: str = 'Data') -> Path:

### Source: `jmac-cornelis/agent-workforce:tests/test_feature_planning_orchestrator_char.py`
- Module: test_feature_planning_orchestrator_char.py
- Description: Characterization tests for Jira actor context in feature-plan
- execution.
- Author: Cornelis Networks — AI Engineering Tools
- import pytest
- from tools.base import ToolResult
- def test_feature_planning_execution_uses_actor_policy_for_ticket_tree_and_links(
- monkeypatch: pytest.MonkeyPatch,
- from agents.feature_planning_orchestrator import FeaturePlanningOrchestrator
- monkeypatch.setattr(

### Source: `jmac-cornelis/agent-workforce:tests/test_file_tools_char.py`
- from pathlib import Path
- from tools.file_tools import FileTools, find_in_files, read_file
- def test_read_file_supports_line_ranges(tmp_path: Path):
- sample = tmp_path / 'sample.txt'
- sample.write_text('alpha\nbeta\ngamma\ndelta', encoding='utf-8')
- result = read_file(str(sample), start_line=2, end_line=3)
- assert result.is_success
- assert result.data['content'] == 'beta\ngamma'
- assert result.data['selected_start_line'] == 2
- assert result.data['selected_end_line'] == 3

### Source: `jmac-cornelis/agent-workforce:tests/test_gantt_agent_char.py`
- import json
- from datetime import datetime, timezone
- from types import SimpleNamespace
- from unittest.mock import MagicMock
- import openpyxl
- import pytest
- from agents.base import AgentResponse
- from agents.gantt.models import (
- BugSummary,
- DependencyGraph,

### Source: `jmac-cornelis/agent-workforce:tests/test_gantt_cli_char.py`
- Module: tests/test_gantt_cli_char.py
- Description: Characterization tests for agents/gantt/cli.py.
- Covers all 10 subcommand handlers: cmd_snapshot, cmd_snapshot_get,
- cmd_snapshot_list, cmd_release_monitor, cmd_release_monitor_get,
- cmd_release_monitor_list, cmd_release_survey, cmd_release_survey_get,
- cmd_release_survey_list, cmd_poll.
- Author: Cornelis Networks
- import json
- from types import SimpleNamespace
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_gantt_components_char.py`
- from datetime import datetime, timezone
- from agents.gantt.models import DependencyEdge, DependencyGraph, MilestoneProposal, PlanningSnapshot
- def test_backlog_interpreter_and_dependency_mapper_normalize_and_attach_edges(
- fake_issue_resource_factory,
- from agents.gantt.components import BacklogInterpreter, DependencyMapper
- issue = fake_issue_resource_factory(
- key='STL-201',
- summary='Planner component work',
- issue_type='Story',
- status='Blocked',

### Source: `jmac-cornelis/agent-workforce:tests/test_gantt_tools_char.py`
- import pytest
- from agents.gantt.models import (
- BugSummary,
- DependencyGraph,
- PlanningSnapshot,
- ReleaseMonitorReport,
- ReleaseSurveyReleaseSummary,
- ReleaseSurveyReport,
- from agents.gantt.tools import (
- GanttTools,

### Source: `jmac-cornelis/agent-workforce:tests/test_github_docs_search_char.py`
- Module: test_github_docs_search_char.py
- Description: Characterization tests for GitHub documentation search capabilities.
- Covers get_repo_readme(), list_repo_docs(), search_repo_docs() in
- github_utils.py and their tool wrappers in tools/github_tools.py.
- Author: Cornelis Networks Engineering Tools
- import sys
- from types import SimpleNamespace
- from typing import Any, Optional
- import pytest
- import github_utils

### Source: `jmac-cornelis/agent-workforce:tests/test_github_integration_char.py`
- Module: tests/test_github_integration_char.py
- Description: Integration smoke tests for the GitHub PR hygiene pipeline.
- Validates analyze_repo_pr_hygiene() → card builder end-to-end.
- Author: Cornelis Networks
- from datetime import datetime, timedelta, timezone
- from types import SimpleNamespace
- import pytest
- import github_utils
- from shannon.cards import (
- build_pr_hygiene_card,

### Source: `jmac-cornelis/agent-workforce:tests/test_github_phase5_char.py`
- from datetime import datetime, timedelta, timezone
- from types import SimpleNamespace
- import pytest
- import github_utils
- ---------------------------------------------------------------------------
- Helpers — reuse patterns from test_github_utils_char.py
- def _silent_output(_message: str = '') -> None:
- return None
- def _patch_common(monkeypatch: pytest.MonkeyPatch) -> None:
- monkeypatch.setattr(github_utils, 'output', _silent_output)

### Source: `jmac-cornelis/agent-workforce:tests/test_github_phase5_integration_char.py`
- Module: tests/test_github_phase5_integration_char.py
- Description: Characterization tests for Phase 5 scan integration layer.
- Covers tool wrappers (5), Shannon cards (10), API endpoints (5),
- and polling dispatch (3) for the extended hygiene scan features.
- Zero live API calls — all github_utils functions are monkeypatched.
- Author: Cornelis Networks
- import sys
- import types
- from unittest.mock import MagicMock
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_github_utils_char.py`
- import sys
- from datetime import datetime, timedelta, timezone
- from types import SimpleNamespace
- from typing import Any, Optional
- import pytest
- import github_utils
- ---------------------------------------------------------------------------
- Helpers — match jira_utils test pattern
- def _silent_output(_message: str = '') -> None:
- return None

### Source: `jmac-cornelis/agent-workforce:tests/test_github_tools_char.py`
- Module: tests/test_github_tools_char.py
- Description: Characterization tests for tools/github_tools.py.
- Validates all 11 tool functions and the GitHubTools collection class.
- Zero live API calls — all github_utils functions are monkeypatched.
- Author: Cornelis Networks
- import pytest
- from tools.github_tools import GitHubTools
- ****************************************************************************************
- A) Repository tools
- def test_list_repos_returns_success(monkeypatch: pytest.MonkeyPatch):

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_api_char.py`
- Module: test_hemingway_api_char.py
- Description: Characterization tests for the Hemingway Documentation Agent REST API.
- Covers health, status, record retrieval, documentation generation,
- impact detection, and publication endpoints in agents/hemingway/api.py.
- Author: Cornelis Networks Engineering Tools
- import os
- import sys
- from types import SimpleNamespace
- from unittest.mock import MagicMock, patch
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_github_write_ops_char.py`
- Module: test_github_write_ops_char.py
- Description: Characterization tests for the 5 write operations in github_utils.py:
- get_pr_changed_files, get_file_content, create_or_update_file,
- batch_commit_files, post_pr_comment.
- Author: Cornelis Networks Engineering Tools
- from types import SimpleNamespace
- import pytest
- import github_utils
- ---------------------------------------------------------------------------
- def _silent_output(_message: str = '') -> None:

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_agent_char.py`
- import json
- from types import SimpleNamespace
- import pytest
- from agents.hemingway.models import (
- DocumentationPatch,
- DocumentationRecord,
- DocumentationRequest,
- PublicationRecord,
- from agents.review_agent import ApprovalStatus, ReviewItem, ReviewSession, ReviewAgent
- from tools.base import ToolResult

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_confluence_publish_char.py`
- Module: test_hemingway_confluence_publish_char.py
- Description: Characterization tests for Hemingway Confluence publish functionality.
- Covers the POST /v1/docs/confluence/publish-page API endpoint,
- the confluence-publish CLI subcommand, and the Shannon card builder.
- Author: Cornelis Networks Engineering Tools
- import sys
- from types import SimpleNamespace
- from unittest.mock import MagicMock, patch
- import pytest
- from tools.base import ToolResult

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_cli_char.py`
- Module: tests/test_hemingway_cli_char.py
- Description: Characterization tests for agents/hemingway/cli.py.
- Covers all three subcommands (cmd_generate, cmd_list, cmd_get)
- with monkeypatched agent and store stubs — no live API calls.
- Author: Cornelis Networks
- import json
- from types import SimpleNamespace
- import pytest
- from agents.hemingway.models import (
- DocumentationPatch,

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_pr_review_char.py`
- Module: test_hemingway_pr_review_char.py
- Description: Characterization tests for the Hemingway POST /v1/docs/pr-review endpoint.
- Covers input validation, dry-run, doc-relevant filtering, agent run,
- batch commit, and record persistence. Updated for async job pattern.
- Author: Cornelis Networks Engineering Tools
- import sys
- import time
- from types import SimpleNamespace
- from unittest.mock import MagicMock, patch
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_search_char.py`
- Module: test_hemingway_search_char.py
- Description: Characterization tests for Hemingway search capabilities.
- Covers HemingwayRecordStore.search_records(), the POST /v1/docs/search
- API endpoint, and the search_hemingway_records() tool wrapper.
- Author: Cornelis Networks Engineering Tools
- import json
- import os
- import sys
- from types import SimpleNamespace
- from typing import Any, Dict, List, Optional

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_shannon_cards_char.py`
- Module: tests/test_hemingway_shannon_cards_char.py
- Description: Characterization tests for the 4 Hemingway card builders in shannon/cards.py.
- Author: Cornelis Networks
- from shannon.cards import (
- build_hemingway_doc_card,
- build_hemingway_impact_card,
- build_hemingway_records_card,
- build_hemingway_publication_card,
- ---------------------------------------------------------------------------
- def _card_schema_ok(card: dict) -> None:

### Source: `jmac-cornelis/agent-workforce:tests/test_jira_actor_policy_char.py`
- Module: test_jira_actor_policy_char.py
- Description: Characterization tests for Jira actor identity resolution.
- Author: Cornelis Networks — AI Engineering Tools
- import pytest
- from core.jira_actor_policy import load_actor_policy, resolve_jira_actor
- def test_resolve_jira_actor_approved_batch_uses_service_account(monkeypatch: pytest.MonkeyPatch):
- monkeypatch.setenv('JIRA_EMAIL', 'engineer@cornelisnetworks.com')
- monkeypatch.setenv('JIRA_API_TOKEN', 'token-123')
- load_actor_policy(force_reload=True)
- result = resolve_jira_actor(

### Source: `jmac-cornelis/agent-workforce:tests/test_jira_identity_char.py`
- Module: test_jira_identity_char.py
- Description: Characterization tests for Jira credential profile resolution.
- Author: Cornelis Networks — AI Engineering Tools
- import pytest
- from config.jira_identity import get_jira_credential_profile
- def test_jira_identity_uses_legacy_fallback_by_default(
- monkeypatch: pytest.MonkeyPatch,
- monkeypatch.setenv('JIRA_EMAIL', 'legacy@cornelisnetworks.com')
- monkeypatch.setenv('JIRA_API_TOKEN', 'legacy-token')
- monkeypatch.delenv('JIRA_REQUESTER_EMAIL', raising=False)

### Source: `jmac-cornelis/agent-workforce:tests/test_hemingway_tools_char.py`
- import pytest
- from agents.hemingway.tools import (
- HemingwayTools,
- generate_hemingway_documentation,
- get_hemingway_record,
- list_hemingway_records,
- def test_generate_hemingway_documentation_tool_persists_record(
- monkeypatch: pytest.MonkeyPatch,
- tmp_path,
- from agents.hemingway import agent as hemingway_agent_module

### Source: `jmac-cornelis/agent-workforce:tests/test_jira_utils_char.py`
- import os
- import sys
- from types import SimpleNamespace
- from typing import Any, Optional
- import pytest
- import jira_utils
- class _Response:
- def __init__(
- status_code: int = 200,
- payload: Optional[dict[str, Any]] = None,

### Source: `jmac-cornelis/agent-workforce:tests/test_jira_tools_char.py`
- from unittest.mock import MagicMock
- import pytest
- from tools.jira_tools import JiraTools
- def test_get_ticket_tool_returns_comments_and_transitions(
- monkeypatch: pytest.MonkeyPatch,
- fake_issue_resource_factory,
- from tools import jira_tools
- jira = MagicMock()
- issue = fake_issue_resource_factory(
- key='STL-800',

### Source: `jmac-cornelis/agent-workforce:tests/test_jira_utils_coverage.py`
- import argparse
- import csv
- import json
- import sys
- from pathlib import Path
- from types import SimpleNamespace
- from typing import Any, cast
- from unittest.mock import MagicMock
- import openpyxl
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_markdown_to_confluence.py`
- Module: tests/test_markdown_to_confluence.py
- Description: Tests for the enhanced markdown_to_storage() converter, diagram rendering,
- convert_markdown_to_confluence() pipeline, and the agent-callable tool.
- Author: Cornelis Networks
- import html
- import os
- import textwrap
- from pathlib import Path
- from unittest.mock import patch
- import pytest

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_char.py`
- import json
- import sys
- from types import SimpleNamespace
- from typing import Any
- import pytest
- from unittest.mock import MagicMock
- def test_issue_to_dict_shape(import_mcp_server):
- issue = {
- 'key': 'STL-500',
- 'fields': {

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_confluence_char.py`
- import json
- import pytest
- def _payload(result):
- assert isinstance(result, list)
- assert len(result) == 1
- assert result[0].type == 'text'
- return json.loads(result[0].text)
- @pytest.mark.asyncio
- async def test_search_confluence_pages_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
- monkeypatch.setattr(import_mcp_server.confluence_utils, 'get_connection', lambda: object())

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_coverage.py`
- import contextlib
- import json
- from types import SimpleNamespace
- from unittest.mock import MagicMock
- import pytest
- import requests
- class _Response:
- def __init__(self, status_code=200, payload=None, text=''):
- self.status_code = status_code
- self._payload = payload

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_drucker_char.py`
- import json
- import pytest
- def _payload(result):
- assert isinstance(result, list)
- assert len(result) == 1
- assert result[0].type == 'text'
- return json.loads(result[0].text)
- @pytest.mark.asyncio
- async def test_create_drucker_hygiene_report_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
- from agents.drucker.models import DruckerHygieneReport

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_gantt_char.py`
- import json
- import pytest
- from agents.gantt.models import (
- BugSummary,
- ReleaseMonitorReport,
- ReleaseSurveyReleaseSummary,
- ReleaseSurveyReport,
- def _payload(result):
- assert isinstance(result, list)
- assert len(result) == 1

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_github_char.py`
- Module: tests/test_mcp_server_github_char.py
- Description: Characterization tests for the 11 GitHub MCP tools in mcp_server.py.
- Validates every GitHub tool function (Tools 26-36) by stubbing
- github_utils via monkeypatch on the import_mcp_server fixture.
- Zero live API calls — all github_utils functions are monkeypatched.
- Author: Cornelis Networks
- import json
- from typing import Any
- import pytest
- ---------------------------------------------------------------------------

### Source: `jmac-cornelis/agent-workforce:tests/test_mcp_server_hemingway_char.py`
- import json
- import pytest
- def _payload(result):
- assert isinstance(result, list)
- assert len(result) == 1
- assert result[0].type == 'text'
- return json.loads(result[0].text)
- @pytest.mark.asyncio
- async def test_generate_hemingway_documentation_tool(import_mcp_server, monkeypatch: pytest.MonkeyPatch):
- from agents.hemingway.models import DocumentationPatch, DocumentationRecord

### Source: `jmac-cornelis/agent-workforce:tests/test_notifications_char.py`
- from types import SimpleNamespace
- def test_jira_comment_notifier_builds_hygiene_comment_with_suggestions():
- from agents.drucker.models import DruckerFinding
- from notifications.jira_comments import JiraCommentNotifier
- comment = JiraCommentNotifier.build_hygiene_comment(
- ticket={'key': 'STL-201', 'summary': 'Missing metadata'},
- findings=[
- DruckerFinding(
- finding_id='F001',
- ticket_key='STL-201',

### Source: `jmac-cornelis/agent-workforce:tests/test_release_tracking.py`
- from datetime import datetime, timedelta, timezone
- from typing import Any, Mapping
- from core.release_tracking import (
- ReleaseSnapshot,
- TrackerConfig,
- assess_readiness,
- build_snapshot,
- compute_cycle_time_stats,
- compute_delta,
- compute_velocity,

### Source: `jmac-cornelis/agent-workforce:tests/test_shannon_pr_cards_char.py`
- Module: tests/test_shannon_pr_cards_char.py
- Description: Characterization tests for the 4 PR card builders in shannon/cards.py.
- Author: Cornelis Networks
- from shannon.cards import (
- build_pr_hygiene_card,
- build_pr_list_card,
- build_pr_reviews_card,
- build_pr_stale_card,
- ---------------------------------------------------------------------------
- def _card_schema_ok(card: dict) -> None:

### Source: `jmac-cornelis/agent-workforce:tests/test_shannon_dry_run_flow_char.py`
- Module: tests/test_shannon_dry_run_flow_char.py
- Description: Characterization tests for the Shannon two-step dry-run flow.
- Author: Cornelis Networks
- from unittest.mock import MagicMock, patch
- from shannon.cards import build_dry_run_preview_card
- from shannon.models import AgentChannelRegistration
- from shannon.service import ShannonService
- def _make_service(mock_poster=None, registry_agents=None):
- from agents.shannon.state_store import ShannonStateStore
- from shannon.registry import ShannonAgentRegistry

### Source: `jmac-cornelis/agent-workforce:tests/test_shannon_service_char.py`
- import base64
- import hashlib
- import hmac
- import json
- from fastapi.testclient import TestClient
- from shannon.app import create_app
- from shannon.outgoing_webhook import extract_hmac_signature
- from shannon.poster import MemoryPoster
- from shannon.registry import ShannonAgentRegistry
- from shannon.service import ShannonService

### Source: `jmac-cornelis/agent-workforce:tests/test_smoke.py`
- import importlib
- def test_import_jira_utils():
- mod = importlib.import_module("jira_utils")
- assert mod is not None
- def test_import_confluence_utils():
- mod = importlib.import_module("confluence_utils")
- def test_import_excel_utils():
- mod = importlib.import_module("excel_utils")
- def test_import_mcp_server(import_mcp_server):
- assert import_mcp_server is not None

### Source: `jmac-cornelis/agent-workforce:tools/__init__.py`
- Module: tools
- Description: Agent tools for Cornelis Agent Pipeline.
- Provides tool wrappers for Jira, draw.io, vision, and file operations.
- Author: Cornelis Networks
- from tools.base import BaseTool, ToolResult, tool
- from tools.jira_tools import (
- get_project_info,
- get_releases,
- get_release_tickets,
- search_tickets,

### Source: `jmac-cornelis/agent-workforce:tools/base.py`
- Module: tools/base.py
- Description: Base classes and decorators for agent tools.
- Provides a consistent interface for tool definition and execution.
- Author: Cornelis Networks
- import functools
- import inspect
- import logging
- import os
- import sys
- from abc import ABC, abstractmethod

### Source: `jmac-cornelis/agent-workforce:tools/confluence_tools.py`
- Module: tools/confluence_tools.py
- Description: Confluence tools for agent use.
- Wraps confluence_utils.py functionality as agent-callable tools.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from typing import Optional
- from dotenv import load_dotenv
- from tools.base import BaseTool, ToolResult, tool

### Source: `jmac-cornelis/agent-workforce:tools/drawio_tools.py`
- Module: tools/drawio_tools.py
- Description: Draw.io tools for agent use.
- Wraps drawio_utilities.py functionality and adds org chart parsing.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- import xml.etree.ElementTree as ET
- from typing import Any, Dict, List, Optional
- from urllib.parse import unquote

### Source: `jmac-cornelis/agent-workforce:tools/file_tools.py`
- Module: tools/file_tools.py
- Description: File tools for agent use.
- Provides file I/O operations for reading, writing, and listing files.
- Author: Cornelis Networks
- import json
- import logging
- import os
- import re
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:tools/excel_tools.py`
- Module: tools/excel_tools.py
- Description: Agent tool wrappers for Excel map building and Excel utility operations.
- Wraps the build-excel-map pipeline from agent_cli.py and excel_utils.py
- functions as agent-callable tools.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- log = logging.getLogger(os.path.basename(sys.argv[0]))
- from typing import List, Optional

### Source: `jmac-cornelis/agent-workforce:tools/github_tools.py`
- Module: tools/github_tools.py
- Description: GitHub tools for agent use.
- Wraps github_utils.py functionality as agent-callable tools.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- from dotenv import load_dotenv
- from tools.base import BaseTool, ToolResult, tool

### Source: `jmac-cornelis/agent-workforce:tools/jira_tools.py`
- Module: tools/jira_tools.py
- Description: Jira tools for agent use.
- Wraps jira_utils.py functionality as agent-callable tools.
- Author: Cornelis Networks
- import logging
- import os
- import sys
- from datetime import datetime, timezone
- from typing import Any, Dict, List, Optional
- from dotenv import load_dotenv

### Source: `jmac-cornelis/agent-workforce:tools/knowledge_tools.py`
- Module: tools/knowledge_tools.py
- Description: Local knowledge-base search and document reading tools.
- Searches Markdown files in data/knowledge/ and reads user-provided
- documents (PDF, DOCX, Markdown, plain text).
- Author: Cornelis Networks
- import logging
- import os
- import re
- import sys
- from pathlib import Path

### Source: `jmac-cornelis/agent-workforce:tools/mcp_tools.py`
- Module: tools/mcp_tools.py
- Description: Cornelis MCP (Model Context Protocol) client tools.
- Provides runtime discovery and invocation of tools exposed by the
- Cornelis MCP server. The server uses the Streamable HTTP transport
- (MCP 2025-03-26 spec) so every request must accept both
- application/json and text/event-stream.
- Author: Cornelis Networks
- import json
- import logging
- import os

### Source: `jmac-cornelis/agent-workforce:tools/plan_export_tools.py`
- Module: tools/plan_export_tools.py
- Description: Converts between feature-plan JSON (as produced by FeaturePlanBuilderAgent)
- and the standard CSV / Excel format used by jira_utils.dump_tickets_to_file().
- Supports BOTH directions:
- JSON → CSV/Excel (plan_json_to_rows, write_plan_csv, write_plan_excel)
- CSV/Excel → JSON (read_plan_rows, plan_rows_to_json)
- Works as:
- 1. An @tool()-decorated function usable inside the agentic pipeline.
- 2. A standalone CLI: python -m tools.plan_export_tools plan.json [-o out.csv]
- python -m tools.plan_export_tools plan.csv --to-json [-o out.json]

### Source: `jmac-cornelis/agent-workforce:tools/vision_tools.py`
- Module: tools/vision_tools.py
- Description: Vision tools for agent use.
- Provides image analysis and document extraction capabilities.
- Author: Cornelis Networks
- import base64
- import logging
- import os
- import sys
- from pathlib import Path
- from typing import Any, Dict, List, Optional

### Source: `jmac-cornelis/agent-workforce:tools/web_search_tools.py`
- Module: tools/web_search_tools.py
- Description: Web search tools for the Feature Planning Agent pipeline.
- Tries the Cornelis MCP server first (looking for a web-search tool),
- then falls back to a direct API call if configured.
- Author: Cornelis Networks
- import json
- import logging
- import os
- import sys
- from typing import Any, Dict, List, Optional
- No authoritative source facts were available.

## Publication Targets
- `repo_markdown` -> `docs/agent-workforce.md` (create)

## Source References
- `/`
- `jmac-cornelis/agent-workforce:AGENTS.md`
- `jmac-cornelis/agent-workforce:STOPPED_HERE_shannon_notifications.md`
- `jmac-cornelis/agent-workforce:.github/workflows/tests.yml`
- `jmac-cornelis/agent-workforce:.github/workflows/docs.yml`
- `jmac-cornelis/agent-workforce:README.md`
- `jmac-cornelis/agent-workforce:.sisyphus/plans/12.2-release-cockpit-recommendations.md`
- `jmac-cornelis/agent-workforce:.sisyphus/plans/12.2-release-status-page.md`
- `jmac-cornelis/agent-workforce:.github/workflows/doc-generation.yml`
- `jmac-cornelis/agent-workforce:TODO.md`
- `jmac-cornelis/agent-workforce:adapters/__init__.py`
- `jmac-cornelis/agent-workforce:adapters/environment/__init__.py`
- `jmac-cornelis/agent-workforce:adapters/fuze/adapter.py`
- `jmac-cornelis/agent-workforce:adapters/fuze/__init__.py`
- `jmac-cornelis/agent-workforce:adapters/github/__init__.py`
- `jmac-cornelis/agent-workforce:adapters/environment/adapter.py`
- `jmac-cornelis/agent-workforce:adapters/github/adapter.py`
- `jmac-cornelis/agent-workforce:adapters/github/webhook.py`
- `jmac-cornelis/agent-workforce:adapters/teams/__init__.py`
- `jmac-cornelis/agent-workforce:agents/README.md`
- `jmac-cornelis/agent-workforce:adapters/teams/adapter.py`
- `jmac-cornelis/agent-workforce:agents/ada/README.md`
- `jmac-cornelis/agent-workforce:agents/ada/__init__.py`
- `jmac-cornelis/agent-workforce:agent_cli.py`
- `jmac-cornelis/agent-workforce:agents/__init__.py`
- `jmac-cornelis/agent-workforce:agents/ada/api.py`
- `jmac-cornelis/agent-workforce:agents/ada/config.yaml`
- `jmac-cornelis/agent-workforce:agents/ada/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/ada/agent.py`
- `jmac-cornelis/agent-workforce:agents/ada/models.py`
- `jmac-cornelis/agent-workforce:agents/ada/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/babbage/README.md`
- `jmac-cornelis/agent-workforce:agents/babbage/__init__.py`
- `jmac-cornelis/agent-workforce:agents/babbage/agent.py`
- `jmac-cornelis/agent-workforce:agents/babbage/api.py`
- `jmac-cornelis/agent-workforce:agents/babbage/config.yaml`
- `jmac-cornelis/agent-workforce:agents/babbage/models.py`
- `jmac-cornelis/agent-workforce:agents/babbage/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/babbage/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/base.py`
- `jmac-cornelis/agent-workforce:agents/bernerslee/README.md`
- `jmac-cornelis/agent-workforce:agents/bernerslee/__init__.py`
- `jmac-cornelis/agent-workforce:agents/bernerslee/agent.py`
- `jmac-cornelis/agent-workforce:agents/bernerslee/config.yaml`
- `jmac-cornelis/agent-workforce:agents/bernerslee/api.py`
- `jmac-cornelis/agent-workforce:agents/bernerslee/models.py`
- `jmac-cornelis/agent-workforce:agents/blackstone/README.md`
- `jmac-cornelis/agent-workforce:agents/bernerslee/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/bernerslee/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/blackstone/__init__.py`
- `jmac-cornelis/agent-workforce:agents/blackstone/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/blackstone/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/blackstone/config.yaml`
- `jmac-cornelis/agent-workforce:agents/brandeis/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/brandeis/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/brooks/README.md`
- `jmac-cornelis/agent-workforce:agents/brandeis/README.md`
- `jmac-cornelis/agent-workforce:agents/brooks/agent.py`
- `jmac-cornelis/agent-workforce:agents/brooks/__init__.py`
- `jmac-cornelis/agent-workforce:agents/brooks/config.yaml`
- `jmac-cornelis/agent-workforce:agents/brooks/api.py`
- `jmac-cornelis/agent-workforce:agents/brooks/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/brooks/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/brooks/models.py`
- `jmac-cornelis/agent-workforce:agents/curie/README.md`
- `jmac-cornelis/agent-workforce:agents/curie/__init__.py`
- `jmac-cornelis/agent-workforce:agents/curie/api.py`
- `jmac-cornelis/agent-workforce:agents/curie/agent.py`
- `jmac-cornelis/agent-workforce:agents/curie/config.yaml`
- `jmac-cornelis/agent-workforce:agents/curie/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/curie/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/curie/models.py`
- `jmac-cornelis/agent-workforce:agents/drucker/README.md`
- `jmac-cornelis/agent-workforce:agents/drucker/agent.py`
- `jmac-cornelis/agent-workforce:agents/drucker/api.py`
- `jmac-cornelis/agent-workforce:agents/drucker/cards.py`
- `jmac-cornelis/agent-workforce:agents/drucker/config/monitor.yaml`
- `jmac-cornelis/agent-workforce:agents/drucker/config/polling.yaml`
- `jmac-cornelis/agent-workforce:agents/drucker/cli.py`
- `jmac-cornelis/agent-workforce:agents/drucker/config/pr_reminders.yaml`
- `jmac-cornelis/agent-workforce:agents/drucker/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/drucker/docs/as-built.md`
- `jmac-cornelis/agent-workforce:agents/drucker/docs/config.md`
- `jmac-cornelis/agent-workforce:agents/drucker/docs/docs.md`
- `jmac-cornelis/agent-workforce:agents/drucker/models.py`
- `jmac-cornelis/agent-workforce:agents/drucker/jira_reporting.py`
- `jmac-cornelis/agent-workforce:agents/drucker/docs/state.md`
- `jmac-cornelis/agent-workforce:agents/drucker/nl_query.py`
- `jmac-cornelis/agent-workforce:agents/drucker/pr_reminders.py`
- `jmac-cornelis/agent-workforce:agents/drucker/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/drucker/state/activity_counter.py`
- `jmac-cornelis/agent-workforce:agents/drucker/state/learning_store.py`
- `jmac-cornelis/agent-workforce:agents/drucker/state/monitor_state.py`
- `jmac-cornelis/agent-workforce:agents/drucker/state/report_store.py`
- `jmac-cornelis/agent-workforce:agents/drucker/state/pr_reminder_state.py`
- `jmac-cornelis/agent-workforce:agents/drucker/tools.py`
- `jmac-cornelis/agent-workforce:agents/faraday/README.md`
- `jmac-cornelis/agent-workforce:agents/faraday/__init__.py`
- `jmac-cornelis/agent-workforce:agents/faraday/agent.py`
- `jmac-cornelis/agent-workforce:agents/faraday/api.py`
- `jmac-cornelis/agent-workforce:agents/faraday/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/faraday/config.yaml`
- `jmac-cornelis/agent-workforce:agents/faraday/models.py`
- `jmac-cornelis/agent-workforce:agents/faraday/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/feature_plan_builder.py`
- `jmac-cornelis/agent-workforce:agents/feature_planning_models.py`
- `jmac-cornelis/agent-workforce:agents/feature_planning_orchestrator.py`
- `jmac-cornelis/agent-workforce:agents/galileo/README.md`
- `jmac-cornelis/agent-workforce:agents/galileo/__init__.py`
- `jmac-cornelis/agent-workforce:agents/galileo/api.py`
- `jmac-cornelis/agent-workforce:agents/galileo/agent.py`
- `jmac-cornelis/agent-workforce:agents/galileo/config.yaml`
- `jmac-cornelis/agent-workforce:agents/galileo/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/galileo/models.py`
- `jmac-cornelis/agent-workforce:agents/galileo/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/gantt/README.md`
- `jmac-cornelis/agent-workforce:agents/gantt/agent.py`
- `jmac-cornelis/agent-workforce:agents/gantt/api.py`
- `jmac-cornelis/agent-workforce:agents/gantt/cli.py`
- `jmac-cornelis/agent-workforce:agents/gantt/components.py`
- `jmac-cornelis/agent-workforce:agents/gantt/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/gantt/docs/PM_IMPLEMENTATION_BACKLOG.md`
- `jmac-cornelis/agent-workforce:agents/gantt/docs/as-built.md`
- `jmac-cornelis/agent-workforce:agents/gantt/models.py`
- `jmac-cornelis/agent-workforce:agents/gantt/docs/prompts.md`
- `jmac-cornelis/agent-workforce:agents/gantt/nl_query.py`
- `jmac-cornelis/agent-workforce:agents/gantt/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/gantt/state/dependency_review_store.py`
- `jmac-cornelis/agent-workforce:agents/gantt/state/release_monitor_store.py`
- `jmac-cornelis/agent-workforce:agents/gantt/state/release_survey_store.py`
- `jmac-cornelis/agent-workforce:agents/gantt/state/snapshot_store.py`
- `jmac-cornelis/agent-workforce:agents/gantt/tools.py`
- `jmac-cornelis/agent-workforce:agents/hardware_analyst.py`
- `jmac-cornelis/agent-workforce:agents/hedy/README.md`
- `jmac-cornelis/agent-workforce:agents/hedy/agent.py`
- `jmac-cornelis/agent-workforce:agents/hedy/__init__.py`
- `jmac-cornelis/agent-workforce:agents/hedy/api.py`
- `jmac-cornelis/agent-workforce:agents/hedy/config.yaml`
- `jmac-cornelis/agent-workforce:agents/hedy/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/hedy/models.py`
- `jmac-cornelis/agent-workforce:agents/hedy/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/hemingway/README.md`
- `jmac-cornelis/agent-workforce:agents/hemingway/__init__.py`
- `jmac-cornelis/agent-workforce:agents/hemingway/agent.py`
- `jmac-cornelis/agent-workforce:agents/hemingway/cli.py`
- `jmac-cornelis/agent-workforce:agents/hemingway/api.py`
- `jmac-cornelis/agent-workforce:agents/hemingway/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/hemingway/models.py`
- `jmac-cornelis/agent-workforce:agents/hemingway/nl_query.py`
- `jmac-cornelis/agent-workforce:agents/hemingway/prompts/as-built-design.md`
- `jmac-cornelis/agent-workforce:agents/hemingway/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/hemingway/prompts/traceability.md`
- `jmac-cornelis/agent-workforce:agents/hemingway/prompts/user-guide.md`
- `jmac-cornelis/agent-workforce:agents/hemingway/tools.py`
- `jmac-cornelis/agent-workforce:agents/hemingway/state/record_store.py`
- `jmac-cornelis/agent-workforce:agents/herodotus/README.md`
- `jmac-cornelis/agent-workforce:agents/herodotus/__init__.py`
- `jmac-cornelis/agent-workforce:agents/herodotus/agent.py`
- `jmac-cornelis/agent-workforce:agents/herodotus/config.yaml`
- `jmac-cornelis/agent-workforce:agents/herodotus/api.py`
- `jmac-cornelis/agent-workforce:agents/herodotus/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/herodotus/models.py`
- `jmac-cornelis/agent-workforce:agents/herodotus/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/humphrey/README.md`
- `jmac-cornelis/agent-workforce:agents/humphrey/__init__.py`
- `jmac-cornelis/agent-workforce:agents/humphrey/api.py`
- `jmac-cornelis/agent-workforce:agents/humphrey/config.yaml`
- `jmac-cornelis/agent-workforce:agents/humphrey/agent.py`
- `jmac-cornelis/agent-workforce:agents/humphrey/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/humphrey/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/humphrey/models.py`
- `jmac-cornelis/agent-workforce:agents/jira_analyst.py`
- `jmac-cornelis/agent-workforce:agents/josephine/README.md`
- `jmac-cornelis/agent-workforce:agents/josephine/agent.py`
- `jmac-cornelis/agent-workforce:agents/josephine/__init__.py`
- `jmac-cornelis/agent-workforce:agents/josephine/config.yaml`
- `jmac-cornelis/agent-workforce:agents/josephine/models.py`
- `jmac-cornelis/agent-workforce:agents/josephine/api.py`
- `jmac-cornelis/agent-workforce:agents/josephine/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/josephine/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/linnaeus/README.md`
- `jmac-cornelis/agent-workforce:agents/linnaeus/__init__.py`
- `jmac-cornelis/agent-workforce:agents/linnaeus/config.yaml`
- `jmac-cornelis/agent-workforce:agents/linnaeus/api.py`
- `jmac-cornelis/agent-workforce:agents/linnaeus/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/linnaeus/agent.py`
- `jmac-cornelis/agent-workforce:agents/linnaeus/models.py`
- `jmac-cornelis/agent-workforce:agents/linnaeus/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/linus/README.md`
- `jmac-cornelis/agent-workforce:agents/linus/agent.py`
- `jmac-cornelis/agent-workforce:agents/linus/__init__.py`
- `jmac-cornelis/agent-workforce:agents/linus/api.py`
- `jmac-cornelis/agent-workforce:agents/linus/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/linus/config.yaml`
- `jmac-cornelis/agent-workforce:agents/linus/models.py`
- `jmac-cornelis/agent-workforce:agents/linus/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/mercator/README.md`
- `jmac-cornelis/agent-workforce:agents/mercator/__init__.py`
- `jmac-cornelis/agent-workforce:agents/mercator/config.yaml`
- `jmac-cornelis/agent-workforce:agents/mercator/agent.py`
- `jmac-cornelis/agent-workforce:agents/mercator/models.py`
- `jmac-cornelis/agent-workforce:agents/mercator/api.py`
- `jmac-cornelis/agent-workforce:agents/mercator/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/mercator/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/nightingale/__init__.py`
- `jmac-cornelis/agent-workforce:agents/nightingale/README.md`
- `jmac-cornelis/agent-workforce:agents/nightingale/config.yaml`
- `jmac-cornelis/agent-workforce:agents/nightingale/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/nightingale/api.py`
- `jmac-cornelis/agent-workforce:agents/nightingale/agent.py`
- `jmac-cornelis/agent-workforce:agents/nightingale/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/nightingale/models.py`
- `jmac-cornelis/agent-workforce:agents/orchestrator.py`
- `jmac-cornelis/agent-workforce:agents/planning_agent.py`
- `jmac-cornelis/agent-workforce:agents/pliny/README.md`
- `jmac-cornelis/agent-workforce:agents/pliny/agent.py`
- `jmac-cornelis/agent-workforce:agents/pliny/api.py`
- `jmac-cornelis/agent-workforce:agents/pliny/__init__.py`
- `jmac-cornelis/agent-workforce:agents/pliny/config.yaml`
- `jmac-cornelis/agent-workforce:agents/pliny/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/pliny/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/pliny/models.py`
- `jmac-cornelis/agent-workforce:agents/pm_runtime.py`
- `jmac-cornelis/agent-workforce:agents/research_agent.py`
- `jmac-cornelis/agent-workforce:agents/rename_registry.py`
- `jmac-cornelis/agent-workforce:agents/review_agent.py`
- `jmac-cornelis/agent-workforce:agents/scoping_agent.py`
- `jmac-cornelis/agent-workforce:agents/shackleton/README.md`
- `jmac-cornelis/agent-workforce:agents/shackleton/agent.py`
- `jmac-cornelis/agent-workforce:agents/shackleton/__init__.py`
- `jmac-cornelis/agent-workforce:agents/shackleton/config.yaml`
- `jmac-cornelis/agent-workforce:agents/shackleton/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/shackleton/api.py`
- `jmac-cornelis/agent-workforce:agents/shackleton/models.py`
- `jmac-cornelis/agent-workforce:agents/shackleton/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/shannon/README.md`
- `jmac-cornelis/agent-workforce:agents/shannon/agent.py`
- `jmac-cornelis/agent-workforce:agents/shannon/__init__.py`
- `jmac-cornelis/agent-workforce:agents/shannon/cli.py`
- `jmac-cornelis/agent-workforce:agents/shannon/api.py`
- `jmac-cornelis/agent-workforce:agents/shannon/cards.py`
- `jmac-cornelis/agent-workforce:agents/shannon/config.yaml`
- `jmac-cornelis/agent-workforce:agents/shannon/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/shannon/docs/TEAMS_BOT_FRAMEWORK.md`
- `jmac-cornelis/agent-workforce:agents/shannon/docs/as-built.md`
- `jmac-cornelis/agent-workforce:agents/shannon/docs/deployment-plan.md`
- `jmac-cornelis/agent-workforce:agents/shannon/docs/teams-setup.md`
- `jmac-cornelis/agent-workforce:agents/shannon/docs/config.md`
- `jmac-cornelis/agent-workforce:agents/shannon/docs/service.md`
- `jmac-cornelis/agent-workforce:agents/shannon/graph_client.py`
- `jmac-cornelis/agent-workforce:agents/shannon/models.py`
- `jmac-cornelis/agent-workforce:agents/shannon/prompts/system.md`
- `jmac-cornelis/agent-workforce:agents/shannon/registry.py`
- `jmac-cornelis/agent-workforce:agents/shannon/state_store.py`
- `jmac-cornelis/agent-workforce:agents/shannon/service.py`
- `jmac-cornelis/agent-workforce:agents/tesla/README.md`
- `jmac-cornelis/agent-workforce:agents/tesla/__init__.py`
- `jmac-cornelis/agent-workforce:agents/tesla/agent.py`
- `jmac-cornelis/agent-workforce:agents/tesla/api.py`
- `jmac-cornelis/agent-workforce:agents/tesla/config.yaml`
- `jmac-cornelis/agent-workforce:agents/tesla/docs/PLAN.md`
- `jmac-cornelis/agent-workforce:agents/vision_analyzer.py`
- `jmac-cornelis/agent-workforce:agents/tesla/models.py`
- `jmac-cornelis/agent-workforce:agents/tesla/prompts/system.md`
- `jmac-cornelis/agent-workforce:config/__init__.py`
- `jmac-cornelis/agent-workforce:config/claude_desktop_config.example.json`
- `jmac-cornelis/agent-workforce:config/env/README.md`
- `jmac-cornelis/agent-workforce:config/env_loader.py`
- `jmac-cornelis/agent-workforce:config/hemingway/voice_config.yaml`
- `jmac-cornelis/agent-workforce:config/jira_actor_identity_policy.yaml`
- `jmac-cornelis/agent-workforce:config/identity_map.yaml`
- `jmac-cornelis/agent-workforce:config/jira_identity.py`
- `jmac-cornelis/agent-workforce:config/prompts/cn5000_bugs_clean.md`
- `jmac-cornelis/agent-workforce:config/prompts/feature_plan_builder.md`
- `jmac-cornelis/agent-workforce:config/prompts/feature_planning_orchestrator.md`
- `jmac-cornelis/agent-workforce:config/prompts/hardware_analyst.md`
- `jmac-cornelis/agent-workforce:config/prompts/jira_analyst.md`
- `jmac-cornelis/agent-workforce:config/prompts/plan_building_instructions.md`
- `jmac-cornelis/agent-workforce:config/prompts/orchestrator.md`
- `jmac-cornelis/agent-workforce:config/prompts/research_agent.md`
- `jmac-cornelis/agent-workforce:config/prompts/planning_agent.md`
- `jmac-cornelis/agent-workforce:config/prompts/review_agent.md`
- `jmac-cornelis/agent-workforce:config/prompts/scope_document_parser.md`
- `jmac-cornelis/agent-workforce:config/prompts/scoping_agent.md`
- `jmac-cornelis/agent-workforce:config/prompts/vision_roadmap_analysis.md`
- `jmac-cornelis/agent-workforce:config/settings.py`
- `jmac-cornelis/agent-workforce:config/prompts/vision_analyzer.md`
- `jmac-cornelis/agent-workforce:config/shannon/agent_registry.yaml`
- `jmac-cornelis/agent-workforce:core/__init__.py`
- `jmac-cornelis/agent-workforce:confluence_utils.py`
- `jmac-cornelis/agent-workforce:config/shannon/teams-app-manifest.template.json`
- `jmac-cornelis/agent-workforce:core/evidence.py`
- `jmac-cornelis/agent-workforce:core/jira_actor_policy.py`
- `jmac-cornelis/agent-workforce:core/monitoring.py`
- `jmac-cornelis/agent-workforce:core/queries.py`
- `jmac-cornelis/agent-workforce:core/release_tracking.py`
- `jmac-cornelis/agent-workforce:core/tickets.py`
- `jmac-cornelis/agent-workforce:core/utils.py`
- `jmac-cornelis/agent-workforce:core/reporting.py`
- `jmac-cornelis/agent-workforce:daily_report.py`
- `jmac-cornelis/agent-workforce:data/knowledge/cornelis_products.md`
- `jmac-cornelis/agent-workforce:data/knowledge/heqing_org.json`
- `jmac-cornelis/agent-workforce:data/knowledge/embedded_sw_fw_patterns.md`
- `jmac-cornelis/agent-workforce:data/templates/create_story.json`
- `jmac-cornelis/agent-workforce:data/knowledge/jira_conventions.md`
- `jmac-cornelis/agent-workforce:data/templates/create_ticket_input.example.json`
- `jmac-cornelis/agent-workforce:data/templates/create_ticket_input.schema.json`
- `jmac-cornelis/agent-workforce:data/templates/epic.json`
- `jmac-cornelis/agent-workforce:data/templates/task.json`
- `jmac-cornelis/agent-workforce:data/templates/story.json`
- `jmac-cornelis/agent-workforce:data/templates/release.json`
- `jmac-cornelis/agent-workforce:deploy/README.md`
- `jmac-cornelis/agent-workforce:deploy/scripts/deploy-shannon.sh`
- `jmac-cornelis/agent-workforce:deploy/scripts/fix-server.sh`
- `jmac-cornelis/agent-workforce:docker-compose.yml`
- `jmac-cornelis/agent-workforce:docs/agent-usefulness-and-applications.md`
- `jmac-cornelis/agent-workforce:docs/agent-workforce-mapping.md`
- `jmac-cornelis/agent-workforce:docs/agents-drucker.md`
- `jmac-cornelis/agent-workforce:docs/agent-workforce.md`
- `jmac-cornelis/agent-workforce:docs/agents-gantt-prompts.md`
- `jmac-cornelis/agent-workforce:docs/agents-hemingway.md`
- `jmac-cornelis/agent-workforce:docs/agents-gantt.md`
- `jmac-cornelis/agent-workforce:docs/agents/index.md`
- `jmac-cornelis/agent-workforce:docs/config.md`
- `jmac-cornelis/agent-workforce:docs/deploy-systemd.md`
- `jmac-cornelis/agent-workforce:docs/index.md`
- `jmac-cornelis/agent-workforce:docs/shannon.md`
- `jmac-cornelis/agent-workforce:docs/installation.md`
- `jmac-cornelis/agent-workforce:docs/tools.md`
- `jmac-cornelis/agent-workforce:docs/tests.md`
- `jmac-cornelis/agent-workforce:docs/workforce/AWS_HYBRID_DEPLOYMENT_PROPOSAL.md`
- `jmac-cornelis/agent-workforce:docs/workflows.md`
- `jmac-cornelis/agent-workforce:docs/workforce/DEPLOYMENT_GUIDE.md`
- `jmac-cornelis/agent-workforce:docs/workforce/INFRASTRUCTURE_ARCHITECTURE.md`
- `jmac-cornelis/agent-workforce:docs/workforce/JIRA_ACTOR_IDENTITY_POLICY.md`
- `jmac-cornelis/agent-workforce:docs/workforce/README.md`
- `jmac-cornelis/agent-workforce:docs/workforce/JIRA_EPIC_STORY_BREAKDOWN.md`
- `jmac-cornelis/agent-workforce:docs/workforce/TEST_FRAMEWORK_EVALUATION.md`
- `jmac-cornelis/agent-workforce:docs/workforce/ai_agents_spec_complete.md`
- `jmac-cornelis/agent-workforce:docs/workforce/ai_agent_implementation_roadmap.md`
- `jmac-cornelis/agent-workforce:drawio_utilities.py`
- `jmac-cornelis/agent-workforce:excel_utils.py`
- `jmac-cornelis/agent-workforce:fix_author.py`
- `jmac-cornelis/agent-workforce:framework/api/__init__.py`
- `jmac-cornelis/agent-workforce:framework/api/app.py`
- `jmac-cornelis/agent-workforce:framework/api/auth.py`
- `jmac-cornelis/agent-workforce:framework/api/health.py`
- `jmac-cornelis/agent-workforce:framework/api/middleware.py`
- `jmac-cornelis/agent-workforce:framework/api/status.py`
- `jmac-cornelis/agent-workforce:framework/events/consumer.py`
- `jmac-cornelis/agent-workforce:framework/events/__init__.py`
- `jmac-cornelis/agent-workforce:framework/events/dead_letter.py`
- `jmac-cornelis/agent-workforce:framework/events/producer.py`
- `jmac-cornelis/agent-workforce:framework/events/envelope.py`
- `jmac-cornelis/agent-workforce:framework/state/__init__.py`
- `jmac-cornelis/agent-workforce:framework/state/audit.py`
- `jmac-cornelis/agent-workforce:framework/state/tokens.py`
- `jmac-cornelis/agent-workforce:framework/state/postgres.py`
- `jmac-cornelis/agent-workforce:jenkins/jenkins_bug_report.sh`
- `jmac-cornelis/agent-workforce:github_utils.py`
- `jmac-cornelis/agent-workforce:jira_utils.py`
- `jmac-cornelis/agent-workforce:llm/__init__.py`
- `jmac-cornelis/agent-workforce:llm/base.py`
- `jmac-cornelis/agent-workforce:llm/config.py`
- `jmac-cornelis/agent-workforce:llm/cornelis_llm.py`
- `jmac-cornelis/agent-workforce:llm/litellm_client.py`
- `jmac-cornelis/agent-workforce:mkdocs.yml`
- `jmac-cornelis/agent-workforce:mcp_server.py`
- `jmac-cornelis/agent-workforce:notifications/__init__.py`
- `jmac-cornelis/agent-workforce:notifications/base.py`
- `jmac-cornelis/agent-workforce:notifications/jira_comments.py`
- `jmac-cornelis/agent-workforce:parse_changelog.py`
- `jmac-cornelis/agent-workforce:parse_changelog_v2.py`
- `jmac-cornelis/agent-workforce:plans/agent-rename-execution-backlog.md`
- `jmac-cornelis/agent-workforce:plans/agent-pipeline-architecture.md`
- `jmac-cornelis/agent-workforce:plans/branch-pr-naming-proposal.md`
- `jmac-cornelis/agent-workforce:plans/build-excel-map-architecture.md`
- `jmac-cornelis/agent-workforce:plans/conversation-summary.md`
- `jmac-cornelis/agent-workforce:plans/daily-report-tool-design.md`
- `jmac-cornelis/agent-workforce:plans/feature-planning-agent-architecture.md`
- `jmac-cornelis/agent-workforce:plans/full-workflow-fix.md`
- `jmac-cornelis/agent-workforce:plans/github-pr-hygiene-proposal.md`
- `jmac-cornelis/agent-workforce:plans/shannon-permanent-deployment.md`
- `jmac-cornelis/agent-workforce:plans/sharing-planning-agent-via-cn-ai-tools.md`
- `jmac-cornelis/agent-workforce:plans/user-resolver-design.md`
- `jmac-cornelis/agent-workforce:plans/version-field-governance-proposal.md`
- `jmac-cornelis/agent-workforce:plans/workflow-design-analysis.md`
- `jmac-cornelis/agent-workforce:requirements.txt`
- `jmac-cornelis/agent-workforce:run_bug_report.sh`
- `jmac-cornelis/agent-workforce:schemas/__init__.py`
- `jmac-cornelis/agent-workforce:schemas/build_record.py`
- `jmac-cornelis/agent-workforce:schemas/documentation_record.py`
- `jmac-cornelis/agent-workforce:schemas/release_record.py`
- `jmac-cornelis/agent-workforce:schemas/meeting_summary_record.py`
- `jmac-cornelis/agent-workforce:schemas/test_execution_record.py`
- `jmac-cornelis/agent-workforce:schemas/traceability_record.py`
- `jmac-cornelis/agent-workforce:scripts/workforce/drawio_to_png.js`
- `jmac-cornelis/agent-workforce:scripts/workforce/drawio_to_mermaid.py`
- `jmac-cornelis/agent-workforce:scripts/workforce/publish_teams_bot_confluence.py`
- `jmac-cornelis/agent-workforce:scripts/workforce/publish_all.py`
- `jmac-cornelis/agent-workforce:scripts/workforce/render_all_diagrams.py`
- `jmac-cornelis/agent-workforce:scripts/workforce/reorder_plan_sections.py`
- `jmac-cornelis/agent-workforce:scripts/workforce/test_teams_post.py`
- `jmac-cornelis/agent-workforce:shannon/__init__.py`
- `jmac-cornelis/agent-workforce:shannon/app.py`
- `jmac-cornelis/agent-workforce:shannon/cards.py`
- `jmac-cornelis/agent-workforce:shannon/models.py`
- `jmac-cornelis/agent-workforce:shannon/outgoing_webhook.py`
- `jmac-cornelis/agent-workforce:shannon/poster.py`
- `jmac-cornelis/agent-workforce:shannon/notification_router.py`
- `jmac-cornelis/agent-workforce:shannon/registry.py`
- `jmac-cornelis/agent-workforce:shannon/service.py`
- `jmac-cornelis/agent-workforce:state/__init__.py`
- `jmac-cornelis/agent-workforce:state/roadmap_snapshot_store.py`
- `jmac-cornelis/agent-workforce:state/persistence.py`
- `jmac-cornelis/agent-workforce:state/session.py`
- `jmac-cornelis/agent-workforce:template.py`
- `jmac-cornelis/agent-workforce:tests/GITHUB_TEST_COVERAGE_ANALYSIS.md`
- `jmac-cornelis/agent-workforce:tests/conftest.py`
- `jmac-cornelis/agent-workforce:tests/test_agent_rename_char.py`
- `jmac-cornelis/agent-workforce:tests/test_agents_char.py`
- `jmac-cornelis/agent-workforce:tests/test_confluence_search_char.py`
- `jmac-cornelis/agent-workforce:tests/test_confluence_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_core_queries_coverage.py`
- `jmac-cornelis/agent-workforce:tests/test_confluence_utils_char.py`
- `jmac-cornelis/agent-workforce:tests/test_core_reporting.py`
- `jmac-cornelis/agent-workforce:tests/test_core_tickets.py`
- `jmac-cornelis/agent-workforce:tests/test_core_utils.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_agent_char.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_api_github_char.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_github_polling_char.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_cli_char.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_learning_char.py`
- `jmac-cornelis/agent-workforce:tests/test_drucker_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_utils_char.py`
- `jmac-cornelis/agent-workforce:tests/test_dry_run_jira_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_dry_run_mcp_messaging_char.py`
- `jmac-cornelis/agent-workforce:tests/test_env_loader_char.py`
- `jmac-cornelis/agent-workforce:tests/test_evidence_contracts_char.py`
- `jmac-cornelis/agent-workforce:tests/test_excel_utils_char.py`
- `jmac-cornelis/agent-workforce:tests/test_excel_utils_coverage.py`
- `jmac-cornelis/agent-workforce:tests/test_feature_planning_orchestrator_char.py`
- `jmac-cornelis/agent-workforce:tests/test_file_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_gantt_agent_char.py`
- `jmac-cornelis/agent-workforce:tests/test_gantt_cli_char.py`
- `jmac-cornelis/agent-workforce:tests/test_gantt_components_char.py`
- `jmac-cornelis/agent-workforce:tests/test_gantt_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_docs_search_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_integration_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_phase5_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_phase5_integration_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_utils_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_api_char.py`
- `jmac-cornelis/agent-workforce:tests/test_github_write_ops_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_agent_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_confluence_publish_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_cli_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_pr_review_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_search_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_shannon_cards_char.py`
- `jmac-cornelis/agent-workforce:tests/test_jira_actor_policy_char.py`
- `jmac-cornelis/agent-workforce:tests/test_jira_identity_char.py`
- `jmac-cornelis/agent-workforce:tests/test_hemingway_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_jira_utils_char.py`
- `jmac-cornelis/agent-workforce:tests/test_jira_tools_char.py`
- `jmac-cornelis/agent-workforce:tests/test_jira_utils_coverage.py`
- `jmac-cornelis/agent-workforce:tests/test_markdown_to_confluence.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_char.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_confluence_char.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_coverage.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_drucker_char.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_gantt_char.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_github_char.py`
- `jmac-cornelis/agent-workforce:tests/test_mcp_server_hemingway_char.py`
- `jmac-cornelis/agent-workforce:tests/test_notifications_char.py`
- `jmac-cornelis/agent-workforce:tests/test_release_tracking.py`
- `jmac-cornelis/agent-workforce:tests/test_shannon_pr_cards_char.py`
- `jmac-cornelis/agent-workforce:tests/test_shannon_dry_run_flow_char.py`
- `jmac-cornelis/agent-workforce:tests/test_shannon_service_char.py`
- `jmac-cornelis/agent-workforce:tests/test_smoke.py`
- `jmac-cornelis/agent-workforce:tools/__init__.py`
- `jmac-cornelis/agent-workforce:tools/base.py`
- `jmac-cornelis/agent-workforce:tools/confluence_tools.py`
- `jmac-cornelis/agent-workforce:tools/drawio_tools.py`
- `jmac-cornelis/agent-workforce:tools/file_tools.py`
- `jmac-cornelis/agent-workforce:tools/excel_tools.py`
- `jmac-cornelis/agent-workforce:tools/github_tools.py`
- `jmac-cornelis/agent-workforce:tools/jira_tools.py`
- `jmac-cornelis/agent-workforce:tools/knowledge_tools.py`
- `jmac-cornelis/agent-workforce:tools/mcp_tools.py`
- `jmac-cornelis/agent-workforce:tools/plan_export_tools.py`
- `jmac-cornelis/agent-workforce:tools/vision_tools.py`
- `jmac-cornelis/agent-workforce:tools/web_search_tools.py`
