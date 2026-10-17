# SignalFlow AI — React Frontend Architecture & Integration Guide

## 1. Overview

The SignalFlow AI React frontend is an institutional-grade fintech dashboard built to visualize the **Strands Decider 2B System 1 Local Policy Gatekeeper** paired with **Google AI Studio's Gemini 3.5 System 2 Analysis**.

It replaces the basic single-page Streamlit experience with a responsive single-page React web application designed after leading financial analytics platforms (**SentimentIQ**, **VoiceWatch AI**, and **AlphaPro**).

---

## 2. Technology Stack

- **Framework:** React 19 with TypeScript
- **Tooling:** Vite 8 (Hot Module Replacement, fast bundling)
- **Styling:** Tailwind CSS v4 with custom dark fintech design tokens
- **Typography:** Google Fonts (`Inter` for UI, `JetBrains Mono` for tickers and latencies)
- **Icons:** `lucide-react`
- **Charts:** `recharts` for interactive SVG charts and donut gauges
- **Testing:** `vitest` + `@testing-library/react` + `@testing-library/jest-dom`
- **Backend Bridge:** FastAPI (`api.py`) exposing asynchronous REST endpoints on port `8008`

---

## 3. Architecture & Integration Strategy

```
                                [ Browser Client ]
                          (React on http://localhost:5173)
                                        │
                         HTTP REST via Vite Proxy (/api)
                                        │
                                        ▼
                           [ FastAPI Backend Bridge ]
                         (api.py on http://0.0.0.0:8008)
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
  [ src.database.py ]          [ src.pipeline.py ]          [ src.review_service.py ]
   SQLite Persistence           Two-Tier Orchestrator        Human Oversight Actions
    (signalflow.db)              ┌───────────────┐           (Confirm, Reclassify,
                                 │ Decider 2B    │            Dismiss)
                                 │ System 1 (CPU)│
                                 └───────┬───────┘
                                         ▼
                                 ┌───────────────┐
                                 │ Gemini 3.5    │
                                 │ System 2      │
                                 └───────────────┘
```

### Zero-Touch Backend Invariance Guarantee
- **No changes** were made to existing classification algorithms, confidence calibrations, or prompt templates in `src/`.
- The FastAPI bridge (`api.py`) acts solely as a lightweight, thread-safe asynchronous gateway translating JSON requests directly into Python calls to `src.database`, `src.pipeline`, and `src.review_service`.
- The existing Streamlit interface (`app.py` on `http://localhost:8501`) remains completely functional and untouched.

---

## 4. Component Structure

```
frontend/src/
├── types/
│   └── index.ts                  # Shared TypeScript interfaces (Signal, KPIs, AppHealth, etc.)
├── lib/
│   └── api-client.ts             # Centralized typed HTTP client with error handling
├── components/
│   └── layout/
│       ├── TopMarketRibbon.tsx   # AlphaPro-style live macro market index ribbon
│       ├── Header.tsx            # VoiceWatch AI-style header with 4 integration status chips
│       └── Sidebar.tsx           # Collapsible navigation drawer with review badge counters
├── features/
│   ├── news/
│   │   └── NewsStreamPage.tsx    # SentimentIQ search, ticker summary, segmented bar, news cards & donut
│   ├── overview/
│   │   └── OverviewPage.tsx      # High-level KPIs, sentiment distributions, and cloud avoidance ratios
│   ├── analysis/
│   │   └── AnalysisPage.tsx      # Deep research dossiers separating facts vs transmission mechanisms
│   ├── review-queue/
│   │   └── ReviewQueuePage.tsx   # Interactive triage: Confirm & Send to Gemini, Reclassify, Dismiss
│   ├── performance/
│   │   └── PerformancePage.tsx   # Head-to-head model comparison cards, latencies, and benchmark runner
│   └── settings/
│       └── SettingsPage.tsx      # Runtime confidence thresholds, Gemini models, and RSS feed manager
├── test/
│   ├── setup.ts                  # Jest-dom testing matchers
│   └── app.test.tsx              # Automated Vitest component suite (6 tests)
├── App.tsx                       # Root orchestrator with auto-sync and error boundaries
├── main.tsx                      # Vite React entry point
└── index.css                     # Tailwind CSS directives, typography, and scrollbars
```

---

## 5. Development & Execution Commands

### Step 1: Start the Backend Bridge
In your Windows PowerShell terminal:
```powershell
Set-Location "c:\Users\Anush Ragav VS\OneDrive\Desktop\signalflow-ai"
.\.venv\Scripts\Activate.ps1
python -m uvicorn api:app --host 0.0.0.0 --port 8008
```

### Step 2: Start the React Frontend
In a second Windows PowerShell terminal:
```powershell
Set-Location "c:\Users\Anush Ragav VS\OneDrive\Desktop\signalflow-ai\frontend"
npm run dev
```
Open **[http://localhost:5173/](http://localhost:5173/)** in your browser.

### Step 3: Run Automated Frontend Tests
```powershell
Set-Location "c:\Users\Anush Ragav VS\OneDrive\Desktop\signalflow-ai\frontend"
npm test
```

### Step 4: Build Production Bundle
```powershell
npm run build
```
The optimized bundle is generated in `frontend/dist/`.
