# SignalFlow AI - Architectural Specification
**Core Tags:** `#strands-decider-2b` `#policy` `#google-gemini` `#fintech`

## 1. System Overview

SignalFlow AI is a high-throughput, cost-optimized algorithmic financial news intelligence system. It couples a local calibrated System One decision model (**Strands Decider 2B**) with a cloud-based generative analysis model (**Google Gemini**) via a deterministic, confidence-aware policy pattern.

```text
                               +----------------------------------------+
                               | Financial News Ingestion               |
                               | (Yahoo Finance, CNBC, MarketWatch, RSS)|
                               +-------------------+--------------------+
                                                   |
                                                   v
                         +----------------------------------------------------+
                         | Normalization & Canonical URL Deduplication        |
                         | (SHA-256 state hashing)                            |
                         +-------------------------+--------------------------+
                                                   |
                                                   v
                         +----------------------------------------------------+
                         | SYSTEM ONE: Strands Decider 2B (Local CPU)         |
                         | - Pointer readout head calibrated confidence       |
                         | - Options: [Bullish, Bearish, Neutral, Noise]      |
                         | - Model: StrandsAgents/strands-decider-2B-qwen3.5  |
                         | - Local latency: ~950 ms | Cost: $0.00             |
                         +-------------------------+--------------------------+
                                                   |
                                                   v
                         +----------------------------------------------------+
                         | REUSABLE POLICY GATEKEEPER & ROUTING ENGINE        |
                         +-------------------------+--------------------------+
                                                   |
         +-----------------------------------------+-----------------------------------------+
         |                                         |                                         |
         v                                         v                                         v
+------------------+                     +-------------------+                     +-------------------+
| Noise / Neutral  |                     | Low-Confidence    |                     | High-Conviction   |
| Headlines        |                     | (< 0.80 threshold)|                     | Bullish / Bearish |
+--------+---------+                     +---------+---------+                     +---------+---------+
         |                                         |                                         |
         v                                         v                                         v
+------------------+                     +-------------------+                     +-------------------+
| LOCAL DROP/SKIP  |                     | HUMAN REVIEW      |   Human Approval    | SYSTEM TWO:       |
| 0 ms Cloud Time  |                     | QUEUE (SQLite)    | ------------------> | Google Gemini API |
| $0.00 Cloud Cost |                     | (Review / Reject) |                     | (google-genai)    |
+------------------+                     +-------------------+                     +---------+---------+
                                                                                             |
                                                                                             v
                                                                                   +-------------------+
                                                                                   | Structured Dossier|
                                                                                   | - Event Summary   |
                                                                                   | - Transmission    |
                                                                                   | - Affected Assets |
                                                                                   | - Facts vs Hypoth.|
                                                                                   | - Uncertainties   |
                                                                                   +-------------------+
```

---

## 2. Why Strands Decider 2B?

Conventional approaches feed every raw news headline directly to commercial cloud LLMs (such as GPT-4, Claude, or Gemini Pro). In financial markets, this architecture fails for three reasons:
1. **Financial Noise Volume**: Over 70% of financial news stream volume consists of routine consensus observations, duplicate wire reports, or irrelevant celebrity/lifestyle commentary. Cloud inference on noise incurs unsustainable API expenses.
2. **Deterministic Confidence**: Standard autoregressive LLMs generate text token-by-token and do not output calibrated probabilities. Strands Decider 2B features a dedicated pointer readout head (`head.safetensors`, 768 dim, 24 slots) providing true calibrated confidence scores (`choice=0.863`).
3. **Local Edge Sovereignty**: Decider 2B runs locally on standard CPU hardware with half-precision weights upcast to `float32` by `SystemOneEngine._upcast_torso_for_cpu()` to utilize AVX vector instructions. It incurs zero external API dependencies or costs.

---

## 3. Two-Tier Workflow Breakdown

### Tier 1: System One Gatekeeper
- **Checkpoint**: `StrandsAgents/strands-decider-2B-qwen3.5-v1-2610`
- **Question**:
  > *"What is the primary market-impact category of this financial headline? Consider whether the headline contains material, specific information that could affect an identifiable financial asset or market. Distinguish positive market implications, negative market implications, genuinely neutral financial information, and irrelevant or non-actionable noise."*
- **Choice Classes**: `Bullish`, `Bearish`, `Neutral`, `Noise`
- **Decision Extraction**: Extracts `choice`, calibrated `confidence`, full class `probabilities`, and `latency_ms`.

### Tier 2: Policy Routing Engine
The policy router evaluates the classification and confidence:
- **`Noise`**: Cloud analysis blocked. 100% cloud cost reduction.
- **`Neutral`**: Cloud analysis blocked. Consensus news stored locally.
- **`Bullish` / `Bearish` (Confidence &ge; 0.80)**: High conviction approved for deep synthesis.
- **`Bullish` / `Bearish` (Confidence < 0.80)**: Routed to SQLite **Review Queue** for human oversight.
- **Service Failure / Invalid Confidence**: Fails safely to the Review Queue.

### Tier 3: System Two Generative Analysis
- **Provider**: Google AI Studio Gemini API using the official `google-genai` Python SDK.
- **Recommended Model**: `gemini-3.5-flash-lite` (or `gemini-3.8-flash`).
- **Structured Schema**:
  1. `event_summary`: Core verified market event.
  2. `transmission_mechanism`: Asset pricing catalyst channel.
  3. `affected_assets`: List of equities, sectors, and commodity instruments.
  4. `directional_implications`: Bullish, bearish, mixed, or uncertain.
  5. `uncertainties_and_risks`: Key watchpoints and missing data.
  6. `reported_facts`: Objective facts explicitly reported.
  7. `analytical_hypotheses`: Forward-looking analytical inferences.

---

## 4. SQLite Audit & Persistence Model

SignalFlow AI enforces a strict audit rule: **User corrections must never overwrite the original model classification.** Both the initial Decider 2B prediction and subsequent human review actions are permanently recorded:

| Field | Description |
|---|---|
| `decider_sentiment` | Original model output (`Bullish`, `Bearish`, `Neutral`, `Noise`) |
| `decider_confidence` | Calibrated confidence score (0.000 to 1.000) |
| `policy_action` | Action evaluated by policy (`APPROVE`, `BLOCK_NOISE`, `BLOCK_NEUTRAL`, `REVIEW_QUEUE`) |
| `review_status` | Current review state (`NONE`, `PENDING`, `CONFIRMED`, `RECLASSIFIED`, `DISMISSED`) |
| `corrected_label` | Human-assigned label if reclassified (preserves `decider_sentiment`) |
| `gemini_status` | Cloud API execution status (`success`, `skipped_by_policy`, `queued_for_review`, `error_*`) |
| `cloud_latency_ms` | Actual measured round-trip API time |
| `input_tokens` / `output_tokens` | Real token counts from `response.usage_metadata` |
| `estimated_cost_usd` | Exact dollar cost computed from official token rates |
