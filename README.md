HEAD
# AICTE FlowGuard

**SIH Problem Statement 26262:** Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Alert Management System  
**Organisation:** All India Council for Technical Education (AICTE)  
**Department:** Regulation Bureau  
**Theme:** Smart Automation  

---

## 1. Executive Summary & Core Objective

**AICTE FlowGuard** is a full-stack, enterprise-grade regulatory management platform engineered to automate institutional approval lifecycles, monitor statutory compliance undertakings, and orchestrate time-sensitive administrative actions.

Unlike rigid software that hardcodes approval workflows, AICTE FlowGuard features a **database-backed configurable state machine**, an auditable **Dual-Clock Calculation Engine** that distinguishes institutional response time from official statutory processing, and an **Explainable AI Scrutiny Intelligence Engine** that assists officials without replacing human regulatory oversight.

```
+-----------------------------------------------------------------------------------+
|                                 AICTE FLOWGUARD                                   |
+-----------------------------------------------------------------------------------+
|  PORTAL 1: Institution Portal       PORTAL 2: Official Portal  PORTAL 3: Admin    |
|  - Applications, Uploads, Clock,    - Scrutiny, EVC, Clock,    - Workflows, Users,|
|    Clarifications, Compliance         Findings, Escalations      Rules, Audit Logs|
+------------------------------------------+----------------------------------------+
|                   REST API (FastAPI + Pydantic v2 + JWT RBAC)                     |
+-------------------+----------------------+--------------------+-------------------+
| Configurable      | Dual-Clock Engine    | AI Scrutiny Engine | Background &      |
| Workflow Engine   | - Institution Clock  | - Secure Ingestion | Escalation Engine |
| - State Machine   | - Official Clock     | - Deterministic    | - APScheduler     |
| - Prerequisites   | - Business/Calendar  |   Extraction & OCR | - Due tracking    |
| - Transition RBAC | - Audit Adjustments  | - Priority Score   | - In-App Alerts   |
+-------------------+----------------------+--------------------+-------------------+
|            PostgreSQL 18 Database (SQLAlchemy 2.0 ORM + Alembic Migrations)        |
+-----------------------------------------------------------------------------------+
```

---

## 2. Technology Stack

- **Frontend:**
  - React 19 + TypeScript + Vite 8
  - Tailwind CSS v4
  - React Router v7
  - Recharts (for workload analytics, stage durations, and bottleneck detection)
  - React Hook Form with Zod validation
  - Lucide React accessible icons
- **Backend:**
  - Python 3.14 + FastAPI
  - SQLAlchemy 2.0 ORM
  - Alembic database migrations
  - Pydantic v2 validation
  - PostgreSQL 18
  - Passlib + Bcrypt password hashing
  - PyJWT token authentication
  - APScheduler 3.x background task scheduler
- **Document Scrutiny:**
  - Secure private local storage (`./storage/documents`), completely isolated from public assets
  - PyPDF deterministic layout and text extraction
  - Regex-based field identification and cross-document validation rules
  - Explainable Scrutiny Priority Score (0–100)
- **Testing:**
  - Pytest backend test suite (14 automated tests passing)

---

## 3. The Three Distinct Portals

### A. Institution Portal
1. **Interactive Dashboard:** View live status of applications, upcoming compliance deadlines, pending clarification requests, and expiring statutory certificates.
2. **Application Lifecycle:** Create, edit draft, submit, and track approval applications in real time.
3. **Clarification Workflow:** When an application is returned by officials with mandatory reasons, the institutional clock turns active. Colleges submit detailed response statements and corrected documents.
4. **Document Vault:** Securely upload mandatory documents (Land Title Deeds, Building Blueprints, Fire Safety NOCs, University Affiliation letters, Faculty Cadre Rosters) with SHA-256 hash tracking and versioning.
5. **Compliance & Undertakings:** View time-bound conditional undertakings (e.g. STP installation, barrier-free access) and upload verified completion certificates.
6. **Data Isolation:** Institutions can **never** access another institution's private records or dossiers.

### B. AICTE Officials Portal
Supports granular role-based access control (RBAC):
- **Scrutiny Officer:** Inspects uploaded documents, reviews AI scrutiny findings, confirms/overrides extracted data, returns applications for clarification, and forwards to EVC.
- **EVC Coordinator:** Schedules Expert Visiting Committee physical inspections, checks officer calendars for scheduling conflicts, and records visit reports.
- **Document Verifier:** Validates certificates and records issue/expiry dates into the statutory register.
- **Compliance Officer:** Reviews submitted undertakings evidence and marks them as Accepted, Correction Requested, or Rejected.
- **Regional Officer:** Monitors regional work queues, pendency bottlenecks, and regional approvals.
- **Bureau Authority / Competent Authority:** Grants final statutory AICTE approvals or issues formal rejections.

Key features:
1. **Role-Filtered Work Queue:** Sorted by stage, region, and Scrutiny Priority Score badge.
2. **Dual-Clock Breakdown:** Real-time visibility into whether elapsed time belongs to the institution or the official bureau.
3. **Authorized Clock Pause/Resume:** Officials can pause the statutory clock during judicial stays, formal hearings, or public inquiry windows with recorded citations.
4. **AI Scrutiny Inspector:** Review extracted fields, citation page references, and cross-document inconsistencies. Record official confirmation or overrides with logged notes.

### C. System Administration Portal
1. **User & Role Provisioning:** Create officials and link institutional users to affiliated colleges.
2. **Configurable Workflow State Machine:** Inspect and modify active stages, permitted transitions, transition prerequisite checks, and SLA durations without recompiling code.
3. **System Health & Escalation Engine:** Run on-demand deadline checks and view auto-escalated overdue tasks.
4. **Audit Trail & CSV Exports:** Complete searchable history of stage transitions, document downloads, and score overrides. Export summary reports to CSV.

---

## 4. Differentiating Core Engines

### 1. Dual-Clock Engine
Tracks:
- **Institution Response Clock:** Elapsed duration while waiting on institutional action (draft preparation, responding to clarification requests, or submitting compliance evidence).
- **Official Processing Clock:** Statutory elapsed time during AICTE official processing (scrutiny review, EVC scheduling, committee evaluation).
- Subtracts authorized pause intervals and public holidays (Republic Day, Independence Day, Gandhi Jayanti).
- Provides an explainable breakdown of elapsed days, hours, percentages, and formula citations.

### 2. Secure AI Scrutiny Intelligence Engine
- **Step 1: Secure Ingestion:** Validates MIME types (`application/pdf`, `image/png`, `image/jpeg`), magic signatures, file size limits (15 MB), and generates private server-controlled UUID storage paths.
- **Step 2: Extraction:** Deterministically extracts Institution Name, Land Area (Acres), Built-up Area (Sq.m), Issue/Expiry Dates, Approved Intake, and Faculty Counts.
- **Step 3: Rule-based Verification:** Compares extracted values with application declarations, cross-checks Land Deed vs Building Plan, validates Fire Safety active dates, and identifies missing mandatory evidence.
- **Step 4: Explainable Scrutiny Priority Score (0–100):**
  $$\text{Priority Score} = \min(100, \text{Missing Docs Pts} + \text{Inconsistency Pts} + \text{Expired Docs Pts} + \text{Low Confidence Pts})$$
  - **Standard Review Priority (0–24):** Routine dossier, standard scrutiny.
  - **Enhanced Review Priority (25–74):** Minor data mismatches or near-expiry items.
  - **High Review Priority (75–100):** Missing mandatory documents or expired statutory clearances.
  - **Non-Negotiable Rule:** A low score *never* bypasses required human scrutiny. A high score *never* automatically rejects an institution. Human officers must review and confirm all findings.

### 3. EVC Inspection & Conflict Detection Engine
- Validates proposed committee members across all active visits.
- Automatically throws a `409 Conflict` if an assigned expert is already scheduled for another physical inspection on the same calendar date.
- Manages an interactive 6-point statutory inspection checklist.

---

## 5. Demonstration Accounts & Seed Data

The database comes pre-seeded with 11 accounts covering all roles. All demo accounts use the password: `DemoPass123!`

| Role | Name & Designation | Email | Portal |
|---|---|---|---|
| **ADMIN** | Rajesh Sharma (System Administrator) | `admin@flowguard.aicte.gov.in` | Administration |
| **SCRUTINY_OFFICER** | Dr. Vikram Sen (Senior Scrutiny Officer) | `scrutiny.officer@aicte.gov.in` | Officials |
| **EVC_COORDINATOR** | Prof. Sunita Rao (Regional EVC Coordinator) | `evc.coordinator@aicte.gov.in` | Officials |
| **DOCUMENT_VERIFIER** | Anil Kumar (Document Verifier) | `doc.verifier@aicte.gov.in` | Officials |
| **COMPLIANCE_OFFICER** | Pooja Deshmukh (Compliance Officer) | `compliance.officer@aicte.gov.in` | Officials |
| **REGIONAL_OFFICER** | Dr. Harish Patel (Regional Officer North) | `regional.officer@aicte.gov.in` | Officials |
| **BUREAU_AUTHORITY** | Dr. K. N. Murthy (Advisor & Competent Authority)| `bureau.authority@aicte.gov.in` | Officials |
| **INSTITUTION (Tech)** | Dr. Alok Verma (Principal, Apex Tech) | `institution@flowguard.aicte.gov.in` | Institution |
| **INSTITUTION (Arch)** | Ar. Meera Joshi (Director, Saraswati Arch) | `saraswati@flowguard.aicte.gov.in` | Institution |
| **INSTITUTION (Pharm)**| Dr. Ramesh Hegde (Dean, Greenfield Pharm) | `greenfield@flowguard.aicte.gov.in` | Institution |
| **INSTITUTION (Mgmt)** | Prof. S. K. Mukherjee (Director, Vidya Sagar)| `vidya@flowguard.aicte.gov.in` | Institution |

### Pre-Seeded Test Scenarios
1. **Application `AICTE-2026-APEX-001` (Standard Priority, Score: 0):** Complete document package (Land Deed 5.0 Acres, Building Plan 8500 Sq.m, Fire Safety valid to 2028, University Affiliation, Faculty list).
2. **Application `AICTE-2026-SARA-002` (Enhanced Priority, Score: 20):** Data mismatch (7.5 Acres declared in application vs 5.0 Acres in Land Deed).
3. **Application `AICTE-2026-GREN-003` (High Priority, Score: 45):** Missing University Affiliation NOC and expired Fire Safety Certificate.
4. **Application `AICTE-2026-VIDY-004` (Clarification Required):** Under active Institutional Response Clock; officer deficiency note provided.
5. **Application `AICTE-2026-APEX-005` (EVC Scheduled):** Active EVC inspection with 3 committee members assigned.
6. **Application `AICTE-2026-APEX-006` (Final Approval & Active Undertakings):** Approved application with active compliance undertakings.

---

## 6. How to Run Locally

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 14+ (or running PostgreSQL service on port 5432)

### Step 1: Backend Setup
```powershell
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run database seed script (creates PostgreSQL schema and loads synthetic test cases)
python seed_data.py

# Start FastAPI backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Backend API will be running at `http://127.0.0.1:8000`.  
Interactive Swagger docs: `http://127.0.0.1:8000/docs`.

### Step 2: Frontend Setup
```powershell
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install dependencies (if not already installed)
npm install

# Start Vite development server
npm run dev
```
Frontend will be available at `http://127.0.0.1:5173`.

### Step 3: Run Automated Test Suite
```powershell
cd backend
python -m pytest
```
Output:
```
======================= 14 passed, 24 warnings in 2.25s =======================
```

---

## 7. Feature Completion Verification

| Specification Requirement | Implemented | Verification Evidence |
|---|---|---|
| Institution Portal | Yes | Full application submission, documents vault, clarifications, compliance |
| Official Portal (Granular Roles) | Yes | Work queue, scrutiny review, EVC, compliance review, role permissions |
| Administration Portal | Yes | User provisioning, workflow configuration, audit trail, CSV export |
| Configurable Workflow Engine | Yes | State machine with 11 stages, transitions, allowed roles, prerequisites |
| Dual-Clock Engine | Yes | Tracks Institution vs Official clock, authorized pauses, holiday subtraction |
| AI Scrutiny Intelligence | Yes | Secure ingestion, deterministic field extraction, cross-document checks |
| Explainable Scrutiny Priority Score | Yes | Documented factor formula (0–100), Standard/Enhanced/High triage bands |
| Human Oversight Mandate | Yes | AI cannot reject/approve; low score cannot bypass; official review recorded |
| EVC Scheduling & Conflict Checks | Yes | Panels scheduled, conflict check throws 409 on double booking, checklists |
| Undertakings & Compliance | Yes | Time-bound due dates, evidence uploads, official accept/reject/correction |
| Document Expiry Register | Yes | Expiry alerts (<30d, <90d, expired), days remaining counter |
| In-App Notifications & Escalation | Yes | PostgreSQL stored, deadline warnings, 48h overdue supervisor escalation |
| Real DB Analytics (No mocks) | Yes | Real aggregation queries for pie charts, bottleneck bars, workload |
| PostgreSQL 18 + SQLAlchemy + Alembic | Yes | Models with foreign keys, indexes, and initial Alembic migration |
| Data Security & Isolation | Yes | Strict server-side ownership checks; private document storage |
| Automated Pytest Suite | Yes | 14 integration tests passing across all critical features |

---

## 8. Known Limitations & Production Safeguards

1. **Optical Character Recognition (OCR):** In this prototype, digital text extraction is handled via `pypdf`. For scanned, low-quality physical documents, an external Tesseract or private microservice can be plugged in without changing the core engine interface.
2. **Email Delivery:** In-app notifications are stored persistently in PostgreSQL. Production deployment should attach an SMTP relay (e.g. AWS SES or government NIC mail server).
3. **Secret Rotation:** Default development keys are provided in `.env.example`. In production, `JWT_SECRET` and database credentials must be injected via secure secret managers (e.g. HashiCorp Vault or AWS Secrets Manager).
4. **Antivirus Scanning:** Private document ingestion verifies MIME signatures, file extensions, and file sizes. In production, a ClamAV daemon should be added to the upload pipeline.
=======
# AICTE-FLOWW



