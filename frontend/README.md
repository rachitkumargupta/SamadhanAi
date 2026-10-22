# 🇮🇳 Samadhan AI — Frontend Application

**AI-Powered Multi-Agent Civic Complaint Management System**  
Built by **Team KAFKA** for civic governance and automated municipal issue resolution.

---

## 🏛️ System Overview

As defined in the project architecture specification (Slide 1 & Slide 7), Samadhan AI coordinates **3 Specialized AI Agents** through an 8-layer architecture:

1. **User Layer**: Role-based web/mobile interfaces:
   - **Citizen Portal**: Submit complaints with auto-tagging, location capture, attachment previews, and full lifecycle tracking.
   - **Officer Dashboard**: Departmental work queue, SLA breach warning countdowns, resolution action logging, and citizen status updates.
   - **Admin Command Center**: City-wide governance dashboard with real-time analytics, SLA compliance metrics, department workload tracking, and officer performance audits.
2. **AI Layer Coordination**:
   - **Agent 1: Complaint Analyst Agent**: Understands civic issues, classifies categories (Roads, Water, Sanitation, Electricity, Drainage, etc.), assesses severity, flags missing info & detects duplicates.
   - **Agent 2: Resolution & Routing Agent**: Identifies jurisdiction, assigns designated officer/department, establishes adaptive SLA deadlines, and dispatches automated notifications.
   - **Agent 3: Monitoring & Escalation Agent**: Real-time SLA tracker that monitors progress, keeps citizens informed at each state change, and escalates delayed tickets to senior municipal authorities upon breach.

---

## 🚀 Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | React 19 + TypeScript |
| **Bundler / Tooling** | Vite 8 |
| **Styling** | Tailwind CSS v4 |
| **Routing** | React Router v7 |
| **Icons** | Lucide React |
| **Data Visualizations** | Recharts (Weekly Trends & Category Distributions) |
| **State Management** | Context API (Role-Based Authentication & Live Notifications) |

---

## 📦 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   └── AppShell.tsx              # Responsive sidebar, navigation & notification center
│   │   └── ui/
│   │       ├── Badge.tsx                 # Status & Severity indicators
│   │       ├── ComplaintCard.tsx         # Ticket preview with SLA breach alerts
│   │       ├── ComplaintTimeline.tsx     # Agent & officer action event stream
│   │       └── StatCard.tsx              # Analytics metric cards with trend indicators
│   ├── context/
│   │   └── AuthContext.tsx               # Instant role-switcher (Citizen / Officer / Admin)
│   ├── data/
│   │   └── mockData.ts                   # Realistic civic complaints, departments & officers
│   ├── pages/
│   │   ├── LoginPage.tsx                 # Interactive multi-role portal launcher
│   │   ├── citizen/
│   │   │   ├── CitizenDashboard.tsx      # Welcome overview, quick stats & recent complaints
│   │   │   ├── CitizenComplaints.tsx     # Filterable list of filed grievances
│   │   │   ├── SubmitComplaint.tsx       # 3-step wizard with simulated AI analysis
│   │   │   └── ComplaintDetail.tsx       # Live status, location, AI reasoning & audit trail
│   │   ├── officer/
│   │   │   ├── OfficerDashboard.tsx      # Assigned queue, SLA timers & resolution statistics
│   │   │   ├── OfficerComplaints.tsx     # Departmental ticket table with status filters
│   │   │   └── OfficerComplaintDetail.tsx# Status transition form (In Progress, Resolved)
│   │   └── admin/
│   │       ├── AdminDashboard.tsx        # High-level metrics, charts & department breakdown
│   │       ├── AdminComplaints.tsx       # Complete civic complaint registry
│   │       ├── AdminDepartments.tsx      # Department workloads & resolution rates
│   │       └── AdminOfficers.tsx         # Municipal officer accountability directory
│   ├── types/
│   │   └── index.ts                      # Strict TypeScript interfaces matching system schema
│   ├── App.tsx                           # Master route configuration & guards
│   ├── main.tsx                          # Application entry point
│   └── index.css                         # Custom theme variables & design tokens
```

---

## 💻 Running the Frontend

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

The application runs at `http://localhost:5173`.

### 3. Production Build
```bash
npm run build
```
Generates an optimized bundle ready for deployment.

---

## 👥 Demo Logins

No credentials needed! Simply visit `/login` and select your persona:

1. **Citizen** (`Ramesh Sharma`) — Experience submitting complaints and receiving automated AI triage feedback.
2. **Officer** (`Vikram Singh`, Roads & Infrastructure) — Inspect assigned tasks and record on-ground progress.
3. **Admin** (`Rachit Kumar Gupta`, Municipal Leader) — Audit overall department efficiency, SLA adherence, and escalate bottlenecks.
