# Incident Enrichment System — Technical Overview

## What Is Incident Enrichment?

Incident enrichment is the process of taking a raw alarm signal and automatically adding:
- **Asset context**: criticality, location, health score, maintenance history
- **Historical patterns**: similar past alarms and how they were resolved
- **Document evidence**: relevant procedures, troubleshooting guides, safety instructions
- **Correlated events**: other alarms occurring on related assets at the same time
- **Prioritisation**: a computed priority score based on multiple operational factors

The goal is to reduce time-to-action by 60–80% by giving operators an enriched incident summary instead of a raw alarm ID.

---

## Data Sources

### 1. Alarm Management API
The primary source of structured alarm data. Provides:
- Real-time active alarm list with severity, status, asset, site, unit
- Alarm detail: description, start time, acknowledgement time, duration
- Trend data: historical alarm occurrence over configurable time windows
- Correlation analysis: alarms that co-occur within configurable lag windows
- Flood detection: windows where alarm rate exceeds safe operating levels
- KPI computation: recurring rate, avg acknowledgement delay, nuisance score

### 2. Ticketing System
Provides historical incident context:
- Past tickets for the same asset or alarm type
- Resolution notes: what was found and what fixed it
- Recurring patterns: assets with repeated incidents
- Open/in-progress tickets: avoid duplicate ticket creation

### 3. Document Corpus (RAG Knowledge Base)
Structured knowledge documents including:
- **alarm_response_playbook.md**: Standard response procedures by alarm type
- **troubleshooting_guide.md**: Root cause analysis trees and diagnostic steps
- **historical_resolutions.md**: Anonymised resolution notes from past incidents
- **operating_procedures.md**: Normal operating ranges and equipment specifications
- **faq.md**: Operator quick reference guide

---

## Enrichment Workflow

```
User Query
    ↓
Intent Detection
    ↓
Asset Resolution (via MCP → Alarm API)
    ↓
Alarm Retrieval (paginated, sorted by severity)
    ↓
Alarm Detail + Context
    ↓
Priority Scoring (severity + criticality + recurrence)
    ↓
Operator Recommendations (step-by-step actions)
    ↓
RAG Retrieval (documents grounding the answer)
    ↓
Similar Ticket Search (historical pattern matching)
    ↓
LLM Synthesis (grounded answer with citations)
    ↓
Draft Ticket (for write intents — requires human confirmation)
    ↓
Structured Response with MCP Trace + Citations
```

---

## Priority Scoring Model

The priority score P for an alarm is computed as:

```
P = w1 × severity_score + w2 × criticality_score + w3 × recurrence_score

Where:
  severity_score: critical=0.92, high=0.72, medium=0.45, low=0.20
  criticality_score: critical=1.0, high=0.75, medium=0.50, low=0.25
  recurrence_score: (count in 90 days) / 10, capped at 1.0
  weights: w1=0.50, w2=0.30, w3=0.20
```

Priority labels:
- P ≥ 0.85 → **Critical** (immediate response required)
- P ≥ 0.70 → **High** (< 15 minutes)
- P ≥ 0.45 → **Medium** (< 2 hours)
- P < 0.45 → **Low** (scheduled)

---

## Severity Definitions

| Level | Definition | Required Response |
|-------|------------|------------------|
| Critical | Imminent equipment damage or safety hazard | Immediate ESD or manual intervention |
| High | Significant process deviation | Operator action within 15 minutes |
| Medium | Process deviation within tolerable limits | Investigation within 2 hours |
| Low | Advisory/informational | Review during next scheduled shift |

---

## Asset Criticality Ratings — EastRefinery

| Asset | Type | Criticality | Unit | Notes |
|-------|------|-------------|------|-------|
| BFP-101 | Boiler Feed Pump | Critical | Unit 1 | No installed standby |
| BFP-102 | Boiler Feed Pump | High | Unit 1 | Standby for BFP-101 |
| C-201 | Compressor | Critical | Unit 2 | Single-train, no bypass |
| C-202 | Compressor | High | Unit 2 | Parallel train |
| HX-101 | Heat Exchanger | Medium | Unit 2 | Multiple units in service |

## Asset Criticality Ratings — SouthPlant

| Asset | Type | Criticality | Unit | Notes |
|-------|------|-------------|------|-------|
| M-501 | Motor | High | Unit 3 | Drives primary conveyor |
| M-502 | Motor | Medium | Unit 3 | Standby motor |

---

## Common Alarm Patterns and Root Causes

### Pattern 1: Pump Trip Cascade
**Trigger sequence**: Low suction pressure → pump trip → process flow low → downstream temperature high
**Root cause**: Usually suction strainer blockage or upstream valve failure
**Resolution**: Clear strainer, restore flow, verify instrument calibration

### Pattern 2: Compressor Temperature Cascade  
**Trigger sequence**: Cooling water low flow → compressor outlet temperature high → compressor vibration high
**Root cause**: Cooling water supply interruption (pump, valve, tower)
**Resolution**: Restore cooling water, verify lube oil temperatures, inspect anti-surge valve

### Pattern 3: Motor Overload Recurrence
**Trigger sequence**: Motor current high → trip → reset → trip again (recurring)
**Root cause**: Driven equipment mechanical issue (binding, wear, obstruction)
**Resolution**: Inspect mechanical coupling, check driven equipment for blockage or bearing failure

### Pattern 4: Instrument Drift Nuisance
**Trigger sequence**: Same alarm triggers repeatedly with no physical change
**Root cause**: Transmitter calibration drift, condensation in impulse lines, or faulty connection
**Resolution**: Calibrate or replace transmitter, trace and clear impulse line

---

## Key Performance Indicators

- **Alarm Flood Index**: Alarms per 10 minutes. Target: < 10 for normal operation.
- **Average Acknowledgement Delay**: Time from activation to acknowledgement. Target: < 3 minutes for critical.
- **Recurring Alarm Rate**: Alarms that fire more than 3× in 30 days. Target: < 5% of alarm list.
- **Nuisance Alarm Rate**: Alarms that auto-clear in < 30 seconds. Target: 0.
- **Mean Time to Resolution (MTTR)**: From ticket open to close. Target: < 4 hours for P1, < 24 hours for P2.
