# Incident Copilot FAQ — Operator Guide

## General

**Q: What is the Incident & Ticket Enrichment Copilot?**
A: The copilot is an AI assistant that helps operators triage industrial alarms, find historical context, and create structured incident tickets faster. It pulls live alarm data, searches similar past incidents, and retrieves relevant procedures automatically.

**Q: How do I start an investigation?**
A: Type a natural-language question in the chat box. Examples:
- "Prepare an incident for the highest-priority active alarm in EastRefinery"
- "Investigate recurring alarms on Boiler Feed Pump 101 over the last 90 days"
- "What are the recommended actions for the active compressor alarm?"
- "Show similar historical tickets for BFP-101 low suction pressure"

**Q: Does the copilot create tickets automatically?**
A: No. The copilot always creates a DRAFT first and shows it to you for review. You must click **Confirm Ticket Creation** and provide your operator ID before any ticket is written to the system. This is mandatory — the system will never create a ticket without explicit human approval.

---

## Alarm Investigation

**Q: What asset names can I ask about?**
A: The system knows these assets:
- Boiler Feed Pump 101 (BFP-101) — EastRefinery, Unit 1
- Boiler Feed Pump 102 (BFP-102) — EastRefinery, Unit 1
- Compressor C-201 — EastRefinery, Unit 2
- Compressor C-202 — EastRefinery, Unit 2
- Motor M-501 — SouthPlant, Unit 3
- Heat Exchanger HX-101 — EastRefinery, Unit 2

**Q: How does the copilot determine alarm priority?**
A: Priority scoring considers: alarm severity (critical/high/medium/low), asset criticality rating, historical recurrence rate, and current operational context. Scores range from 0.0 to 1.0. Scores ≥ 0.85 are labelled Critical, ≥ 0.70 are High, ≥ 0.45 are Medium, and below that are Low.

**Q: What is alarm correlation?**
A: Correlated alarms are alarms that tend to occur together within a short time window (default: 15 minutes) across related assets. For example, a cooling water flow alarm and a compressor temperature alarm often have the same root cause. The copilot uses cooccurrence analysis to surface these links.

**Q: What is alarm flood analysis?**
A: An alarm flood is when more than 10 alarms activate within any 10-minute rolling window on a single plant unit. The copilot can detect flood windows and identify the root cause alarm so operators don't chase consequential alarms.

**Q: What are rationalization candidates?**
A: These are alarms that trigger very frequently (default threshold: 5 times in the analysis period) without indicating a real process problem. They are nuisance alarms that waste operator attention. The copilot identifies them for potential suppression or setpoint review.

---

## RAG Document Retrieval

**Q: What documents does the copilot search?**
A: The copilot searches:
- Alarm Response Playbook (standard operating procedures)
- Troubleshooting guides for pumps, compressors, and motors
- Historical resolution notes from past incidents
- Operating procedures and maintenance standards

**Q: How do I know which documents were used?**
A: The RAG Citations panel shows every document source used to generate the answer, with a relevance score (0.0–1.0). Only documents scoring above 0.25 are included.

**Q: What does a low confidence response look like?**
A: If the copilot cannot find relevant documentation or alarm data, it will say so explicitly rather than guessing. Low-confidence responses include a caveat: "The following is based on limited evidence — verify with on-site inspection."

---

## Ticket Management

**Q: How do I edit the ticket draft?**
A: Go to the **Ticket Draft** tab. The draft fields (title, description, priority, recommended actions) are all editable text boxes. Make your changes before confirming.

**Q: What happens after I confirm ticket creation?**
A: The ticket is written to the ticketing system and assigned a permanent INC-XXXX identifier. The Draft ID is retired and can no longer be used. An audit log entry is created recording your operator ID, the timestamp, and the confirmed ticket ID.

**Q: Can I cancel a draft?**
A: Simply close the session or start a new query. Unconfirmed drafts do not create any ticket. They expire when the session ends.

---

## MCP Trace

**Q: What is the MCP Execution Trace?**
A: The MCP Trace tab shows every tool the copilot called to answer your query: which server, which tool, how long it took, and whether it succeeded. This gives full auditability of the copilot's reasoning steps.

**Q: What do the green and red indicators mean?**
A: Green ✅ means the tool call succeeded. Red ❌ means the tool call failed. The copilot handles individual tool failures gracefully — a failed non-critical tool results in a degraded but still useful response, not a complete failure.

---

## Security and Compliance

**Q: Is my input monitored for sensitive data?**
A: Yes. The copilot automatically detects and masks PII (email addresses, phone numbers, account numbers) in both inputs and outputs. It also screens inputs for prompt injection attempts — attempts to override system behaviour will be blocked.

**Q: Is the copilot's output always accurate?**
A: The copilot grounds all answers in retrieved data and documents. It is designed to say "I don't know" rather than fabricate. However, always verify critical recommendations with on-site observation before taking action.
