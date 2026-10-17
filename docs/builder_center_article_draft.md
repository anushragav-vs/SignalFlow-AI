# Building SignalFlow AI: Two-Tier Financial Intelligence with Strands Decider 2B and Google Gemini
**Author:** First-Year AIML Student & SignalFlow AI Contributor  
**Hackathon:** AWS Agent Experience Hackathon featuring Strands Decider 2B  
**Tags:** `#strands-decider-2b` `#policy`

---

## 1. Introduction: The Financial News Deluge Problem

In algorithmic trading, institutional research, and market intelligence, speed and cost are existential constraints. Financial news wires pump out tens of thousands of headlines daily. Yet, quantitative analysis shows that **over 60% of daily headlines are non-material noise, routine consensus, or irrelevant gossip**.

A naive agent architecture pipes every incoming RSS headline directly into a frontier cloud LLM. In production, this causes two critical failures:
1. **Financial Waste**: Incurring commercial cloud token fees on headlines like *"Celebrity chef spotted in the Hamptons"* burns budget with zero ROI.
2. **Hallucination Risk**: Large generative LLMs are prone to fabricating market reactions or confidence scores when given ambiguous information.

To solve this, I designed and built **SignalFlow AI**: an open-source, two-tier financial intelligence pipeline that pairs a local System One decision engine (**Strands Decider 2B**) with a cloud System Two analysis model (**Google Gemini**).

---

## 2. System Architecture: System One Meets System Two

SignalFlow AI is inspired by cognitive dual-process theory:

- **System One (Local Edge Gatekeeper)**: Strands Decider 2B evaluates news headlines locally on standard Windows CPU hardware in ~950 ms. It outputs calibrated sentiment (`Bullish`, `Bearish`, `Neutral`, `Noise`) and an empirical confidence score from its pointer readout head.
- **Reusable Policy Engine**: A confidence-gated router inspects Decider 2B's outputs:
  - `Noise` & `Neutral`: Filtered locally with **0 ms cloud latency and $0.00 cloud cost**.
  - `Low Confidence (< 0.80)`: Intercepted in a persistent SQLite **Review Queue** for human oversight.
  - `High Conviction (&ge; 0.80)`: Dispatched to System Two.
- **System Two (Google Gemini Synthesis)**: Google Gemini generates structured institutional research dossiers separating reported facts, transmission mechanisms, affected assets, and key uncertainties.

---

## 3. Why Strands Decider 2B is the Ideal Gatekeeper

Strands Decider 2B is not another general-purpose conversational chatbot. It is purpose-built for high-speed, calibrated classification:
- **Calibrated Pointer Head**: Unlike softmax probabilities that suffer from overconfidence calibration drift, Decider 2B's readout head produces genuine calibrated confidence (`choice=0.863`).
- **Standard Hardware Compatibility**: Running half-precision weights upcast to `float32` allows AVX vector acceleration on standard consumer laptops with 16 GB RAM and no dedicated GPU.
- **Zero API Dependency**: Local edge execution guarantees that network outages or cloud API throttles never disrupt the initial classification stream.

---

## 4. The Reusable Policy Pattern

To make this project useful to the broader developer community, I encapsulated the decision logic into an independent, modular asset: [`reusable_patterns/financial_news_policy.py`](../reusable_patterns/financial_news_policy.py).

Any developer can adapt this pattern to other agent domains:
```python
from reusable_patterns.financial_news_policy import FinancialNewsPolicyGatekeeper

gatekeeper = FinancialNewsPolicyGatekeeper(min_confidence=0.80)
evaluation = gatekeeper.evaluate_headline("Tesla reports Q3 net income surges 17%...")

if evaluation.route == ActionRoute.APPROVE:
    # Dispatch to downstream LLM
elif evaluation.route == ActionRoute.REVIEW_QUEUE:
    # Escalate to human supervisor
```

---

## 5. Measured Experimental Results

On an 8-headline benchmark dataset representing real-world market distributions:
- **Cloud Calls Avoided**: **62.5%** of headlines were safely filtered locally.
- **Estimated Cloud Cost Reduction**: **62.5%** savings compared to sending all headlines to Gemini.
- **Local Decider Latency (CPU)**: Median of **968.8 ms**, p95 of **1,100.2 ms**.
- **Average Cloud Roundtrip**: **7,950 ms** (only paid when market conviction is high).

---

## 6. Lessons Learned & Failure Handling

As a first-year student, building SignalFlow AI taught me several crucial engineering lessons:
1. **Fail Safely**: Network timeouts and rate limits happen. Implementing bounded timeouts, automatic model availability checks, and graceful review queue routing prevents pipeline crashes.
2. **Preserve Ground Truth**: Never let human corrections overwrite model predictions in SQLite. Storing both allows continuous backtesting and model monitoring.
3. **Strict Fact Separation**: Generative models must be forced via JSON schema to separate verified source facts from analytical hypotheses.

---

## 7. Conclusion

SignalFlow AI proves that local System One models like Strands Decider 2B make cloud LLM agents exponentially cheaper, faster, and safer. The complete project is open-source under the MIT license and ready for community exploration.
