## Instructions

Please build a Jira project plan from these scoped items:

1. **Look up components** — Use `get_components` to find the project's component list for `{project_key}`.
2. **Create functional-thread Epics** — Group items into Epics based on their dependency connections using the directed root-tree threading algorithm described in your system prompt.  Items connected by dependencies (even across firmware/driver/tool) belong in the same Epic.  Do NOT group by work-type.
3. **Order Stories by dependencies** — Within each Epic, list Stories in topological order (items that must be done first appear first).
4. **Create Stories** — One per scope item, with full descriptions and acceptance criteria.  Every Story must include "Unit tests pass" and "Code reviewed and merged" as acceptance criteria.
5. **Do NOT create test or documentation tickets** — Those are acceptance criteria on coding Stories, not separate tickets.
6. **Assign components** — Match scope categories to Jira components.
7. **Produce the JSON plan** — Emit a single ```json``` code block conforming to the JSON output schema in your system prompt.

This is a DRY RUN — do NOT create any tickets. Just produce the plan.
