# Release Survey: STL

**Survey ID**: 7455a69c-a901-4dc4-b6f8-97bf6eedd720
**Created**: 2026-03-25T20:17:24.981390+00:00
**Survey Mode**: Feature Dev
**Releases Surveyed**: 12.2.0.x
**Scope Label**: CN5000,CN6000

## Snapshot Totals

- Counts in this section are a point-in-time snapshot.
- Jira macro sections below are live Jira views and may drift after publication.
- Total tickets: 40
- Done: 18 (45.0%)
- In progress: 9
- Remaining: 13
- Blocked: 0
- Stale: 0
- Unassigned: 0

## 12.2.0.x

- Snapshot total tickets: 40
- Snapshot done: 18 (45.0%)
- Snapshot in progress: 9
- Snapshot remaining: 13
- Snapshot blocked: 0
- Snapshot stale: 0
- Snapshot unassigned: 0
- Snapshot status mix: Closed=18, In Progress=6, In Review=2, Open=11, Ready=1, To Do=1, Verify=1

### In Progress
Snapshot count at publish time: 9. This Jira table stays live after publication.

<div>
<ac:structured-macro ac:name="jira" ac:schema-version="1" data-layout="full-width">
<ac:parameter ac:name="server">System Jira</ac:parameter>
<ac:parameter ac:name="columns">key,summary,type,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="columnIds">issuekey,summary,issuetype,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="maximumIssues">200</ac:parameter>
<ac:parameter ac:name="jqlQuery">project = STL AND fixVersion = &quot;12.2.0.x&quot; AND (labels = &quot;CN5000&quot; OR &quot;product family&quot; = &quot;CN5000&quot; OR labels = &quot;CN6000&quot; OR &quot;product family&quot; = &quot;CN6000&quot;) AND issuetype != Bug AND status in (&quot;In Progress&quot;, &quot;In Review&quot;, &quot;Verify&quot;) ORDER BY priority ASC, updated DESC</ac:parameter>
<ac:parameter ac:name="serverId">332fe428-27be-3c06-ad09-b2cd4d269bee</ac:parameter>
</ac:structured-macro>
</div>

### Blocked (0)
- None

### Remaining
Snapshot count at publish time: 13. This Jira table stays live after publication.

<div>
<ac:structured-macro ac:name="jira" ac:schema-version="1" data-layout="full-width">
<ac:parameter ac:name="server">System Jira</ac:parameter>
<ac:parameter ac:name="columns">key,summary,type,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="columnIds">issuekey,summary,issuetype,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="maximumIssues">200</ac:parameter>
<ac:parameter ac:name="jqlQuery">project = STL AND fixVersion = &quot;12.2.0.x&quot; AND (labels = &quot;CN5000&quot; OR &quot;product family&quot; = &quot;CN5000&quot; OR labels = &quot;CN6000&quot; OR &quot;product family&quot; = &quot;CN6000&quot;) AND issuetype != Bug AND status in (&quot;Open&quot;, &quot;Ready&quot;, &quot;To Do&quot;) ORDER BY priority ASC, updated DESC</ac:parameter>
<ac:parameter ac:name="serverId">332fe428-27be-3c06-ad09-b2cd4d269bee</ac:parameter>
</ac:structured-macro>
</div>

### Done (18)
- [STL-69160](https://cornelisnetworks.atlassian.net/browse/STL-69160): Port Subdivision Phase 2 (Closed; Novak, Eugene; P3-Medium; updated 2026-03-25)
- [STL-74833](https://cornelisnetworks.atlassian.net/browse/STL-74833): bmcMgmtWho - Add option for CKF (Closed; Spinhirne, Alec; P3-Medium; updated 2026-03-23)
- [STL-74832](https://cornelisnetworks.atlassian.net/browse/STL-74832): Mapping Port Config to ASICs (Closed; Spinhirne, Alec; P3-Medium; updated 2026-03-23)
- [STL-74114](https://cornelisnetworks.atlassian.net/browse/STL-74114): [SR-IOV Driver] SR-IOV Ethernet Support - Driver (Closed; Tauferner, Andrew; P3-Medium; updated 2026-03-20)
- [STL-76618](https://cornelisnetworks.atlassian.net/browse/STL-76618): Add CKF led configuration to manny (Closed; Nagarajan, Gnaneshwar; P3-Medium; updated 2026-03-18)
- [STL-76543](https://cornelisnetworks.atlassian.net/browse/STL-76543): Add CKF sensors and enum to CnChassisFactory (Closed; Nagarajan, Gnaneshwar; P3-Medium; updated 2026-03-18)
- [STL-76607](https://cornelisnetworks.atlassian.net/browse/STL-76607): Add overlay to convert port fm view to cable view (Closed; DeMario, Joseph; P3-Medium; updated 2026-03-17)
- [STL-62433](https://cornelisnetworks.atlassian.net/browse/STL-62433): Redfish Phase 1 (Closed; Cook, Sam; P3-Medium; updated 2026-03-14)
- [STL-76541](https://cornelisnetworks.atlassian.net/browse/STL-76541): Establish PortMap format for CKF (Closed; DeMario, Joseph; P3-Medium; updated 2026-03-12)
- [STL-73439](https://cornelisnetworks.atlassian.net/browse/STL-73439): CN6000 New BMC SPI Chip Select Component (Closed; DeMario, Joseph; P3-Medium; updated 2026-03-12)
- [STL-76671](https://cornelisnetworks.atlassian.net/browse/STL-76671): Add boardRev and generation to cnBoardId (Closed; Nagarajan, Gnaneshwar; P3-Medium; updated 2026-03-11)
- [STL-68629](https://cornelisnetworks.atlassian.net/browse/STL-68629): Investigate Openbmc phosphor-logging in 2.18 (Closed; Reddington, Tom; P4-Low; updated 2026-03-09)
- [STL-76018](https://cornelisnetworks.atlassian.net/browse/STL-76018): Change dbus objects for cn-sw-server (Closed; Cook, Sam; P3-Medium; updated 2026-03-09)
- [STL-63015](https://cornelisnetworks.atlassian.net/browse/STL-63015): BMC: Drivers (Closed; Novak, Eugene; P3-Medium; updated 2026-03-04)
- [STL-73590](https://cornelisnetworks.atlassian.net/browse/STL-73590): CN5000 BTS Kernel - Reliability Framework (Closed; Blocksome, Michael; P3-Medium; updated 2026-03-03)
- [STL-73860](https://cornelisnetworks.atlassian.net/browse/STL-73860): MYR Driver - Sending packets from user-space takes ~100ms for driver to respond (Closed; Child, Nicholas; P3-Medium; updated 2026-03-02)
- [STL-76624](https://cornelisnetworks.atlassian.net/browse/STL-76624): FPDM Production Code Hardening — Fix 6 Defects Found During Unit Test Coverage (spec-005) (Closed; Novak, Eugene; P3-Medium; updated 2026-03-02)
- [STL-70256](https://cornelisnetworks.atlassian.net/browse/STL-70256): Integration: Verify integration of IPoIB in simulation (Closed; Reddington, Tom; P3-Medium; updated 2026-03-01)

### Product Family Breakouts

- The Jira tables in this section are live views filtered by product family.

#### CN5000 In Progress
Snapshot count at publish time: 9. This Jira table stays live after publication.

<div>
<ac:structured-macro ac:name="jira" ac:schema-version="1" data-layout="full-width">
<ac:parameter ac:name="server">System Jira</ac:parameter>
<ac:parameter ac:name="columns">key,summary,type,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="columnIds">issuekey,summary,issuetype,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="maximumIssues">200</ac:parameter>
<ac:parameter ac:name="jqlQuery">project = STL AND fixVersion = &quot;12.2.0.x&quot; AND (labels = &quot;CN5000&quot; OR &quot;product family&quot; = &quot;CN5000&quot; OR labels = &quot;CN6000&quot; OR &quot;product family&quot; = &quot;CN6000&quot;) AND issuetype != Bug AND &quot;product family&quot; = &quot;CN5000&quot; AND status in (&quot;In Progress&quot;, &quot;In Review&quot;, &quot;Verify&quot;) ORDER BY priority ASC, updated DESC</ac:parameter>
<ac:parameter ac:name="serverId">332fe428-27be-3c06-ad09-b2cd4d269bee</ac:parameter>
</ac:structured-macro>
</div>

#### CN5000 Remaining
Snapshot count at publish time: 8. This Jira table stays live after publication.

<div>
<ac:structured-macro ac:name="jira" ac:schema-version="1" data-layout="full-width">
<ac:parameter ac:name="server">System Jira</ac:parameter>
<ac:parameter ac:name="columns">key,summary,type,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="columnIds">issuekey,summary,issuetype,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="maximumIssues">200</ac:parameter>
<ac:parameter ac:name="jqlQuery">project = STL AND fixVersion = &quot;12.2.0.x&quot; AND (labels = &quot;CN5000&quot; OR &quot;product family&quot; = &quot;CN5000&quot; OR labels = &quot;CN6000&quot; OR &quot;product family&quot; = &quot;CN6000&quot;) AND issuetype != Bug AND &quot;product family&quot; = &quot;CN5000&quot; AND status in (&quot;Open&quot;, &quot;To Do&quot;) ORDER BY priority ASC, updated DESC</ac:parameter>
<ac:parameter ac:name="serverId">332fe428-27be-3c06-ad09-b2cd4d269bee</ac:parameter>
</ac:structured-macro>
</div>

#### CN5000 Epics
Snapshot count at publish time: 6. This Jira table stays live after publication.

<div>
<ac:structured-macro ac:name="jira" ac:schema-version="1" data-layout="full-width">
<ac:parameter ac:name="server">System Jira</ac:parameter>
<ac:parameter ac:name="columns">key,summary,type,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="columnIds">issuekey,summary,issuetype,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="maximumIssues">200</ac:parameter>
<ac:parameter ac:name="jqlQuery">project = STL AND fixVersion = &quot;12.2.0.x&quot; AND (labels = &quot;CN5000&quot; OR &quot;product family&quot; = &quot;CN5000&quot; OR labels = &quot;CN6000&quot; OR &quot;product family&quot; = &quot;CN6000&quot;) AND issuetype != Bug AND &quot;product family&quot; = &quot;CN5000&quot; AND issuetype = &quot;Epic&quot; ORDER BY priority ASC, updated DESC</ac:parameter>
<ac:parameter ac:name="serverId">332fe428-27be-3c06-ad09-b2cd4d269bee</ac:parameter>
</ac:structured-macro>
</div>

#### CN5000 Open Epic Child Analysis (2)
##### [STL-68268](https://cornelisnetworks.atlassian.net/browse/STL-68268): MYR Linux Driver Work - ipoib
- Epic status: Open; open descendants: 2 of 2 non-bug descendants
- Open type mix: Story=2

| Depth | Ticket | Type | Summary | Status | Assignee | Manager | Priority | Fix Versions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [STL-71715](https://cornelisnetworks.atlassian.net/browse/STL-71715) | Story | Enable IPoIB with the MYR host driver on real HW | In Progress | Child, Nicholas | Heqing Zhu | P3-Medium | 12.2.0.x, 12.1.1.x |
| 1 | [STL-65825](https://cornelisnetworks.atlassian.net/browse/STL-65825) | Story | Enable IPoIB with the MYR host driver in simulator | Ready | Child, Nicholas | Heqing Zhu | P3-Medium | FutureDev |

##### [STL-69162](https://cornelisnetworks.atlassian.net/browse/STL-69162): BMC: IPoIB
- Epic status: Open; open descendants: 1 of 4 non-bug descendants
- Open type mix: Story=1

| Depth | Ticket | Type | Summary | Status | Assignee | Manager | Priority | Fix Versions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [STL-70348](https://cornelisnetworks.atlassian.net/browse/STL-70348) | Story | DCS: Enable ip forwarding for the IB0 interface | In Review | Reddington, Tom | Eugene Novak | P3-Medium | 12.2.0.x |

#### CN6000 In Progress
Snapshot count at publish time: 0.

- None

#### CN6000 Remaining
Snapshot count at publish time: 5. This Jira table stays live after publication.

<div>
<ac:structured-macro ac:name="jira" ac:schema-version="1" data-layout="full-width">
<ac:parameter ac:name="server">System Jira</ac:parameter>
<ac:parameter ac:name="columns">key,summary,type,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="columnIds">issuekey,summary,issuetype,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="maximumIssues">200</ac:parameter>
<ac:parameter ac:name="jqlQuery">project = STL AND fixVersion = &quot;12.2.0.x&quot; AND (labels = &quot;CN5000&quot; OR &quot;product family&quot; = &quot;CN5000&quot; OR labels = &quot;CN6000&quot; OR &quot;product family&quot; = &quot;CN6000&quot;) AND issuetype != Bug AND &quot;product family&quot; = &quot;CN6000&quot; AND status in (&quot;Open&quot;, &quot;Ready&quot;) ORDER BY priority ASC, updated DESC</ac:parameter>
<ac:parameter ac:name="serverId">332fe428-27be-3c06-ad09-b2cd4d269bee</ac:parameter>
</ac:structured-macro>
</div>

#### CN6000 Epics
Snapshot count at publish time: 1. This Jira table stays live after publication.

<div>
<ac:structured-macro ac:name="jira" ac:schema-version="1" data-layout="full-width">
<ac:parameter ac:name="server">System Jira</ac:parameter>
<ac:parameter ac:name="columns">key,summary,type,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="columnIds">issuekey,summary,issuetype,status,assignee,priority,updated</ac:parameter>
<ac:parameter ac:name="maximumIssues">200</ac:parameter>
<ac:parameter ac:name="jqlQuery">project = STL AND fixVersion = &quot;12.2.0.x&quot; AND (labels = &quot;CN5000&quot; OR &quot;product family&quot; = &quot;CN5000&quot; OR labels = &quot;CN6000&quot; OR &quot;product family&quot; = &quot;CN6000&quot;) AND issuetype != Bug AND &quot;product family&quot; = &quot;CN6000&quot; AND issuetype = &quot;Epic&quot; ORDER BY priority ASC, updated DESC</ac:parameter>
<ac:parameter ac:name="serverId">332fe428-27be-3c06-ad09-b2cd4d269bee</ac:parameter>
</ac:structured-macro>
</div>

#### CN6000 Open Epic Child Analysis (0)
- None
