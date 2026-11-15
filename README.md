# SignalFlow AI — Real-Time Algorithmic Financial News Filter & Market Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![System One: Strands Decider 2B](https://img.shields.io/badge/System%20One-Strands%20Decider%202B-emerald.svg)](https://huggingface.co/StrandsAgents/strands-decider-2B-qwen3.5-v1-2610)
[![System Two: Google Gemini 3.5](https://img.shields.io/badge/System%20Two-Google%20AI%20Studio%20Gemini%203.5-teal.svg)](https://aistudio.google.com/)
[![Market Intelligence: Smart Tickers & Impact](https://img.shields.io/badge/Market%20Intelligence-Forex%20NLP%20%7C%20Impact%20Predictor-blue.svg)](src/ticker_detection/)
[![Frontend: React + Vite + Tailwind](https://img.shields.io/badge/Frontend-React%20%7C%20Vite%20%7C%20Tailwind-cyan.svg)](https://vitejs.dev/)
[![Tests: 79 Passed](https://img.shields.io/badge/Tests-79%20Passed%20(67%20Pytest%20%2B%2012%20Vitest)-brightgreen.svg)](tests/)

**GitHub Repository:** [https://github.com/anushragav-vs/SignalFlow-AI](https://github.com/anushragav-vs/SignalFlow-AI)  
**Core Tags:** `#strands-decider-2b` `#policy` `#google-gemini` `#fintech`

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

### 🌐 6. Smart Ticker Detection Engine (Forex NLP & Multi-Asset Registry)
- **Supported Universe**: Initially supports 12 institutional currency pairs and commodities: `EUR/USD`, `GBP/USD`, `USD/JPY`, `AUD/USD`, `USD/CAD`, `USD/CHF`, `NZD/USD`, `EUR/GBP`, `EUR/JPY`, `GBP/JPY`, `AUD/JPY`, and `XAU/USD` (Gold).
- **Externalized Entity Dictionary**: Centralized in `src/ticker_detection/entity_dictionary.json`, containing aliases, central banks (Federal Reserve, ECB, BoE, BoJ, RBA, BoC, SNB, RBNZ), economic indicators (CPI, PPI, GDP, NFP, Unemployment, PMI, Interest Rates), and commodities.
- **Hybrid Multi-Tier Extraction**:
  1. *Deterministic Matching*: Regex word-boundary scanning with canonical alias normalization (e.g., "Cable" -> GBP/USD, "Fiber" -> EUR/USD, "The Fed" -> Federal Reserve).
  2. *Macro Transmission Engine*: Maps central bank rate decisions and macroeconomic shocks into defensible currency pair impacts without assuming every pair is affected.
  3. *Selective Gemini Extraction*: Used when complex multi-clause geopolitical news requires deeper parsing; strictly whitelisted against the supported registry to reject fabricated ticker symbols (e.g. `XYZ/ABC`).
  4. *Relationship Taxonomy*: Strictly distinguishes between **DIRECT** (explicitly mentioned in text), **INDIRECT** (defensible macroeconomic transmission channel), and **POTENTIAL** (uncertain spillover).
  5. *Manual Correction Capability*: Analysts can inject manual overrides stored persistently for ongoing model calibration.

### ⚡ 7. Market Impact Predictor (6-Dimension Quantitative Scoring Engine)
- **4 Quantitative Impact Levels**: Configurable score boundaries:
  - `LOW` (0–24): Limited market relevance or routine consensus recaps.
  - `MEDIUM` (25–49): Moderate relevance to one or more currency pairs.
  - `HIGH` (50–74): Substantial potential volatility and institutional relevance.
  - `CRITICAL` (75–100): Exceptional event (e.g., emergency rate hike, bank collapse, geopolitical shock).
- **6-Dimension Normalized Architecture (0–100)**:
  - *Economic Importance* (25% weight): Systemic weight of the underlying event.
  - *Surprise Magnitude* (20% weight): Deviation relative to consensus expectations.
  - *Instrument Relevance* (20% weight): Directness of transmission to forex markets.
  - *Source Reliability* (10% weight): Publisher trust score (Reuters, Bloomberg, Fed, WSJ).
  - *News Novelty* (10% weight): Breaking event vs. routine follow-up recap.
  - *Potential Volatility* (15% weight): Expected dispersion and liquidity conditions.
- **Strict Directional Decoupling**: Impact score measures *magnitude and significance*, strictly separated from bullish/bearish direction. A critical event can be bullish, bearish, or directionally uncertain.
- **13 Macro Event Categories**: `central_bank_decisions`, `interest_rate_announcements`, `inflation_releases`, `employment_reports`, `gdp_releases`, `geopolitical_events`, `elections`, `trade_restrictions`, `financial_crises`, `banking_events`, `commodity_supply_disruptions`, `unexpected_economic_announcements`, `other_financial_events`.
- **Historical Context Windows & Zero Fabrication**: Supports evaluation windows (`15m`, `1h`, `4h`, `1d`) measuring realized return and volatility. When verified historical records do not exist, the engine explicitly outputs `historical_data_unavailable` with transparent rule-based labeling rather than hallucinating statistics.

### 🔔 8. Market Intelligence Alert Dispatcher & Rule Manager
- Real-time rule-based alerting engine triggered during news processing.
- Configurable rules: `critical_impact`, `high_impact`, `instrument_mention`, and `confidence_threshold`.
- In-app notification drawer with unread counter badge on the left navigation sidebar.
- 1-click alert triage and mark-as-read tracking.

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

The test suite validates Decider classification, policy thresholds, live RSS parsing, database schema migrations, Smart Ticker Detection, Market Impact scoring, alert dispatching, and Google Gemini integration:

```powershell
# Run the core Market Intelligence & NLP test suite (39 tests in ~2.8s)
.\.venv\Scripts\python.exe -m pytest tests/test_ticker_detection.py tests/test_market_impact.py tests/test_intelligence_pipeline.py tests/test_intelligence_api.py -v

# Run the complete backend test suite (67 unit & integration tests)
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

```powershell
# Run the frontend Vitest component test suite (12 tests)
cd frontend
npm test -- --run

# Run full frontend production build & TypeScript type checking
npm run build
```
*(All 67 backend pytest tests and 12 frontend Vitest component tests pass with 100% compliance)*

---

## 9. API Reference

### Core News, Market & Review Endpoints
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

### Market Intelligence, Smart Ticker & Impact Predictor Endpoints
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/intelligence/tickers` | `GET` | Supported currency pairs, entities, and instrument mention aggregation |
| `/api/intelligence/impact` | `GET` | Impact level distribution (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and dimension averages |
| `/api/intelligence/news/{article_id}` | `GET` | Full intelligence dossier: detected entities, affected instruments, 6 dimensions, and historical context |
| `/api/intelligence/instruments/{symbol}` | `GET` | Deep dive on a specific instrument: total mentions, direct/indirect breakdown, and correlated news |
| `/api/intelligence/alerts` | `GET` | Triggered alert notifications and active alert rules |
| `/api/intelligence/alerts/rules` | `POST` | Creates a new real-time alerting rule (`critical_impact`, `instrument_mention`, etc.) |
| `/api/intelligence/alerts/{alert_id}/read` | `POST` | Marks an alert notification as read |
| `/api/intelligence/analyze/{article_id}` | `POST` | Re-evaluates an existing article through Ticker Detection & Impact Predictor |
| `/api/intelligence/statistics` | `GET` | Overall aggregate intelligence metrics: average score, top events, and alert counts |

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
│   ├── rss_service.py          # Real-time RSS feed ingestion & deduplication
│   ├── ticker_detection/       # FEATURE A: Smart Ticker Detection
│   │   ├── __init__.py
│   │   ├── registry.py         # Supported Forex & commodity universe with validation
│   │   ├── entity_dictionary.json # Externalized maintainable aliases & entities
│   │   ├── models.py           # Typed Pydantic schemas (Entities, Instruments)
│   │   ├── matcher.py          # Deterministic regex entity extractor
│   │   ├── relationship_engine.py # DIRECT, INDIRECT, POTENTIAL transmission mapping
│   │   ├── gemini_extractor.py # Whitelisted Gemini-assisted extraction
│   │   └── detector.py         # Master SmartTickerDetector service
│   ├── market_impact/          # FEATURE B: Market Impact Predictor
│   │   ├── __init__.py
│   │   ├── models.py           # Typed Pydantic schemas (ImpactDimensions, HistoricalContext)
│   │   ├── event_classifier.py # 13 macroeconomic event taxonomies
│   │   ├── scoring.py          # 6-dimension weighted engine (LOW, MED, HIGH, CRIT)
│   │   ├── historical_context.py # Realized returns (15m, 1h, 4h, 1d) & zero-fabrication
│   │   └── predictor.py        # Master MarketImpactPredictor engine
│   └── alerts/                 # Real-time Market Intelligence Alerts
│       ├── __init__.py
│       ├── models.py           # Alert & Rule data models
│       └── alert_engine.py     # Rule evaluation & notification dispatcher
├── frontend/                   # React + Vite + Tailwind + TypeScript Application
│   ├── index.html              # HTML shell with Inter & JetBrains Mono typography
│   ├── package.json            # Node dependencies (React 19, Lucide, Recharts, Vite)
│   ├── src/
│   │   ├── App.tsx             # Root workspace layout & state orchestration
│   │   ├── types/index.ts      # TypeScript definitions for signals, tickers, intelligence, and KPIs
│   │   ├── lib/api-client.ts   # Typed API client for FastAPI backend
│   │   ├── components/
│   │   │   ├── layout/         # Header, Sidebar (with Radar alert badge), and TopMarketRibbon
│   │   │   └── market/         # StockDetailModal with live charts & correlation
│   │   └── features/
│   │       ├── news/           # NewsStreamPage with custom analyzer & dossier view
│   │       ├── intelligence/   # React Market Intelligence Suite
│   │       │   ├── MarketIntelligencePage.tsx # Master page with macro KPI bar & subtabs
│   │       │   ├── SmartTickerDetectionPanel.tsx # Forex pair filters, badges & confidence slider
│   │       │   ├── MarketImpactPanel.tsx # 6 dimension bars, level filters & distribution pie
│   │       │   ├── NewsDetailModal.tsx # Full drill-down modal with transmission rationales
│   │       │   └── AlertsManagerModal.tsx # Real-time notification drawer & rule builder
│   │       ├── overview/       # KPIs, avoided cost metrics, and activity timeline
│   │       ├── analysis/       # Dedicated Gemini research dossiers view
│   │       ├── review-queue/   # Human-in-the-loop review queue interface
│   │       ├── performance/    # Latency distributions and cost benchmark cards
│   │       └── settings/       # Policy thresholds, model selection, and feed manager
├── tests/                      # Automated test suite (67 Pytest tests + 12 Vitest tests)
│   ├── test_ticker_detection.py# Smart ticker detection, aliases, and direct/indirect tests (17 tests)
│   ├── test_market_impact.py   # 6-dimension scoring, 13 events, and decoupling tests (9 tests)
│   ├── test_intelligence_pipeline.py # End-to-end pipeline intelligence integration (2 tests)
│   ├── test_intelligence_api.py# FastAPI intelligence REST endpoints (11 tests)
│   ├── test_classification.py  # Decider classification & threshold tests
│   ├── test_database.py        # SQLite persistence & audit preservation tests
│   ├── test_gemini.py          # Gemini mock, timeout & error tests
│   ├── test_live_integration.py# Live Google Gemini & Decider endpoint tests
│   ├── test_metrics.py         # Cost & latency formula validation tests
│   ├── test_pipeline.py        # End-to-end pipeline tests
│   ├── test_rss.py             # RSS normalization & deduplication tests
│   └── frontend/src/test/      # Vitest React component test suite (12 tests)
├── reusable_patterns/          # Independent policy pattern asset
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
