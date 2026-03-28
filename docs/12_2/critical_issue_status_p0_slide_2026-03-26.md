# Critical Issue Status (P0 Only) — 2026-03-26

**Source:** Jira filter "SW 12.1.2 Targeted P0 Bugs" (filter 33606)
- CN5000, P0-Stopper only, Exposure Critical/High, fixVersion = 12.1.2.x
- **23 P0 bugs total** — 12 active, 6 Verify, 5 Closed

---

## Issues / Bug Status

| Open Critical | New This Week | Waiting for Verify in DST | Investigating |
|:------------:|:-------------:|:------------------------:|:------------:|
| **12**       | **3**         | **6**                    | **10**       |

- **Open Critical** = all 12 bugs not in Closed or Verify (includes Investigating + In Review)
- **New This Week** = created since 2026-03-20: STL-77092, STL-77078 (already Closed), STL-77071
- **Waiting for Verify in DST** = status = Verify — 6 bugs with fixes landed, awaiting test build validation. These are _not_ counted in Open Critical (fix exists, pending confirmation).
- **Investigating** = bugs where the team is actively working toward a fix (maps from Open, In Progress, In Review). 10 of the 12 Open Critical are Investigating; the remaining 2 are In Review with fixes already submitted.

---

## SLIDE 1 — Rollup by Root Cause (12 active bugs → 8 rows)

| Area | Issues | Description | Customer | Status | Next Steps |
|------|--------|-------------|----------|--------|------------|
| **BTS / Lustre** | [STL-76950](https://cornelisnetworks.atlassian.net/browse/STL-76950), [STL-76880](https://cornelisnetworks.atlassian.net/browse/STL-76880), [STL-76940](https://cornelisnetworks.atlassian.net/browse/STL-76940) | GPU DMA-buf deregistration race — mi300x kernel panics in rdmavt + Lustre RDMA timeouts with BTS. All hit same BTS memory lifecycle path. | — | In Review / Investigating | 76950 fix in review (Child); blocked by 76982 (Verify) + 76983, 76984 (Open). If all land → cascade-fixes cluster. |
| **OPX — TID cache** | [STL-76365](https://cornelisnetworks.atlassian.net/browse/STL-76365), [STL-73247](https://cornelisnetworks.atlassian.net/browse/STL-73247) | OPX TID cache diverges from kernel TID table under high expected-receive rate. HPL + sph_exa hangs. Chronic — 73247 open since 12.1.0.x. | — | Investigating | Architecturally complex fix spanning OPX user-space + hfi1 kernel. Cernohous + Erwin investigating. |
| **OPX — GPU AI** | [STL-77071](https://cornelisnetworks.atlassian.net/browse/STL-77071) | MPT-30B hang with aws-ofi dmabuf at RWTH. May overlap BTS DMA-buf cluster — needs triage. New this week. | RWTH | Investigating | Espinoza assessing. Possible user config issue — engaging customer directly. |
| **Fabric / MYR FW** | [STL-76338](https://cornelisnetworks.atlassian.net/browse/STL-76338), [STL-76494](https://cornelisnetworks.atlassian.net/browse/STL-76494) | MYR switch buffer/credit mgmt — tportPktDropPending on ISLs, RbufCtrlSbe hung nodes. Related switch-side failures. 76494 has sw_fixed workaround. | TACC | Investigating | Wright on ISL drops. Rothermel on RbufCtrlSbe. No fixes landed yet. |
| **Fabric / MYR FW** | [STL-77092](https://cornelisnetworks.atlassian.net/browse/STL-77092) | DWC switch VR (voltage regulator) fault on liquid-cooled switch. Hardware issue, separate from buffer/credit cluster. New this week. | Lenovo | In Review | Nagarajan fix in review. |
| **Host Driver — IPoIB** | [STL-76836](https://cornelisnetworks.atlassian.net/browse/STL-76836) | ipoib timeout at LLNL Lynx. May be fabric-caused — Jira links to 76494 (RbufCtrlSbe) + 76873 (link training). | LLNL (Lynx) | Investigating | Correlate with fabric cluster. If fabric-side, reclassify. |
| **Host Driver — PCIe** | [STL-76997](https://cornelisnetworks.atlassian.net/browse/STL-76997) | Jobs crashed during SPEC run at NEC/RWTH. PCIe uncorrectable error correlation. Relates to STL-75193. | NEC/RWTH | Investigating | Luick investigating PCIe error correlation. Koch providing lspci output. |
| **Link / 8051 FW** | [STL-76873](https://cornelisnetworks.atlassian.net/browse/STL-76873) | Link repeatedly fails LNI during EstablishComm.TxRxHunt — 8051 FW SerDes link training. ~8 links affected. Feeds into LLNL Lynx fabric instability picture. | LLNL (Lynx) | Investigating | Johanson leading via Link Working Group. |

---

## SLIDE 2 — BTS / Lustre Detail

### Active (3 bugs)

| Issue | Pri | Summary | Assignee | Status | Root Cause / Blockers | Next Steps |
|-------|-----|---------|----------|--------|-----------------------|------------|
| [STL-76950](https://cornelisnetworks.atlassian.net/browse/STL-76950) | P0 | mi300x crash on ctl-c BTS/dmabuf — `bulksvc_user_info_destroy` | Child | In Review | GPU DMA-buf deregistration race in rdmavt. Blocked by: [STL-76982](https://cornelisnetworks.atlassian.net/browse/STL-76982) (DMS unregister, **Verify**), [STL-76983](https://cornelisnetworks.atlassian.net/browse/STL-76983) (force-cancel trackers, **Open**), [STL-76984](https://cornelisnetworks.atlassian.net/browse/STL-76984) (rvt/bulksvc race, **Open**) | Retest with next DST once all 3 blockers land. 76982 in Verify; 76983 + 76984 still need code. |
| [STL-76880](https://cornelisnetworks.atlassian.net/browse/STL-76880) | P0 | mi300x GPU kernel panic `rvt_send_complete` | Simonson | Investigating | Same rdmavt DMA-buf path as 76950. GPU memory invalidation during HFI DMA mapping teardown. | Likely fixed by 76950 cluster patches. Retest together. |
| [STL-76940](https://cornelisnetworks.atlassian.net/browse/STL-76940) | P0 | LNetError RDMA timeout with BTS — Lustre client eviction | Simonson | Investigating | Lustre ko2iblnd hitting BTS verbs path. Caused by [STL-76941](https://cornelisnetworks.atlassian.net/browse/STL-76941) (`hfi1_dms_handle_data` crash, **Verify**). Blocked by [STL-76999](https://cornelisnetworks.atlassian.net/browse/STL-76999) (spinwait deadlock, **Verify**). | Zhu: "Wait for 12.1.2 DST to review — we have fixed a few bugs as we investigated this." |

### Verify Queue (5 BTS fixes awaiting validation)

| Issue | Summary | Owner | What It Fixes |
|-------|---------|-------|---------------|
| [STL-76999](https://cornelisnetworks.atlassian.net/browse/STL-76999) | Fix bulksvc_dbg_open unbounded spin-wait deadlock | Blocksome | Blocks 76940 (Lustre RDMA timeout) |
| [STL-76942](https://cornelisnetworks.atlassian.net/browse/STL-76942) | bufcount error — BTS buffer management | Blocksome | BTS Lustre data integrity |
| [STL-76863](https://cornelisnetworks.atlassian.net/browse/STL-76863) | BAD WRITE CHECKSUM — BTS MR registration error | Erwin | BTS Lustre data integrity |
| [STL-76847](https://cornelisnetworks.atlassian.net/browse/STL-76847) | `calculate_mr_page_offset` Invalid — MR offset error | Erwin | BTS Lustre data integrity |
| [STL-76732](https://cornelisnetworks.atlassian.net/browse/STL-76732) | `hfi1_dms_impl_dlist_remove` crash — DMS list corruption | Erwin | BTS internal locking |

### Key Takeaway
BTS has 3 active + 5 in Verify. Heavy investment paying off — but 76950's fix depends on 2 patches still Open (76983, 76984). **Next DST build is the gate.**

---

## SLIDE 3 — OPX Detail

### Active (3 bugs)

| Issue | Pri | Summary | Assignee | Status | Customer | Root Cause | Next Steps |
|-------|-----|---------|----------|--------|----------|------------|------------|
| [STL-76365](https://cornelisnetworks.atlassian.net/browse/STL-76365) | P0 | HPL hang in `hfi1_user_exp_rcv_setup` | Cernohous | Investigating | — | OPX TID cache diverges from kernel TID table. Massive link web: [STL-76561](https://cornelisnetworks.atlassian.net/browse/STL-76561), [STL-76972](https://cornelisnetworks.atlassian.net/browse/STL-76972), [STL-76685](https://cornelisnetworks.atlassian.net/browse/STL-76685), [STL-76554](https://cornelisnetworks.atlassian.net/browse/STL-76554). | Debugging TID cache invalidation race — fix must span OPX user-space + hfi1 kernel. |
| [STL-73247](https://cornelisnetworks.atlassian.net/browse/STL-73247) | P0 | sph_exa hang with OPX Open MPI | Erwin | Investigating | — | Same TID cache root cause as 76365. Open since 12.1.0.x — chronic. | Same fix as 76365. |
| [STL-77071](https://cornelisnetworks.atlassian.net/browse/STL-77071) | P0 | MPT-30B hang with aws-ofi dmabuf | Espinoza | Investigating | RWTH | Possibly OPX + DMA-buf interaction during GPU AI training. May be user config issue. | Engaging RWTH directly. Need to determine if OPX bug or job config issue. |

### Verify Queue (1 OPX fix)

| Issue | Summary | Owner | What It Fixes |
|-------|---------|-------|---------------|
| [STL-76561](https://cornelisnetworks.atlassian.net/browse/STL-76561) | HPL OPX_TID_CACHE assert with use_bulksvc:N | Bollig | Related to TID cache cluster (76365, 73247) |

### Key Takeaway
TID cache is the chronic OPX issue (76365 + 73247) — architecturally hard, spans user + kernel. 77071 (RWTH GPU AI hang) is new this week and needs triage.

---

## SLIDE 4 — Fabric / MYR FW Detail

### Active (3 bugs)

| Issue | Pri | Summary | Assignee | Status | Customer | Root Cause | Next Steps |
|-------|-----|---------|----------|--------|----------|------------|------------|
| [STL-76338](https://cornelisnetworks.atlassian.net/browse/STL-76338) | P0 | tportPktDropPending hang when bouncing ISL under small-packet traffic | Wright | Investigating | TACC | MYR FW Tport state machine hangs when credits drain during link bounce. Relates to [STL-76651](https://cornelisnetworks.atlassian.net/browse/STL-76651), [STL-76652](https://cornelisnetworks.atlassian.net/browse/STL-76652), [ISS-8041](https://cornelisnetworks.atlassian.net/browse/ISS-8041). | Wright investigating Tport credit accounting. Reproduced internally on benchmark cluster. |
| [STL-76494](https://cornelisnetworks.atlassian.net/browse/STL-76494) | P0 | Hung nodes under 12.1.0.1.x due to RbufCtrlSbe | Rothermel | Investigating | TACC | SRAM ECC single-bit errors corrupt buffer management → node hangs. Label: sw_fixed. Relates to [STL-76836](https://cornelisnetworks.atlassian.net/browse/STL-76836), [STL-77090](https://cornelisnetworks.atlassian.net/browse/STL-77090). | Software workaround exists (sw_fixed). Watch SBE rate — if increasing, could indicate HW degradation. |
| [STL-77092](https://cornelisnetworks.atlassian.net/browse/STL-77092) | P0 | DWC switch VR fault on liquid-cooled switch | Nagarajan | In Review | Lenovo | Voltage regulator fault in switch hardware — separate from buffer/credit issues. New this week. | Fix in review. |

### Key Takeaway
MYR buffer/credit cluster (76338, 76494) — 2 P0 bugs, both In Progress, zero fixes landed. TACC is primary customer. 76494 has sw_fixed workaround. 77092 (VR fault) is separate and close to landing.

---

## SLIDE 5 — Host Driver + Link / 8051 FW Detail

### Active (3 bugs)

| Issue | Pri | Summary | Assignee | Status | Customer | Root Cause | Next Steps |
|-------|-----|---------|----------|--------|----------|------------|------------|
| [STL-76836](https://cornelisnetworks.atlassian.net/browse/STL-76836) | P0 | ipoib timeout at LLNL Lynx | Novak | Investigating | LLNL (Lynx) | IPoIB → SDMA transmit path stall. BUT: Jira links to [STL-76494](https://cornelisnetworks.atlassian.net/browse/STL-76494) (RbufCtrlSbe) + [STL-76873](https://cornelisnetworks.atlassian.net/browse/STL-76873) (link training). McGinnis observed ipoib issues correlate with link/fabric anomalies — may be fabric-caused. | Correlate with fabric cluster (76494, 76873). If fabric-side, reclassify. |
| [STL-76997](https://cornelisnetworks.atlassian.net/browse/STL-76997) | P0 | Jobs crashed during SPEC run at NEC/RWTH | Luick | Investigating | NEC/RWTH | Host driver crash path. Relates to [STL-75193](https://cornelisnetworks.atlassian.net/browse/STL-75193) (fatal PCIe error). Luick: "proceed — if we see errors from the driver we can perhaps correlate the uncorrectable error." | Investigating PCIe uncorrectable error correlation. Koch providing lspci output. |
| [STL-76873](https://cornelisnetworks.atlassian.net/browse/STL-76873) | P0 | Link repeatedly fails LNI during EstablishComm.TxRxHunt | Johanson | Investigating | LLNL (Lynx) | 8051 FW SerDes/link training failure — handful of links not coming up with MYR FW 12.1.0.2.9 / JKR FW 12.1.0.1.1. About 8 links affected across fabric. Linked to [STL-76836](https://cornelisnetworks.atlassian.net/browse/STL-76836) (ipoib timeout). | Johanson leading via Link Working Group. Analyzing SerDes tuning vs cable qualification. |

### Key Takeaway
76836 (LLNL ipoib) is the most interesting — it may not be a host driver bug at all. If fabric instability (76494 RbufCtrlSbe + 76873 link training) is the root cause, the fix comes from the Fabric/MYR FW and Link/8051 FW clusters. 76997 (NEC/RWTH SPEC crash) is a standalone PCIe investigation.

---

## Key Callouts

1. **BTS is the #1 area** — 3 active + 5 in Verify. 76950 fix depends on 2 patches still in Open (76983, 76984). **Next DST build is the gate.**

2. **MYR buffer/credit has zero fixes landed** — 2 P0 bugs (76338, 76494), both In Progress. TACC is primary customer. 76494 has sw_fixed workaround but needs permanent fix.

3. **76836 (LLNL ipoib)** may be fabric-caused — Jira links and field observations suggest fabric instability (RbufCtrlSbe + link training) as root cause. If confirmed, this is a Fabric/MYR FW + Link/8051 FW problem.

4. **OPX TID hangs still chronic** — 73247 open since 12.1.0.x. Architecturally complex fix spanning user-space + kernel.

5. **77071 (RWTH GPU AI hang)** is new this week — may be user config issue, needs triage before committing engineering resources.
