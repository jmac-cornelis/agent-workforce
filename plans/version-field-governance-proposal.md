# Version Field Governance Proposal

Date: 2026-03-13
Status: Draft proposal
Audience: PM, QA, development, release engineering

## Goal

Define a single, consistent way to use these Jira fields:

- Release object / Jira Version
- `fixVersion`
- `affectedVersion`
- `Found In Build`
- `Fixed In Build`

The proposal is designed to satisfy these requirements:

1. A user must be able to choose a human version in Jira and see all tickets logged against that version.
2. One human version may contain multiple builds.
3. Test and bug-finding teams should record the actual build where the issue was found.
4. For planning, `fixVersion` is the target version the issue/story/bug is planned for.

## External Basis

This proposal follows the semantics used by Jira and aligns with long-standing bug-tracking practice:

- Atlassian states that Jira versions are used to schedule and organize releases, and that assigning work to a version lets you filter and report on that release.
- Atlassian states that `fixVersion` is the version the work is released in, while `affectedVersion` is the version or versions impacted by the problem.
- Bugzilla, used heavily by Mozilla and other engineering organizations, uses the same split: `Version` means the released version affected by the bug, while `Target Milestone` is the future version in which the bug should be fixed.
- Semantic Versioning treats build metadata as separate from release precedence, which supports keeping builds distinct from the human release version.

Sources:

- Atlassian, “Manage versions”: https://support.atlassian.com/jira-cloud-administration/docs/manage-versions/
- Atlassian, “What is a version?”: https://support.atlassian.com/jira-software-cloud/docs/what-is-a-version/
- Atlassian, “JQL fields”: https://support.atlassian.com/jira-service-management-cloud/docs/jql-fields/
- Atlassian, “Create release notes”: https://support.atlassian.com/jira-cloud-administration/docs/create-release-notes/
- Bugzilla docs, “Understanding a Bug”: https://bugzilla.readthedocs.io/en/5.0.4/using/understanding.html
- Semantic Versioning 2.0.0: https://semver.org/

## Recommended Model

### 1. Release object / Jira Version

Use the Jira Version object for the human release version, following the current 12.* Jira naming scheme already in use.

Current examples:

- `12.1.1.x`
- `12.2.0.x`

Examples:

- `12.1.1.x`
- `12.2.0.x`
- `12.2.1.x`

Rules:

- Use the exact Jira version names already used by the current release series.
- Create one Jira Version per human release line, such as `12.1.1.x` or `12.2.0.x`.
- Do not create one Jira Version per build.
- Use Jira Version ordering, release dates, release notes, and release reports only at the human-release level.
- Do not invent a second normalized naming layer in Jira.
- If the current release naming convention is `12.1.1.x`, use that exact value consistently in Jira Version, `fixVersion`, and `affectedVersion`.

Reason:

- This matches Jira’s native release model.
- It keeps release filtering and release notes usable.
- It satisfies the requirement that users can choose a version and see work for that version.
- It avoids confusion between the naming used in planning discussions and the naming already used in Jira.

### 2. `fixVersion`

Use `fixVersion` as the planned target version.

Meaning:

- “In which release do we plan to deliver this work?”

Rules:

- Required for planning items: Epics, Stories, Tasks, Bugs that are accepted for work.
- Default to one `fixVersion`.
- Allow multiple `fixVersion` values only for approved backports or deliberate multi-release delivery.
- Never put build numbers in `fixVersion`.
- For roadmap and planning work, `fixVersion` should point to the planned release using the current Jira naming scheme, such as `12.1.1.x`.
- For maintenance or committed bug-fix work, `fixVersion` can point to another concrete release such as `12.1.0.2.x` or `12.2.0.x`.
- Do not use build identifiers such as `12.1.1.0.16` in `fixVersion`.

Examples:

- Story planned for the 12.1.1.x release line: `fixVersion = 12.1.1.x`
- Bug fix planned for the 12.1.0.2.x maintenance line: `fixVersion = 12.1.0.2.x`
- Bug planned for backport to two release lines: `fixVersion in (12.1.1.x, 12.2.0.x)`

### 3. `affectedVersion`

Use `affectedVersion` as the derived human release version where the problem exists.

Meaning:

- “Which released human version(s) are affected by this bug, based on the found build?”

Rules:

- QA, validation, support, and bug reporters populate `Found In Build`.
- The agent or validation automation derives `affectedVersion` from `Found In Build`.
- Required for Bugs.
- Optional and usually unused for Stories/Epics unless your process explicitly needs it.
- Multiple values are allowed when the same bug reproduces in multiple releases.
- Never put build numbers in `affectedVersion`.
- `affectedVersion` should point to the human release version where the bug exists, such as `12.1.1.x` or `12.2.0.x`.
- Use the exact current Jira version value that corresponds to the found build.

Examples:

- Bug found in the 12.1.1.x release line: `affectedVersion = 12.1.1.x`
- Bug reproduced in two maintained releases: `affectedVersion in (12.1.1.x, 12.2.0.x)`

### 4. `Found In Build`

Use `Found In Build` for the exact build where the issue was observed.

Meaning:

- “In which exact build did QA, support, or a customer find this issue?”

Recommended implementation:

- Make `Found In Build` a custom field.
- Best option: a custom Version Picker (multiple versions) field if Jira admin constraints allow it.
- Acceptable fallback: a controlled multi-select field.
- Avoid a free-text field if possible, because filtering, autocomplete, and data quality will be worse.

Rules:

- `Found In Build` values represent installable build identifiers, for example `12.1.1.0.16`.
- This field is owned by QA, support, or whoever found the problem.
- Prefer single-value unless there is a real need to capture multiple reproduced builds.
- This field is the primary source for deriving `affectedVersion`.
- This field is not used for release planning.
- Example mapping: `Found In Build = 12.1.1.0.16` maps to `affectedVersion = 12.1.1.x`.

### 5. `Fixed In Build`

Use `Fixed In Build` for the first build where the fix is present.

Meaning:

- “In which exact build did this fix first appear?”

Recommended implementation:

- Make `Fixed In Build` a custom field.
- Best option: a custom Version Picker or another strongly typed option field.
- Prefer a single value representing the first meaningful build that contains the fix.

Rules:

- `Fixed In Build` is populated by the build or release automation, not by QA.
- This field should usually record the first promoted or meaningful integration build containing the fix.
- Do not use this field as a substitute for `fixVersion`.
- This field is execution evidence, not a planning commitment.
- This field may later be complemented by `Verified In Build` if QA needs to distinguish “fix included” from “fix validated.”

## Proposed Operational Policy

### Bugs

At intake:

- Reporter or QA sets `Found In Build`.
- The agent derives `affectedVersion` from `Found In Build`.
- `fixVersion` may be blank until triage assigns the target release.

After triage:

- PM or dev lead sets `fixVersion`.

After integration:

- Automation sets `Fixed In Build`.

After validation:

- QA may later populate `Verified In Build` if that distinction becomes necessary.

### Stories / Epics / Tasks

At planning:

- PM sets `fixVersion`.
- Do not use `affectedVersion`.
- Do not use build fields unless there is a specific implementation or validation reason.

### Releases

- Release managers create Jira Versions using the current release naming already present in the 12.* series.
- Release notes and release readiness are driven from Jira Versions / `fixVersion`.
- Build progression is tracked separately in `Found In Build`, `Fixed In Build`, and build tooling.

## Recommended Naming Conventions

### Human release versions

Use the current Jira naming scheme already in the 12.* series:

- `12.1.1.x`
- `12.2.0.x`
- `12.1.0.2.x`

Recommended usage:

- `fixVersion` uses the planned release, such as `12.1.1.x` or `12.2.0.x`
- `affectedVersion` is derived from the reported found build
- the derived version should match the exact Jira release name already in use

### Build identifiers

Use the exact build label produced by the build system.

Examples:

- `12.1.1.0.16`
- `12.1.1.0.17`

Recommendation:

- Keep build identifiers sortable and immutable.
- Do not overload the human version fields with build identifiers.

## How This Meets the Requirements

### Requirement 1

“Choose a version and see all tickets logged against a version.”

Recommended Jira filters:

- Planned for a release:
  - `fixVersion = "12.1.1.x"`
- Bugs affecting a release line:
  - `issuetype = Bug AND affectedVersion = "12.1.1.x"`
- All tickets associated with current 12.* release lines:
  - `(fixVersion in ("12.1.1.x", "12.2.0.x") OR affectedVersion in ("12.1.1.x", "12.2.0.x"))`

### Requirement 2

“A version may contain multiple builds.”

Handled by:

- One Jira Version for the human release
- Many concrete build values under that release family

Example:

- Jira Version release line: `12.1.1.x`
- Jira Version release line: `12.2.0.x`
- `Found In Build` / `Fixed In Build` values: `12.1.1.0.16`, `12.1.1.0.17`, `12.1.1.0.18`

### Requirement 3

“The test team or bug finders should use the affects version.”

Handled by:

- QA/reporters own `Found In Build`
- the agent derives `affectedVersion`
- `affectedVersion = 12.1.1.x` means the found build maps to the 12.1.1.x release line

### Requirement 4

“For planning purposes the fix version is the value that indicates the version that the issue / story / bug is planned for.”

Handled by:

- `fixVersion` is the PM/dev-triage planning target
- `fixVersion` refers to the human release target, not the build

## JQL Examples

Find all bugs found in a release:

```jql
project = STL AND issuetype = Bug AND affectedVersion = "12.1.1.x"
```

Find all work planned for a release:

```jql
project = STL AND fixVersion = "12.1.1.x"
```

Find all work associated with current 12.* release lines in either direction:

```jql
project = STL AND (fixVersion in ("12.1.1.x", "12.2.0.x") OR affectedVersion in ("12.1.1.x", "12.2.0.x"))
```

Find planned work in all currently open releases:

```jql
project = STL AND fixVersion in unreleasedVersions(STL)
```

Find bugs affecting all currently open releases:

```jql
project = STL AND issuetype = Bug AND affectedVersion in unreleasedVersions(STL)
```

If Build is implemented as a custom version field:

```jql
project = STL AND "Found In Build" = "12.1.1.0.16"
```

Find issues first fixed in a given build:

```jql
project = STL AND "Fixed In Build" = "12.1.1.0.19"
```

If the build fields are implemented as another custom field type, the exact JQL syntax will vary.

## Guardrails

Do:

- Use Jira Version values exactly as they are named in the current 12.* series.
- Use `fixVersion` for the planned human release target.
- Use `Found In Build` for the build where the issue was observed.
- Use `Fixed In Build` for the first build where the fix is present.
- Derive `affectedVersion` from `Found In Build`.
- Require `affectedVersion` on Bugs.
- Require `fixVersion` on planned work.

Do not:

- Put build identifiers into Jira Versions.
- Put build identifiers into `fixVersion`.
- Put build identifiers into `affectedVersion`.
- Use build fields as planning target fields.

## Suggested Rollout

Phase 1:

- Adopt this field policy.
- Create or clean up Jira Versions using the current 12.* naming already in Jira.
- Make `fixVersion` required for planned work.
- Make `Found In Build` required for Bugs where the reporting build is known.
- Derive `affectedVersion` from `Found In Build`.
- Keep `Fixed In Build` manual until automation is ready.

Phase 2:

- Convert `Found In Build` and `Fixed In Build` to strongly typed fields if needed.
- Add automation to populate `Fixed In Build` from the build system.
- Add validation rules in the ticket monitor so Bugs missing `Found In Build` or Stories missing `fixVersion` are flagged.

Phase 3:

- If needed, add:
  - `Verified In Build`

## Final Recommendation

Adopt this simple rule:

- Jira Version = current Jira release names such as `12.1.1.x` and `12.2.0.x`
- `fixVersion` = planned human release target
- `Found In Build` = exact build where the issue was found
- `Fixed In Build` = exact build where the fix first appears
- `affectedVersion` = released version inferred from `Found In Build`

That gives you:

- clean Jira filtering
- clean release notes
- alignment with the current 12.* naming already used by the team
- separation between planning, defect discovery, and build integration
- room for one release to have many builds
- a clean automation path when the build system starts writing build data
