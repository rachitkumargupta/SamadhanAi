# Samadhan AI — Frontend Portal

An official, responsive Government Portal interface for the **Samadhan AI** Multi-Agent Civic Grievance Resolution Platform. Built with React 19, TypeScript, Vite, Tailwind CSS, and Leaflet.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run the Development Server
```bash
npm run dev
```
The app will be running at `http://localhost:5173`.

---

## ⚡ Backend Integration & Proxy

The development server includes a built-in proxy in `vite.config.ts`:
- `/api` → `http://localhost:8000` (FastAPI backend)
- `/health` → `http://localhost:8000`

### Zero CORS Issues
Requests from the frontend are proxied directly to FastAPI, avoiding all browser CORS restrictions in development.

---

## 🛠 Features

1. **Online Grievance Registration Form (`/lodge`)**:
   - Photographic evidence capture/upload with camera support and `< 10 MB` validation.
   - 1-click **Auto-Detect GPS Location** (`navigator.geolocation`) with reverse-geocoding.
   - Interactive **OpenStreetMap / Leaflet** map pin (100% free, zero API keys required).
   - Character-counted narrative description.
   - Multipart form submission directly to `POST /api/v1/complaints`.

2. **Grievance Status Details & ATR (`/status`)**:
   - Official 2-column municipal summary table.
   - Live polling for **Agent 1 (AI Complaint Analyst)** assessment findings.
   - Official **Action Taken Report (ATR) / Audit History** table.
   - **Citizen Resolution Verification** strip with 48-hour confirm/dispute actions.

3. **Registered Grievances Log (`/history`)**:
   - Searchable and filterable master log of submitted grievances.

4. **Municipal Officer Review Queue (`/officer`)**:
   - Access to normalized complaint photographs (`/reviews/{ref}/image`).
   - Side-by-side evidence inspection and departmental work order allocation.

5. **Universal Accessibility & Mode Controls**:
   - Working **Dark Mode** toggle.
   - **Mode Switcher**: 1-click toggle between **Live API (Port 8000)** and **Mock Demo** mode so anyone can test the full flow even without PostgreSQL running.
   - **Portal Switcher**: 1-click swap between **Citizen Portal** and **Officer Portal** (automatically generates valid HS256 tokens matching the backend).
