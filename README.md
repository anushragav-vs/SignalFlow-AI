# SignalFlow AI — Real-Time Algorithmic Financial News Filter & Market Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![System One: Strands Decider 2B](https://img.shields.io/badge/System%20One-Strands%20Decider%202B-emerald.svg)](https://huggingface.co/StrandsAgents/strands-decider-2B-qwen3.5-v1-2610)
[![System Two: Google Gemini 3.5](https://img.shields.io/badge/System%20Two-Google%20AI%20Studio%20Gemini%203.5-teal.svg)](https://aistudio.google.com/)
[![SDK: google-genai](https://img.shields.io/badge/SDK-google--genai%20v2.31+-purple.svg)](https://pypi.org/project/google-genai/)
[![Frontend: React + Vite + Tailwind](https://img.shields.io/badge/Frontend-React%20%7C%20Vite%20%7C%20Tailwind-cyan.svg)](https://vitejs.dev/)
[![Tests: 29 Passed](https://img.shields.io/badge/Tests-29%20Passed%20(Pytest)-brightgreen.svg)](tests/)

**GitHub Repository:** [https://github.com/anushragav-vs/SignalFlow-AI](https://github.com/anushragav-vs/SignalFlow-AI)  
**Hackathon Tags:** `#strands-decider-2b` `#policy` `#google-gemini` `#fintech`

---

> ### ⚖️ Educational & Regulatory Disclaimer
> **Research and educational purposes only. This is not financial advice or an automated trading system.**  
> SignalFlow AI does not place live orders, execute financial trades, or guarantee predictive investment returns. All classifications and generated dossiers represent automated AI inferences for educational research.

---

## 1. Executive Summary & Problem Statement

Financial news wires generate thousands of raw headlines per minute across global exchanges. However, **over 60% of financial news stream volume consists of routine consensus observations, duplicate reports, or non-actionable lifestyle noise**.

Piping every incoming headline directly into a commercial cloud LLM causes two severe production failures:
1. **Financial & Compute Waste**: Paying commercial token fees to analyze irrelevant noise like *"Celebrity chef spotted in the Hamptons"* burns budget with zero ROI.
2. **Hallucination & Risk**: Generative LLMs without calibrated confidence scores fabricate certainty, making them unsafe for high-stakes decision routing.

**SignalFlow AI** solves this by implementing a **two-tier cognitive architecture**:
- **System One (Local Edge Gatekeeper)**: [Strands Decider 2B](https://huggingface.co/StrandsAgents/strands-decider-2B-qwen3.5-v1-2610) classifies market sentiment into `[Bullish, Bearish, Neutral, Noise]` on standard CPU hardware with calibrated confidence scores in ~950 ms with **$0.00 API cost**.
- **Confidence-Aware Policy Pattern**: Blocks `Noise` and `Neutral` locally, escalates low-confidence items (< 0.80) to a persistent **Human Review Queue**, and routes only high-conviction signals to cloud synthesis.
- **System Two (Cloud Deep Research)**: [Google AI Studio's Gemini 3.5 API](https://aistudio.google.com/) synthesizes an **8-factor institutional research dossier** strictly separating reported facts, transmission channels, analytical hypotheses, catalyst watchpoints, impact horizons, institutional risk levels, and peer sensitivities.
- **Live Market Data & Stock Correlation Engine**: Real-time ticker ribbon, 5-day sparklines, key statistics, volume, and interactive stock modal that connects live price movements directly with correlated AI research dossiers.

---

## 2. Two-Tier System Architecture

```text
                                +-----------------------------------------------+
                                | Live Multi-Stream News & RSS Ingestion        |
                                | (Yahoo Finance, CNBC, MarketWatch, WSJ, User) |
                                +-----------------------+-----------------------+
                                                        |
                                                        v
                                +-----------------------------------------------+
                                | Normalization & SHA-256 State Deduplication   |
                                +-----------------------+-----------------------+
                                                        |
                                                        v
                                +-----------------------------------------------+
                                | SYSTEM ONE: Strands Decider 2B (Local Edge)   |
                                | - Typed ChoiceQuestion classifier             |
                                | - Calibrated pointer readout head (24 slots)  |
                                | - Latency: ~950 ms | Edge Cost: $0.00         |
                                +-----------------------+-----------------------+
                                                        |
                                                        v
                                +-----------------------------------------------+
                                | POLICY GATEKEEPER & ROUTING ENGINE            |
                                +-----------------------+-----------------------+
                                                        |
               +----------------------------------------+----------------------------------------+
               |                                        |                                        |
               v                                        v                                        v
     +-------------------+                    +--------------------+                   +--------------------+
     | Noise / Neutral   |                    | Low-Confidence     |                   | High-Conviction    |
     | Headlines         |                    | (< 0.80 threshold) |                   | Bullish / Bearish  |
     +---------+---------+                    +----------+---------+                   +----------+---------+
               |                                        |                                         |
               v                                        v                                         v
     +-------------------+                    +--------------------+                   +--------------------+
     | LOCAL DROP / SKIP |                    | HUMAN REVIEW QUEUE |  Human Approval   | SYSTEM TWO:        |
     | 0 ms Cloud Time   |                    | (SQLite Audit DB)  | ----------------> | Google Gemini 3.5  |
     | $0.00 Cloud Cost  |                    | (Confirm/Reclassify|                   | (google-genai SDK) |
     +-------------------+                    +--------------------+                   +----------+---------+
                                                                                                  |
                                                                                                  v
                                                                                       +--------------------+
                                                                                       | 8-FACTOR DOSSIER   |
                                                                                       | • Verified Facts   |
                                                                                       | • Transmission     |
                                                                                       | • Hypotheses       |
                                                                                       | • Catalyst Watch   |
                                                                                       | • Impact Horizon   |
                                                                                       | • Risk Level       |
                                                                                       | • Peer Sensitivity |
                                                                                       | • Downside Risks   |
                                                                                       +--------------------+
```

---

## 3. Core Capabilities & Key Features

### 📡 1. Live Market Ticker & Interactive Stock Modals
- **Real-Time Ribbon**: Live quotes for major indices and assets (`NASDAQ`, `S&P 500`, `DOW JONES`, `NVDA`, `TSLA`, `AAPL`, `MSFT`, `CRUDE OIL`) via Yahoo Finance API.
- **Stock Detail Modal**: Clicking any stock ticker across the ribbon or news cards opens a comprehensive market view:
  - Live price, day dollar/percentage change, previous close, and exchange.
  - Interactive **5-day SVG sparkline** trend.
  - Day range, 52-week range, and trading volume.
  - Calibrated **Market Sentiment Index (0-100)** computed from processed news ledger records.
  - Correlated news signals and deep research dossiers matching that symbol.
  - 1-click **"Filter News Stream to this Ticker"** navigation.

### 🔬 2. Deep Institutional Research Breakdown (8-Factor Dossier)
High-conviction headlines approved by the policy gatekeeper are synthesized into institutional-grade research:
1. **Reported Facts (Source Verifiable)**: Objective, source-derived empirical statements.
2. **Economic Transmission Mechanism**: Exact financial transmission channel (cost of capital, discount rates, gross margin compression, enterprise capex).
3. **Forward-Looking Analytical Hypotheses**: Institutional hypotheses on multi-week price absorption and analyst revisions.
4. **Directional Implications & Impact Horizon**: Explicit directional bias (`Bullish` / `Bearish`) with timeframe (`Tactical (1-4 weeks)`, `Intraday`, `Multi-Quarter`).
5. **Affected Asset Classes & Key Tickers**: Interactive chips linking directly to live market quotes.
6. **Upcoming Catalyst Watchpoints**: Specific forward calendar events to monitor (e.g. *TSMC Monthly Revenue*, *FOMC Minutes*, *Q4 Earnings Guidance*).
7. **Peer & Supply Chain Sensitivity**: Cross-impact mapping to key competitors, foundry partners, and enterprise customers.
8. **Invalidation Risks & Scenarios**: Specific downside conditions that would invalidate the investment thesis.

### ⚡ 3. Custom Financial Headline Analyzer
- Real-time sandbox allowing analysts to input custom headlines or select from 4 quick presets (Bullish Growth, Bearish Slump, Fed Rate Decision, Lifestyle Noise).
- Instant Decider 2B edge evaluation with calibrated confidence percentage and policy routing decision.
- Immediate Google Gemini deep synthesis dossier generation on approved headlines.

### 🛡️ 4. Human Review Queue & Audit Ledger
- Low-confidence signals (< 0.80) are quarantined in the review queue.
- Human reviewers can **Confirm** (escalate to Gemini), **Reclassify** (correct label with audit notes), or **Dismiss**.
- Immutable SQLite audit ledger preserves original decider classifications while recording reviewer actions and timestamps.

### 📊 5. SentimentIQ Analytics & Donut Visualization
- Real-time sentiment distribution donut chart with center bullish percentage.
- Segmented multi-color progress bars tracking positive, neutral, and negative market bias.
- Search filter across headlines, publishers, and tickers with instantaneous category filtering.

---

## 4. Hardware & Benchmark Performance

Evaluated on the benchmark dataset ([`data/sample_headlines.json`](data/sample_headlines.json)) on Windows 11 CPU (16 GB RAM):

| Performance Metric | Baseline (100% Cloud) | SignalFlow AI (Decider Gatekeeper) | Impact / Savings |
|---|---|---|---|
| **Headlines Evaluated** | 8 | 8 | Identical dataset |
| **Cloud LLM Invocations** | 8 | 3 | **62.5% Cloud Calls Avoided** |
| **Locally Filtered (Noise/Neutral)** | 0 | 4 | **50.0% filtered at $0.00** |
| **Escalated to Review Queue** | 0 | 1 | **12.5% quarantined for safety** |
| **Decider Median Latency (CPU)** | N/A | **968.8 ms** | Local edge speed |
| **Decider p95 Latency (CPU)** | N/A | **1,100.2 ms** | Deterministic inference |
| **Estimated Cloud Spend** | $0.000680 | **$0.000255** | **62.5% Dollar Cost Reduction** |

*All metrics are calculated strictly from recorded execution instances using monotonic clocks and official token metadata (`time.perf_counter()`, `response.usage_metadata`). Zero fabricated metrics.*

---

## 5. Technology Stack

### Backend & AI Pipeline
- **Python 3.10+**
- **Strands Decider 2B** (`StrandsAgents/strands-decider-2B-qwen3.5-v1-2610`): ChoiceQuestion classification with calibrated pointer readout head.
- **PyTorch & Hugging Face Transformers**: AVX-accelerated CPU inference with float32 upcasting.
- **Google Gen AI SDK** (`google-genai`): Official SDK for Google AI Studio Gemini 3.5 synthesis.
- **FastAPI & Uvicorn**: High-throughput REST API with CORS and JSON serialization.
- **SQLite**: Zero-maintenance, persistent relational audit ledger with schema migrations.
- **Feedparser & Requests**: Live multi-feed RSS ingestion with timeout resilience.

### Frontend Dashboard
- **React 19 & TypeScript**: Component-driven architecture with strict type safety.
- **Vite**: Sub-second Hot Module Replacement (HMR) and optimized rollup bundling.
- **Vanilla CSS & Tailwind CSS**: Custom dark navy fintech aesthetic (`#060b15`) with glassmorphism and cyan glows.
- **Recharts**: Responsive sentiment donut charts and distribution bars.
- **Lucide React**: Modern financial and system iconography.

---

## 6. Installation & Quick Start

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm
- Free [Google AI Studio API Key](https://aistudio.google.com/app/apikey)

### 1. Clone the Repository
```bash
git clone https://github.com/anushragav-vs/SignalFlow-AI.git
cd SignalFlow-AI
```

### 2. Configure Python Virtual Environment
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Copy environment template
Copy-Item .env.example .env
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

### 3. Add Google AI Studio API Key
Open `.env` and set your key:
```ini
GEMINI_API_KEY=your_actual_google_ai_studio_api_key_here
GEMINI_MODEL_ID=gemini-3.5-flash-lite
MIN_CONFIDENCE_THRESHOLD=0.80
```

### 4. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 7. Running the Application

### Option A: Launch the Full Modern Web Platform (Recommended)

**Terminal 1 — FastAPI Backend:**
```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 0.0.0.0 --port 8008
```

**Terminal 2 — React/Vite Frontend:**
```powershell
cd frontend
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

### Option B: Launch the Interactive Streamlit Dashboard
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

### Option C: Run the Command-Line Demonstration
```powershell
python demo.py gemini-3.5-flash-lite
```

---

## 8. Automated Testing & Verification

The test suite validates Decider classification, policy thresholds, live RSS parsing, database schema migrations, and Google Gemini integration:

```powershell
# Run all 29 backend pytest tests
pytest tests/ -v
```
*(All 29 tests pass with 100% compliance)*

```powershell
# Run frontend build & type check
cd frontend
npm run build
```

---

## 9. API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check, model status, and database connectivity |
| `/api/kpis` | `GET` | System-wide statistics, spend, latency, and avoided cloud calls |
| `/api/signals` | `GET` | Paginated SQLite signals with search, sentiment, and policy filters |
| `/api/news/fetch` | `POST` | Ingests live RSS feeds, deduplicates, and evaluates batch signals |
| `/api/news/evaluate-manual` | `POST` | Evaluates a custom financial headline through Decider 2B and Gemini |
| `/api/market/tickers` | `GET` | Real-time quotes, changes, and sparklines for top indices & assets |
| `/api/market/quote/{symbol}` | `GET` | Live quote, 5-day sparkline, volume, sentiment score, and correlated news |
| `/api/review-queue` | `GET` | Quarantined low-confidence signals awaiting human review |
| `/api/review-queue/{id}/confirm` | `POST` | Approves quarantined signal and triggers Gemini deep research |
| `/api/review-queue/{id}/reclassify`| `POST` | Corrects label with reviewer notes while preserving original inference |
| `/api/review-queue/{id}/dismiss` | `POST` | Dismisses signal from review queue with audit trail |
| `/api/benchmarks/run` | `POST` | Executes automated benchmark comparing Decider gatekeeper vs baseline |

---

## 10. Reusable Policy Pattern Asset

Other developers can integrate our confidence-gated policy router into their own agents:
- File: [`reusable_patterns/financial_news_policy.py`](reusable_patterns/financial_news_policy.py)
- Documentation: [`reusable_patterns/README.md`](reusable_patterns/README.md)

Minimal runnable example:
```python
from reusable_patterns.financial_news_policy import FinancialNewsPolicyGatekeeper, ActionRoute

gatekeeper = FinancialNewsPolicyGatekeeper(min_confidence=0.80)
evaluation = gatekeeper.evaluate_headline("Tesla reports Q3 net income surges 17%...")

if evaluation.route == ActionRoute.APPROVE:
    print(f"Approved for downstream LLM synthesis: {evaluation.selected_choice}")
elif evaluation.route == ActionRoute.REVIEW_QUEUE:
    print("Held in review queue for human verification.")
```

---

## 11. Project Directory Layout

```text
signalflow-ai/
├── api.py                      # FastAPI REST API backend bridge
├── app.py                      # Interactive Streamlit fintech dashboard
├── config.py                   # Centralized typed configuration
├── demo.py                     # CLI demonstration pipeline script
├── requirements.txt            # Production Python dependencies
├── LICENSE                     # MIT Open-Source License
├── README.md                   # Complete architectural and execution guide
├── .gitignore                  # Enforces secret, database, and node_modules exclusion
├── .env.example                # Safe environment variables template
├── src/                        # Modular backend services
│   ├── __init__.py
│   ├── classification_service.py # Policy routing & confidence thresholds
│   ├── database.py             # SQLite audit trail & schema migrations
│   ├── decider_client.py       # Strands Decider 2B HTTP & in-process client
│   ├── gemini_service.py       # Google Gen AI SDK client & structured analysis
│   ├── market_service.py       # Live market quotes, sparklines & ticker resolution
│   ├── metrics.py              # Latency distributions & cost formulas
│   ├── pipeline.py             # End-to-end signal orchestration & batch evaluation
│   ├── review_service.py       # Human-in-the-loop review queue management
│   └── rss_service.py          # Real-time RSS feed ingestion & deduplication
├── frontend/                   # React + Vite + Tailwind + TypeScript Application
│   ├── index.html              # HTML shell with Inter & JetBrains Mono typography
│   ├── package.json            # Node dependencies (React 19, Lucide, Recharts, Vite)
│   ├── src/
│   │   ├── App.tsx             # Root workspace layout & state orchestration
│   │   ├── types/index.ts      # TypeScript definitions for signals, tickers, and KPIs
│   │   ├── lib/api-client.ts   # Typed API client for FastAPI backend
│   │   ├── components/
│   │   │   ├── layout/         # Header, Sidebar, and TopMarketRibbon
│   │   │   └── market/         # StockDetailModal with live charts & correlation
│   │   └── features/
│   │       ├── news/           # NewsStreamPage with custom analyzer & dossier view
│   │       ├── overview/       # KPIs, avoided cost metrics, and activity timeline
│   │       ├── analysis/       # Dedicated Gemini research dossiers view
│   │       ├── review-queue/   # Human-in-the-loop review queue interface
│   │       ├── performance/    # Latency distributions and cost benchmark cards
│   │       └── settings/       # Policy thresholds, model selection, and feed manager
├── tests/                      # Automated test suite (29 Pytest tests)
│   ├── test_classification.py  # Decider classification & threshold tests
│   ├── test_database.py        # SQLite persistence & audit preservation tests
│   ├── test_gemini.py          # Gemini mock, timeout & error tests
│   ├── test_live_integration.py# Live Google Gemini & Decider endpoint tests
│   ├── test_metrics.py         # Cost & latency formula validation tests
│   ├── test_pipeline.py        # End-to-end pipeline tests
│   └── test_rss.py             # RSS normalization & deduplication tests
├── reusable_patterns/          # Independent hackathon pattern asset
│   ├── financial_news_policy.py# Standalone reusable policy router
│   └── README.md               # Pattern documentation & integration guide
└── data/                       # Ground-truth datasets & fixtures
    ├── sample_headlines.json   # 8 labeled test headlines covering all classes
    └── sample_headlines.py     # Benchmark dataset loading helper
```

---

## 12. License & Author

Distributed under the [MIT License](LICENSE).  
Developed by **[Anush Ragav V S](https://github.com/anushragav-vs)**.
