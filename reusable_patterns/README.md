# Reusable Pattern: Calibrated Multi-Class Policy Gatekeeper
**Hackathon Tags:** `#strands-decider-2b` `#policy`

## Overview
This asset provides an independent, production-grade implementation of a **confidence-gated decision policy** powered by **Strands Decider 2B**. It acts as a lightweight System One filter that intercepts high-velocity inputs, evaluates their sentiment and calibrated confidence, and gates downstream actions.

## Pattern Architecture

```text
Incoming Input (Headline / Event / Alert)
                    │
                    ▼
  Strands Decider 2B Choice Evaluation
  Options: [Bullish, Bearish, Neutral, Noise]
                    │
                    ▼
     Calibrated Confidence Evaluation
  (Extracted from calibrated readout head)
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
  Noise /      Confidence <    High Conviction
  Neutral       Threshold      Bullish / Bearish
      │             │             │
      ▼             ▼             ▼
  BLOCK_ROUTE   REVIEW_QUEUE   APPROVE_ROUTE
  (0 ms cloud   (Escalate to   (Forward to
   latency)     human review)   downstream LLM)
```

## How It Works

1. **Typed Choice Question**:
   The engine passes a structured `ChoiceQuestion` specification:
   ```python
   ChoiceQuestion(
       instructions="What is the primary market-impact category of this financial headline? ...",
       criteria={"Bullish": "", "Bearish": "", "Neutral": "", "Noise": ""}
   )
   ```
2. **Confidence Interpretation**:
   Strands Decider 2B features a calibrated pointer readout head (`choice=0.863`). Confidence reflects the model's calibrated probabilistic certainty, distinct from a standard soft-max argmax.
3. **Audit-Compliant Routing**:
   - `Noise`: Dropped locally. Zero downstream compute cost.
   - `Neutral`: Logged locally. Skips deep cloud synthesis.
   - `Low Confidence (< 0.80)`: Intercepted in a persistent review queue for human verification.
   - `High Conviction (&ge; 0.80)`: Approved for execution or cloud synthesis.

## How to Adapt to Another Domain

To reuse this pattern in another domain (e.g., IT incident routing, medical triage, customer support priority):

1. **Modify the Question & Options**:
   Update `instructions` and `criteria` in `financial_news_policy.py`:
   ```python
   # Example: IT Incident Triage
   INCIDENT_QUESTION = "What is the severity of this system alert?"
   ALLOWED_CHOICES = ["Critical", "Warning", "Informational", "FalseAlarm"]
   ```
2. **Tune the Confidence Threshold**:
   Set `min_confidence` according to your domain's risk tolerance:
   ```python
   gatekeeper = FinancialNewsPolicyGatekeeper(min_confidence=0.85)
   ```
3. **Execute**:
   ```powershell
   python reusable_patterns/financial_news_policy.py
   ```
