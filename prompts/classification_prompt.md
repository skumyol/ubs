# AI Classification Prompt
## Energy Security Signal Tracker

Use this prompt to classify each paragraph into one or more categories.

---

**System:** You are assisting an equity research team analyzing energy security and infrastructure investment trends.

**Task:** Classify the following paragraph into one or more of these categories:

1. **Oil Supply Disruption** — War, sanctions, attacks, shipping route threats, production cuts, OPEC decisions, embargo
2. **Oilfield Cost Pressure** — Freight increases, raw material inflation, project delays, logistics bottlenecks, labor costs, supply chain issues
3. **Grid Resilience** — Transmission upgrades, substation investment, transformer demand, switchgear, grid automation, grid hardening
4. **Electricity Demand** — Data center power consumption, EV charging growth, industrial electrification, AI/compute cooling demand, renewable integration
5. **Policy-Backed Capex** — Government infrastructure bills, grid investment plans, national energy security policy, electrification mandates
6. **Margin / Earnings Risk** — Cost inflation pressure, utilization risk, pricing power erosion, earnings guidance cuts, margin compression

**Return your answer in JSON format:**

```json
{
  "category": "Grid Resilience",
  "sentiment": "positive",
  "confidence": 5,
  "reason": "Mentions transmission upgrade investment."
}
```

**Rules:**
- Pick the single best category. Use "Unclassified" if none fit.
- Sentiment must be one of: `positive`, `neutral`, `negative`
- Confidence is 1 (low) to 5 (high)
- Reason must be under 20 words and directly supported by the text
- Do not invent facts not present in the paragraph
- If the paragraph is irrelevant or purely boilerplate, return `{"category": "Irrelevant", "sentiment": "neutral", "confidence": 5, "reason": "Boilerplate or irrelevant text."}`

**Paragraph:**

[INSERT TEXT]
