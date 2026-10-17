# SignalFlow AI - Video Demonstration Script
**Target Duration:** Under 2 minutes 45 seconds (2:30 planned)
**Hackathon Tags:** `#strands-decider-2b` `#policy`

---

## Video Timeline & Script

| Timestamp | Visual Screen | Voiceover / Action | Key Point Demonstrated |
|---|---|---|---|
| **0:00 - 0:25** | Terminal showing `streamlit run app.py` and Dashboard Home Page | "Welcome to SignalFlow AI, a real-time financial news intelligence pipeline built for the AWS Agent Experience Hackathon featuring Strands Decider 2B. Modern financial markets generate thousands of headlines per minute. Sending all of them to cloud LLMs wastes money on noise. SignalFlow AI solves this with a two-tier architecture." | Problem statement & Hackathon intro |
| **0:25 - 0:55** | Live Pipeline Tab in Streamlit; Ingest RSS headlines button clicked | "Here in our Live Pipeline tab, we ingest live market news from Yahoo Finance, CNBC, and MarketWatch. Watch what happens: Strands Decider 2B evaluates each headline on CPU in under 1 second. For example, 'Tesla Q3 net income surges 17%' is classified as Bullish with 96.1% calibrated confidence. Because confidence exceeds our 80% policy threshold, it's approved for cloud synthesis." | Strands Decider 2B decision & calibrated confidence score |
| **0:55 - 1:25** | Live Pipeline Table showing Noise and Neutral badges | "Now look at the next headlines. An article about a celebrity chef is classified as 'Noise' with 44% confidence. Our policy gatekeeper drops it locally. Notice the cloud latency is 0.0 milliseconds and cloud cost is exactly zero dollars. Similarly, routine Federal Reserve consensus is classified as 'Neutral' and skipped. We just filtered over 60% of our news volume locally!" | Locally filtered headline (Noise/Neutral, 0 ms cloud latency, $0.00 cost) |
| **1:25 - 1:55** | Human Review Queue Tab | "What about uncertain headlines? Here's an ambiguous takeover rumor classified as Bullish, but with only 52% confidence. Instead of hallucinating in the cloud, our policy intercepts it in the Human Review Queue. As an analyst, I can inspect the headline, review Decider's probability distribution, and click 'Confirm & Send to Gemini' or 'Reject'." | Low-confidence review case & human oversight |
| **1:55 - 2:20** | Structured Research Cards Tab | "For approved signals, Google Gemini synthesizes a structured institutional dossier. Notice how our schema strictly separates verified Reported Facts, financial Transmission Mechanisms, Affected Asset Classes like TSLA and consumer discretionary ETFs, and forward-looking Uncertainties and Risks. Facts and analytical hypotheses are never confused." | Google Gemini structured analysis & financial boundaries |
| **2:20 - 2:45** | Analytics Tab with KPI metrics and Cost Tracker | "Finally, our Analytics tab shows real, measured results: over 62% of cloud calls avoided, sub-second Decider p95 latency on standard Windows CPU hardware, and cumulative spend of fractions of a cent. Plus, our decision logic is packaged as a reusable policy module for other developers. Thank you for watching SignalFlow AI!" | Real measured metrics, reusable pattern, conclusion |

---

## Demonstration Checklist

1. [ ] Have `.env` configured with your `GEMINI_API_KEY`.
2. [ ] Run `streamlit run app.py`.
3. [ ] Click **"🚀 Ingest & Process Signals"** on Tab 1.
4. [ ] Point out the Bullish (96%), Noise (44%), and Neutral (78%) badges.
5. [ ] Switch to Tab 2 (**Review Queue**) and click **"Approve & Send to Gemini"** on the pending item.
6. [ ] Switch to Tab 3 (**Research Cards**) and highlight Reported Facts vs Uncertainties.
7. [ ] Switch to Tab 4 (**Analytics**) and show the 62.5% local filter savings rate.
