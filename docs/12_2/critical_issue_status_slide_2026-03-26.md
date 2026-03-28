# Critical Issue Status — 2026-03-26

**Source:** Jira filter "SW 12.1.2 Targeted P0/P1 Bugs" (filter 33573)
- CN5000, P0-Stopper + P1-Critical, Exposure Critical/High, fixVersion = 12.1.2.x
- **33 bugs total** — 23 P0, 10 P1
- Active: 12 In Progress, 5 Open, 2 In Review, 1 Ready | Resolved: 9 Verify, 4 Closed

---

## Issues / Bug Status

| Open Critical | New This Week | Waiting for Verify in DST | Actively Root-Causing |
|:------------:|:-------------:|:------------------------:|:---------------------:|
| **20**       | **5**         | **9**                    | **12**                |

- **Open Critical** = status not in Closed/Verify (In Progress, Open, In Review, Ready)
- **New This Week** = created since 2026-03-20: STL-77092, STL-77078, STL-77071, STL-77046, STL-77023
- **Waiting for Verify in DST** = status = Verify (fixes landed, need test build)
- **Actively Root-Causing** = status = In Progress

---

## SLIDE 1 — Rollup by Root Cause (20 active bugs → 11 rows)

| Area | Issues | Description | Customer | Status | Next Steps |
|------|--------|-------------|----------|--------|------------|
| **BTS / Lustre** | [STL-76950](https://cornelisnetworks.atlassian.net/browse/STL-76950), [STL-76880](https://cornelisnetworks.atlassian.net/browse/STL-76880), [STL-76940](https://cornelisnetworks.atlassian.net/browse/STL-76940) | GPU DMA-buf deregistration race — mi300x kernel panics in rdmavt + Lustre RDMA timeouts with BTS. All hit same BTS memory lifecycle path. | — | In Review / In Progress | 76950 fix in review (Child); depends on 1 sub-fix in Verify + 2 still Open. If all land → likely cascade-fixes cluster. |
| **OPX — TID cache** | [STL-76365](https://cornelisnetworks.atlassian.net/browse/STL-76365), [STL-73247](https://cornelisnetworks.atlassian.net/browse/STL-73247) | OPX TID cache diverges from kernel TID table under high expected-receive rate. HPL + sph_exa hangs. Chronic — 73247 open since 12.1.0.x. | — | In Progress | Architecturally complex fix spanning OPX user-space + hfi1 kernel. Cernohous + Erwin investigating. |
| **OPX — GPU AI** | [STL-77071](https://cornelisnetworks.atlassian.net/browse/STL-77071) | MPT-30B hang with aws-ofi dmabuf at RWTH. May overlap BTS DMA-buf cluster — needs triage. New this week. | RWTH | Open | Espinoza assessing. Initial look suggests possible user config issue — engaging customer directly. |
| **OPX — Perf** | [STL-76240](https://cornelisnetworks.atlassian.net/browse/STL-76240) | IMB Biband/Sendrecv performance drop starting at OPXS 12.1.0.0-62. OPX + host driver data path regression on AMD. | AMD | In Progress | Simonson bisecting OPX builds to isolate regression commit. |
| **OPX / Lustre** | [STL-77023](https://cornelisnetworks.atlassian.net/browse/STL-77023) | Endeavour Lustre problems with use_bulksvc=N — data path fails even without BTS. Separate root cause from BTS cluster. New this week. | Intel | Open | Child assessing. Waiting on server/client dmesg from Intel. |
| **Fabric / MYR FW** | [STL-76338](https://cornelisnetworks.atlassian.net/browse/STL-76338), [STL-76494](https://cornelisnetworks.atlassian.net/browse/STL-76494), [STL-76725](https://cornelisnetworks.atlassian.net/browse/STL-76725), [STL-75962](https://cornelisnetworks.atlassian.net/browse/STL-75962) | MYR switch buffer/credit management — tportPktDropPending on ISLs, RbufCtrlSbe hung nodes, TxHoqDiscards, credit exhaustion. All related switch-side failures. 76494 has sw_fixed label. | TACC | In Progress | Wright on ISL drops. Rothermel on RbufCtrlSbe. King on HoQ discards. Monitor SBE rate for HW degradation. No fixes landed yet. |
| **Fabric / MYR FW** | [STL-77092](https://cornelisnetworks.atlassian.net/browse/STL-77092) | DWC switch VR (voltage regulator) fault on liquid-cooled switch. Hardware issue, separate from buffer/credit cluster. New this week. | Lenovo | In Review | Nagarajan fix in review. |
| **Host Driver — IPoIB** | [STL-76836](https://cornelisnetworks.atlassian.net/browse/STL-76836), [STL-74848](https://cornelisnetworks.atlassian.net/browse/STL-74848) | ipoib timeout + SDMA Tx queue stalls — same IPoIB → SDMA transmit path. 74848 has sw_fixed. Note: 76836 may actually be caused by Fabric/MYR cluster (Lynx links to 76494 + 76873). | LLNL (Lynx) | Open / In Progress | Hwang's SDMA fix (74848, sw_fixed) → test if it resolves 76836. If not, root cause is likely fabric-side. |
| **Host Driver — PCIe** | [STL-75661](https://cornelisnetworks.atlassian.net/browse/STL-75661), [STL-76323](https://cornelisnetworks.atlassian.net/browse/STL-76323), [STL-76997](https://cornelisnetworks.atlassian.net/browse/STL-76997) | Cards failing init after power events (75661, 76323) + runtime PCIe fatal errors under SPEC benchmark (76997). All PCIe / 8051 FW initialization path. | Lenovo, IOCB, NEC/RWTH | Open / In Progress | Davis on IOCB (76323). Luick investigating SPEC crash vs uncorrectable PCIe error correlation. 75661 needs pickup (Zhang, Open). |
| **Link / 8051 FW** | [STL-76873](https://cornelisnetworks.atlassian.net/browse/STL-76873) | Link repeatedly fails LNI during EstablishComm.TxRxHunt — 8051 FW SerDes link training. Feeds into LLNL Lynx fabric instability picture. | LLNL (Lynx) | In Progress | Johanson leading via Link Working Group. |
| **Chassis** | [STL-77046](https://cornelisnetworks.atlassian.net/browse/STL-77046) | BMC FruDevice introspect fail — switch enters buggy state after link bounce + reboot testing. Not data-path impacting. New this week. | — | Ready | Queued for Nagarajan. |

---

## SLIDE 2 — BTS / Lustre Detail

### Active (3 bugs)

| Issue | Pri | Summary | Assignee | Status | Customer | Root Cause | Next Steps |
|-------|-----|---------|----------|--------|----------|------------|------------|
| [STL-76950](https://cornelisnetworks.atlassian.net/browse/STL-76950) | P0 | mi300x crash on ctl-c BTS/dmabuf job — `bulksvc_user_info_destroy` | Child | In Review | — | GPU DMA-buf deregistration race in rdmavt. Blocked by: [STL-76982](https://cornelisnetworks.atlassian.net/browse/STL-76982) (DMS unregister rearchitect, **Verify**), [STL-76983](https://cornelisnetworks.atlassian.net/browse/STL-76983) (force-cancel trackers, **Open**), [STL-76984](https://cornelisnetworks.atlassian.net/browse/STL-76984) (rvt/bulksvc thread race, **Open**) | Retest with next DST once all 3 blockers land. 76982 in Verify; 76983 + 76984 still need code. |
| [STL-76880](https://cornelisnetworks.atlassian.net/browse/STL-76880) | P0 | mi300x GPU kernel panic `rvt_send_complete` | Simonson | In Progress | — | Same rdmavt DMA-buf path as 76950. GPU memory invalidation during HFI DMA mapping teardown. | Likely fixed by 76950 cluster patches. Retest together. |
| [STL-76940](https://cornelisnetworks.atlassian.net/browse/STL-76940) | P0 | LNetError RDMA timeout with BTS — Lustre client eviction | Simonson | In Progress | — | Lustre ko2iblnd hitting BTS verbs path. Caused by [STL-76941](https://cornelisnetworks.atlassian.net/browse/STL-76941) (`hfi1_dms_handle_data` crash, **Verify**). Blocked by [STL-76999](https://cornelisnetworks.atlassian.net/browse/STL-76999) (spinwait deadlock, **Verify**). | Zhu: "Wait for 12.1.2 DST to review — we have fixed a few bugs as we investigated this." |

### Verify Queue (5 BTS fixes awaiting validation)

| Issue | Pri | Summary | Owner | What It Fixes |
|-------|-----|---------|-------|---------------|
| [STL-76982](https://cornelisnetworks.atlassian.net/browse/STL-76982) | — | Rearchitect DMS unregister to be always-asynchronous | — | Blocks 76950 (DMA-buf crash) |
| [STL-76999](https://cornelisnetworks.atlassian.net/browse/STL-76999) | — | Fix bulksvc_dbg_open unbounded spin-wait deadlock | Blocksome | Blocks 76940 (Lustre RDMA timeout) |
| [STL-76863](https://cornelisnetworks.atlassian.net/browse/STL-76863) | P0 | BAD WRITE CHECKSUM — BTS MR registration error | Erwin | BTS Lustre data integrity |
| [STL-76847](https://cornelisnetworks.atlassian.net/browse/STL-76847) | P0 | `calculate_mr_page_offset` Invalid — MR offset error | Blocksome | BTS Lustre data integrity |
| [STL-76942](https://cornelisnetworks.atlassian.net/browse/STL-76942) | P0 | bufcount error — BTS buffer management | Erwin | BTS Lustre data integrity |
| [STL-76732](https://cornelisnetworks.atlassian.net/browse/STL-76732) | P0 | `hfi1_dms_impl_dlist_remove` crash — DMS list corruption | Erwin | BTS internal locking |

### Key Takeaway
BTS has 3 active + 6 in Verify. Heavy investment paying off — but 76950's fix depends on 2 patches still Open (76983, 76984). **Next DST build is the gate.**

---

## SLIDE 3 — OPX Detail

### Active (4 bugs)

| Issue | Pri | Summary | Assignee | Status | Customer | Root Cause | Next Steps |
|-------|-----|---------|----------|--------|----------|------------|------------|
| [STL-76365](https://cornelisnetworks.atlassian.net/browse/STL-76365) | P0 | HPL hang in `hfi1_user_exp_rcv_setup` | Cernohous | In Progress | — | OPX TID cache diverges from kernel TID table. Massive link web: [STL-76561](https://cornelisnetworks.atlassian.net/browse/STL-76561), [STL-76972](https://cornelisnetworks.atlassian.net/browse/STL-76972), [STL-76685](https://cornelisnetworks.atlassian.net/browse/STL-76685), [STL-76554](https://cornelisnetworks.atlassian.net/browse/STL-76554). | Debugging TID cache invalidation race — fix must span OPX user-space + hfi1 kernel. |
| [STL-73247](https://cornelisnetworks.atlassian.net/browse/STL-73247) | P0 | sph_exa hang with OPX Open MPI | Erwin | In Progress | — | Same TID cache root cause as 76365. Open since 12.1.0.x — chronic. | Same fix as 76365. |
| [STL-77071](https://cornelisnetworks.atlassian.net/browse/STL-77071) | P0 | MPT-30B hang with aws-ofi dmabuf | Espinoza | Open | RWTH | Possibly OPX + DMA-buf interaction during GPU AI training. Espinoza notes "hang should happen regardless of whether they're using mlx5 or opa" — may be user config. | Engaging RWTH directly. Need to determine if OPX issue or job config issue. |
| [STL-76240](https://cornelisnetworks.atlassian.net/browse/STL-76240) | P1 | IMB Biband/Sendrecv perf drop with OPXS 12.1.0.0-62+ | Simonson | In Progress | AMD | OPX + host driver data path regression. Blocks: [STL-76449](https://cornelisnetworks.atlassian.net/browse/STL-76449), [STL-77018](https://cornelisnetworks.atlassian.net/browse/STL-77018), [STL-76861](https://cornelisnetworks.atlassian.net/browse/STL-76861). | Bisecting OPX builds to isolate regression commit. |
| [STL-77023](https://cornelisnetworks.atlassian.net/browse/STL-77023) | P1 | Endeavour Lustre with use_bulksvc=N | Child | Open | Intel | Lustre data path fails even without BTS — separate root cause from BTS cluster. New this week. | Waiting on server/client dmesg from Intel. |

### Verify Queue (2 OPX fixes)

| Issue | Pri | Summary | Owner | What It Fixes |
|-------|-----|---------|-------|---------------|
| [STL-76561](https://cornelisnetworks.atlassian.net/browse/STL-76561) | P0 | HPL OPX_TID_CACHE assert with use_bulksvc:N | Bollig | Related to TID cache cluster (76365, 73247) |
| [STL-76644](https://cornelisnetworks.atlassian.net/browse/STL-76644) | P0 | NEC IMB-RMA SDMA abort — OPX rendezvous path | Zhang | OPX data path correctness |

### Key Takeaway
TID cache is the chronic OPX issue (76365 + 73247) — architecturally hard, spans user + kernel. Performance regression (76240) is a separate, newer problem. Two new bugs this week (77071, 77023).

---

## SLIDE 4 — Fabric / MYR FW Detail

### Active (5 bugs)

| Issue | Pri | Summary | Assignee | Status | Customer | Root Cause | Next Steps |
|-------|-----|---------|----------|--------|----------|------------|------------|
| [STL-76338](https://cornelisnetworks.atlassian.net/browse/STL-76338) | P0 | tportPktDropPending hang when bouncing ISL under small-packet traffic | Wright | In Progress | TACC | MYR FW Tport state machine hangs when credits drain during link bounce. Relates to [STL-76651](https://cornelisnetworks.atlassian.net/browse/STL-76651), [STL-76652](https://cornelisnetworks.atlassian.net/browse/STL-76652), [ISS-8041](https://cornelisnetworks.atlassian.net/browse/ISS-8041). | Wright investigating Tport credit accounting. Reproduced internally on benchmark cluster. |
| [STL-76494](https://cornelisnetworks.atlassian.net/browse/STL-76494) | P0 | Hung nodes under 12.1.0.1.x due to RbufCtrlSbe | Rothermel | In Progress | TACC | SRAM ECC single-bit errors corrupt buffer management → node hangs. Label: sw_fixed. Relates to [STL-76836](https://cornelisnetworks.atlassian.net/browse/STL-76836), [STL-77090](https://cornelisnetworks.atlassian.net/browse/STL-77090). | Software workaround exists (sw_fixed). Watch SBE rate — if increasing, could indicate HW degradation. |
| [STL-76725](https://cornelisnetworks.atlassian.net/browse/STL-76725) | P1 | Excessive TxHoqDiscards | King | In Progress | TACC | Head-of-queue blocking in MYR switch, same credit/buffer subsystem. Relates to [STL-75822](https://cornelisnetworks.atlassian.net/browse/STL-75822). | Reproduced internally with synthetic ISL saturation. King analyzing. |
| [STL-75962](https://cornelisnetworks.atlassian.net/browse/STL-75962) | P1 | Job hang — running out of credits on MYR Tport | Rothermel | In Progress | — | MYR transport credit exhaustion. Relates to [STL-75847](https://cornelisnetworks.atlassian.net/browse/STL-75847). | Credit accounting analysis in progress. |
| [STL-77092](https://cornelisnetworks.atlassian.net/browse/STL-77092) | P0 | DWC switch VR fault on liquid-cooled switch | Nagarajan | In Review | Lenovo | Voltage regulator fault in switch hardware — separate from buffer/credit issues. New this week. | Fix in review. |

### Key Takeaway
MYR buffer/credit cluster is the riskiest area — **4 bugs, all In Progress, zero fixes landed.** TACC is primary customer. 76494 has sw_fixed workaround. 77092 (VR fault) is separate and close to landing.

---

## SLIDE 5 — Host Driver Detail

### Active (5 bugs)

| Issue | Pri | Summary | Assignee | Status | Customer | Root Cause | Next Steps |
|-------|-----|---------|----------|--------|----------|------------|------------|
| [STL-76836](https://cornelisnetworks.atlassian.net/browse/STL-76836) | P0 | ipoib timeout at LLNL Lynx | Novak | Open | LLNL (Lynx) | IPoIB → SDMA transmit path stall. BUT: Jira links to [STL-76494](https://cornelisnetworks.atlassian.net/browse/STL-76494) (RbufCtrlSbe) + [STL-76873](https://cornelisnetworks.atlassian.net/browse/STL-76873) (link training). McGinnis observed ipoib issues correlate with link/fabric anomalies — may be fabric-caused. | Test 74848 SDMA fix first. If unresolved, root cause is likely fabric-side (Cluster B). |
| [STL-74848](https://cornelisnetworks.atlassian.net/browse/STL-74848) | P1 | SDMA Tx queue timeout — no descriptors available for ipoib | Hwang | In Progress | — | SDMA descriptor exhaustion under concurrent ipoib traffic. Label: sw_fixed. | Fix ready (sw_fixed). Retest in next DST → if fixes 76836 too, closes 2 bugs. |
| [STL-76997](https://cornelisnetworks.atlassian.net/browse/STL-76997) | P0 | Job crashes during SPEC run at NEC/RWTH | Luick | Open | NEC/RWTH | Host driver crash path. Relates to [STL-75193](https://cornelisnetworks.atlassian.net/browse/STL-75193) (fatal PCIe error). Luick: "proceed — if we see errors from the driver we can perhaps correlate the uncorrectable error." | Investigating PCIe uncorrectable error correlation. Koch providing lspci output. |
| [STL-75661](https://cornelisnetworks.atlassian.net/browse/STL-75661) | P1 | Link not Active after power-cycle stress test | Zhang | Open | Lenovo | 8051 FW / JKR FW PCIe init — card fails to enumerate after power-cycle. | **Needs pickup** — Zhang assigned but Open, no recent activity. |
| [STL-76323](https://cornelisnetworks.atlassian.net/browse/STL-76323) | P1 | PCIe enumeration / HFI init failures | Davis | In Progress | IOCB | Same PCIe init path as 75661. 5 failed jobs out of 204 — improved but not resolved. Blocks [STL-75847](https://cornelisnetworks.atlassian.net/browse/STL-75847). | Davis actively investigating. IOCB repro rate reduced. |

### Verify Queue (2 Host Driver fixes)

| Issue | Pri | Summary | Owner | What It Fixes |
|-------|-----|---------|-------|---------------|
| [STL-77078](https://cornelisnetworks.atlassian.net/browse/STL-77078) | P0 | Nightly CI IB Verbs Atomic BW failure | Hibbard | CI regression |
| [STL-76108](https://cornelisnetworks.atlassian.net/browse/STL-76108) | P1 | SRIOV VMs cannot query SA | Miller | sw_fixed |

### Key Takeaway
76836 (LLNL ipoib) is the most interesting — it may not be a host driver bug at all. If 74848's SDMA fix doesn't resolve it, look at fabric side. 75661 (Lenovo power-cycle) needs attention — Open with no activity.

---

## SLIDE 6 — Link / 8051 FW + Chassis Detail

### Active (2 bugs)

| Issue | Pri | Summary | Assignee | Status | Customer | Root Cause | Next Steps |
|-------|-----|---------|----------|--------|----------|------------|------------|
| [STL-76873](https://cornelisnetworks.atlassian.net/browse/STL-76873) | P0 | Link repeatedly fails LNI during EstablishComm.TxRxHunt | Johanson | In Progress | LLNL (Lynx) | 8051 FW SerDes/link training failure — handful of links not coming up with MYR FW 12.1.0.2.9 / JKR FW 12.1.0.1.1. About 8 links affected across fabric. Linked to [STL-76836](https://cornelisnetworks.atlassian.net/browse/STL-76836) (ipoib timeout). | Johanson leading via Link Working Group. Analyzing SerDes tuning vs cable qualification. |
| [STL-77046](https://cornelisnetworks.atlassian.net/browse/STL-77046) | P1 | BMC FruDevice introspect fail — switch in buggy state | Nagarajan | Ready | — | Chassis management. BMC fails FruDevice introspect after ~17h of link bounce + reboot testing. Not data-path impacting. New this week. | Queued for Nagarajan. |

---

## Root Cause Cluster Summary

| # | Root Cause | Active | Verify | Closed | Fix One, Fix All? |
|---|-----------|:------:|:------:|:------:|-------------------|
| 1 | **BTS DMA-buf deregistration** race | 3 | 6 | 1 | Yes — 76950 fix in review → cascade-fixes 76880 + 76940. But 2 of 3 blocking patches still Open. |
| 2 | **OPX TID cache** kernel divergence | 2 | 1 | — | Yes — same architectural fix needed. Complex (user + kernel). |
| 3 | **MYR buffer/credit** switch FW | 4 | — | — | Partially — related but may need separate fixes for each manifestation. Zero resolved. |
| 4 | **IPoIB / SDMA** transmit | 2 | — | — | Maybe — 74848 sw_fixed may resolve 76836. If not, 76836 is fabric-caused. |
| 5 | **PCIe / card init** | 3 | — | — | Partially — 75661 + 76323 same init path, 76997 is runtime. |
| 6 | **OPX GPU AI** | 1 | — | 2 | TBD — 77071 may be user config, not OPX bug. |
| 7 | **OPX perf regression** | 1 | 1 | 1 | Separate — bisecting to isolate commit. |
| 8 | **Link training** 8051 FW | 1 | — | — | Standalone. Link WG owns. |
| — | Standalone (Lustre non-BTS, MYR VR, BMC, CI, SRIOV) | 4 | 2 | — | Each separate. |

---

## Key Callouts

1. **BTS is the #1 area** — 3 active + 6 in Verify. Heavy investment paying off, but 76950 depends on 2 patches still in Open (76983, 76984). **Next DST build is the gate.**

2. **MYR buffer/credit is riskiest** — 4 bugs, all In Progress, zero fixes landed. TACC is primary customer.

3. **76836 (LLNL ipoib)** may not be a host driver bug — Jira links and field observations suggest fabric instability as root cause. Test SDMA fix first; if no resolution, reclassify.

4. **OPX TID hangs still chronic** — 73247 open since 12.1.0.x. Architecturally complex fix.

5. **75661 (Lenovo power-cycle) needs pickup** — assigned to Zhang, Open, no recent activity.
