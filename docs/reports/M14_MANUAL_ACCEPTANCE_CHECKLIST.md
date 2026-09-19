# M14 Manual Acceptance Checklist

**Platform**: MuleTrace AI  
**Milestone**: Milestone 14 (M14) — BUILD IT Release / Hardening  
**Target Environment**: Localhost (`http://localhost:3000` & `http://127.0.0.1:8000`)  
**Status**: **PENDING USER VALIDATION**  

> [!NOTE]
> This checklist must be manually executed in the browser by the developer / manual tester.
> Automated tests have passed 100%, and the local backend and frontend instances are currently running.

---

## Service Endpoints for Manual Testing

- **Frontend Application**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Primary Benchmark Case**: `CAS-2025-0045` (Western Region Mule Ring)
- **Secondary Benchmark Case**: `CAS-2025-0046` (Andheri Fan-In Hub)

---

## Test Cases

### MT-01 — Application Load
- **Action**: Open [http://localhost:3000](http://localhost:3000) in your web browser.
- **Verification Criteria**:
  - [ ] Page loads cleanly without a blank screen
  - [ ] No fatal uncaught JavaScript errors in browser console
  - [ ] Navigation sidebar renders with MuleTrace AI logo
  - [ ] Redirects smoothly to `/dashboard`
  - [ ] Backend status indicator displays operational state
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-02 — Dashboard
- **Action**: Navigate to `/dashboard`.
- **Verification Criteria**:
  - [ ] Dashboard overview widgets render
  - [ ] High-level KPI metrics display (e.g., active alerts, flagged accounts, system risk)
  - [ ] No indefinite loading spinners
  - [ ] Chart/metrics visualizations render without layout distortion
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-03 — Alerts Triage
- **Action**: Click on "Alert Triage" (`/alerts`) in the sidebar.
- **Verification Criteria**:
  - [ ] Alert queue loads with active alerts
  - [ ] Severity badges render (CRITICAL, HIGH, MEDIUM, LOW)
  - [ ] Selecting an alert displays alert details/metadata
  - [ ] Status triage actions are selectable
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-04 — Investigations Case View
- **Action**: Click on "Investigations" (`/investigations`) in the sidebar.
- **Verification Criteria**:
  - [ ] Investigation cases grid loads (`CAS-2025-0045`, `CAS-2025-0046`, etc.)
  - [ ] Case numbers, titles, priority badges, and alert counts render
  - [ ] Clicking `CAS-2025-0045` activates the case detail board
  - [ ] Case Overview card and Evidence Timeline card display correctly
  - [ ] M13 Deterministic Risk Intelligence panel renders below the case cards
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-05 — M10 Risk Fusion Display
- **Action**: Review the Risk Fusion section inside the active case `CAS-2025-0045`.
- **Verification Criteria**:
  - [ ] Composite Risk Score is visible (e.g., `12.0%` or evaluated score)
  - [ ] Categorical Risk Level badge displays (`LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`)
  - [ ] Score strictly matches the backend API response without client-side math drift
  - [ ] 5-modality contributions grid displays all modalities:
    - Modular Rules (M5)
    - Temporal Intelligence (M6)
    - Graph Intelligence (M7)
    - Tabular ML (M8)
    - Graph ML / GNN (M9)
  - [ ] Progress bars and effective weight points render for each active modality
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-06 — M11 Auditable Evidence Dossier
- **Action**: Scroll to the "Auditable Evidence Items" section in `CAS-2025-0045`.
- **Verification Criteria**:
  - [ ] Total verified evidence count is displayed
  - [ ] Individual evidence cards render with verified IDs (e.g., `EVD-TEMPORAL-...`)
  - [ ] Category, Title, Description, and Severity badges render
  - [ ] Associated entities (Account IDs, Transaction IDs, IP addresses) are visible
  - [ ] No hallucinated evidence IDs or placeholder strings
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-07 — M12 Investigation Copilot Insights
- **Action**: Inspect the "Deterministic Copilot Summary & Key Findings" section.
- **Verification Criteria**:
  - [ ] Executive Narrative summary appears with clean prose
  - [ ] Key Forensic Findings list displays severity badges and linked evidence tags
  - [ ] Recommended Investigation Actions appear with priority tags (`IMMEDIATE`, `HIGH`, `MEDIUM`)
  - [ ] Action type tags render (e.g., `TEMPORAL_AUDIT`, `RESTRICT_ACCOUNT`, `FILE_SAR`)
  - [ ] Investigator follow-up questions and audit limitations are visible
  - [ ] Zero LLM loading spinners or generative delays
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-08 — Graph Intelligence
- **Action**: Click on "Graph Intelligence" (`/graph`) in the sidebar.
- **Verification Criteria**:
  - [ ] Graph canvas loads and mounts
  - [ ] Account and entity nodes render with visual distinctions
  - [ ] Transaction and relationship edges connect nodes
  - [ ] Graph controls (zoom, pan, search, filter) respond to user input
  - [ ] Selecting a node highlights its local neighborhood
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-09 — Geo Intelligence
- **Action**: Click on "Geo Intelligence" (`/geo`) in the sidebar.
- **Verification Criteria**:
  - [ ] Geographic intelligence map canvas loads
  - [ ] Regional risk clusters or travel anomaly markers display
  - [ ] Interactive zoom and map controls work smoothly
  - [ ] No Map/Leaflet rendering errors in the browser console
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-10 — Reports Management
- **Action**: Click on "Reports" (`/reports`) in the sidebar.
- **Verification Criteria**:
  - [ ] Reports management table renders
  - [ ] Existing generated STR/CTR/Cybercrime reports display
  - [ ] Filtering and search controls function as expected
  - [ ] Report details modal opens upon clicking a report row
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-11 — Full End-to-End Investigation Workflow
- **Action**: Perform complete investigator journey:
  1. Open `/alerts` -> Inspect high-severity alert.
  2. Open `/investigations` -> Select `CAS-2025-0045`.
  3. Review composite risk score and modality breakdown.
  4. Cross-reference evidence item `EVD-TEMPORAL-...`.
  5. Read copilot narrative and note suggested next steps.
  6. Navigate to `/graph` to observe transaction topology.
  7. Return to `/investigations` -> Select `CAS-2025-0045`.
- **Verification Criteria**:
  - [ ] Case intelligence persists and remains identical upon return
  - [ ] Modality weights and evidence IDs do not flicker or randomize
  - [ ] Navigation is seamless and responsive
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-12 — Mock / Offline Fallback Safety
- **Action**: Evaluate the visual indicators for live vs. fallback intelligence.
- **Verification Criteria**:
  - [ ] When connected to live backend, status pill indicates `LIVE` and intelligence is evaluated in real time
  - [ ] If backend is temporarily paused, fallback intelligence clearly shows `DEGRADED MODE` badge
  - [ ] Fallback limitations explicitly state: `"[OFFLINE / DEMO FALLBACK] Showing simulated benchmark fallback data"`
  - [ ] Simulated benchmark data is never silently misrepresented as live production intelligence
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-13 — Browser Refresh & History Navigation
- **Action**: Test browser actions:
  - Refresh `/investigations` page.
  - Navigate Dashboard -> Alerts -> Investigations -> Graph -> Reports.
  - Click Browser Back twice, then Browser Forward twice.
- **Verification Criteria**:
  - [ ] No 404 route errors on reload
  - [ ] No stuck spinner or frozen state
  - [ ] Active state is restored cleanly
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

### MT-14 — Error Handling & Boundary Safety
- **Action**:
  - Navigate to invalid case URL: `http://localhost:3000/investigations?case=NON-EXISTENT-CASE`
  - Query Swagger API directly with unknown case: `GET /api/v1/investigations/UNKNOWN-999`
- **Verification Criteria**:
  - [ ] API cleanly returns HTTP 404 with structured JSON error
  - [ ] No uncaught 500 internal server error
  - [ ] No sensitive stack traces or internal secrets leaked
  - [ ] Backend process remains alive and continues serving subsequent requests
- **Result**: `[ ] PASS` / `[ ] FAIL`
- **Tester Notes**:

---

## Acceptance Sign-Off

- **Manual Testing Date**: ____________________
- **Tester Name**: ____________________
- **Overall Result**: `[ ] ACCEPTED` / `[ ] REJECTED`
