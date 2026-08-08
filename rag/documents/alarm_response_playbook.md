# Alarm Response Playbook

## Purpose
This playbook defines the standard response procedure for industrial alarms across EastRefinery and SouthPlant sites.

---

## Section 1: Critical Alarm Response (Severity: CRITICAL)

### Step 1 — Immediate Acknowledgement (within 2 minutes)
- Acknowledge the alarm in the DCS/SCADA system immediately.
- Record the alarm ID, asset ID, timestamp, and your operator ID.
- Do NOT silence without acknowledgement.

### Step 2 — Initial Assessment (within 5 minutes)
- Identify the affected asset name, tag, site, and unit.
- Check adjacent sensors: suction pressure, discharge pressure, temperature, flow rate, vibration.
- Confirm whether the alarm is genuine or instrument-related (compare with field observation).

### Step 3 — Isolation and Safe-State Initiation
- If the alarm indicates imminent mechanical failure, initiate emergency shutdown (ESD) per SOP-ESD-001.
- Notify the shift engineer and plant manager.
- Isolate the affected equipment if safe to do so.

### Step 4 — Root Cause Investigation
- Review alarm history for the last 90 days on the affected asset.
- Check for co-occurring alarms on correlated assets (e.g., cooling water, lube oil, seal systems).
- Compare against historical ticket resolutions (search INC tickets for same asset ID).

### Step 5 — Ticket Creation
- Create an incident ticket with: asset ID, alarm ID, severity, start time, description, initial root cause hypothesis.
- Attach relevant sensor readings and trend screenshots.
- Set priority based on asset criticality and alarm severity (see priority matrix below).

### Step 6 — Escalation
- Escalate to Maintenance if physical inspection is required.
- Escalate to Engineering if root cause is unknown after 30 minutes.
- Notify Safety if there is risk of personnel hazard.

---

## Section 2: High-Priority Alarm Response

### Boiler Feed Pump Alarms

#### Low Suction Pressure (ALM-001 type)
- **Threshold**: Below 2.0 bar for > 30 seconds
- **Likely Causes**:
  1. Clogged suction strainer (most common — check differential pressure)
  2. Upstream valve partially closed or failed
  3. Feed tank level too low (< 30% normal operating level)
  4. Suction pressure transmitter failure or drift
  5. Cavitation in progress (listen for unusual noise)
- **Immediate Actions**:
  1. Check suction strainer differential pressure indicator — if > 0.5 bar, schedule cleaning within 4 hours
  2. Verify upstream gate valve position (should be fully open)
  3. Check feed tank level indicator (T-101 level transmitter LT-201)
  4. Compare suction pressure reading with field gauge — if > 10% discrepancy, tag for instrument maintenance
  5. Reduce pump flow rate by 15% to relieve potential cavitation
- **Escalation Trigger**: Trip or sustained low pressure > 15 minutes without resolution

#### High Vibration (BFP vibration alarm)
- **Threshold**: Above 7.1 mm/s RMS on bearing housings
- **Likely Causes**:
  1. Mechanical seal deterioration
  2. Impeller wear or imbalance
  3. Misalignment after maintenance
  4. Cavitation-induced vibration
- **Immediate Actions**:
  1. Trend vibration readings over last 4 hours
  2. Check seal face temperature if available
  3. Switch to standby pump if dual-pump configuration
  4. Schedule vibration analysis within 24 hours

### Compressor Alarms

#### High Discharge Temperature (ALM-003 type)
- **Threshold**: Above 135°C on discharge line
- **Likely Causes**:
  1. Lube oil temperature too high (check lube oil cooler)
  2. Cooling water supply interrupted or reduced
  3. Anti-surge valve malfunction (recirculating hot gas)
  4. Fouled inter-stage cooler
  5. High compression ratio due to suction pressure drop
- **Immediate Actions**:
  1. Verify lube oil inlet temperature — should be 40–50°C
  2. Check cooling water flow rate and inlet temperature
  3. Inspect anti-surge valve position — confirm fully closed during normal operation
  4. Review suction conditions for abnormal pressure
  5. If temperature exceeds 150°C, initiate compressor shutdown procedure CS-001
- **Escalation Trigger**: Temperature > 150°C or rapid rise > 10°C/minute

#### Cooling Water Low Flow
- **Threshold**: Below 80% of design flow
- **Likely Causes**:
  1. Cooling tower fan failure
  2. Pump cavitation in cooling water circuit
  3. Partially closed isolation valve
  4. Fouled heat exchanger
- **Immediate Actions**:
  1. Check cooling water header pressure
  2. Verify cooling tower operational status
  3. Inspect all isolation valves in cooling water circuit
  4. If flow cannot be restored within 10 minutes, reduce compressor load by 20%

### Motor Alarms

#### Motor Overload (ALM-006 type)
- **Threshold**: Current > 105% of FLA for > 10 seconds
- **Likely Causes**:
  1. Overloaded driven equipment (pump, compressor, conveyor)
  2. Phase imbalance or voltage sag
  3. Mechanical binding in driven equipment
  4. Bearing failure in motor or driven load
- **Immediate Actions**:
  1. Check motor current on all three phases — imbalance > 5% indicates electrical issue
  2. Verify driven equipment is not mechanically jammed
  3. Check motor winding temperature — should not exceed Class F rating
  4. If current > 115% FLA, trip immediately via MCC
  5. Inspect coupling and driven load for mechanical issues

---

## Section 3: Priority Matrix

| Severity | Asset Criticality | Priority Label | Response Time |
|----------|------------------|----------------|---------------|
| Critical | Critical         | P1 - Critical  | Immediate (< 5 min) |
| Critical | High             | P1 - Critical  | Immediate (< 5 min) |
| High     | Critical         | P2 - High      | < 15 minutes  |
| High     | High             | P2 - High      | < 30 minutes  |
| Medium   | Critical         | P3 - Medium    | < 2 hours     |
| Low      | Any              | P4 - Low       | Scheduled     |

---

## Section 4: Alarm Flood Response

If more than 10 alarms activate within a 10-minute window on a single unit:
1. Notify shift engineer immediately — this is an alarm flood event.
2. Identify the root cause alarm (first alarm to trigger) — suppress all consequential alarms.
3. Focus response on root cause asset only.
4. Document all alarms in the flood window for post-incident review.
5. Create a single incident ticket for the flood event referencing all alarm IDs.

---

## Section 5: Ticket Documentation Standards

Every incident ticket must include:
- **Title**: [Asset Name] — [Alarm Name] — [Date]
- **Asset ID**: From asset register
- **Alarm IDs**: All associated alarm identifiers
- **Priority**: Based on priority matrix above
- **Description**: Observable symptoms, sensor readings, any field observations
- **Initial hypothesis**: Most likely root cause based on available data
- **Actions taken**: Chronological log of all response steps
- **Resolution**: Root cause confirmed, corrective action taken, recurrence prevention

---

## References
- SOP-ESD-001: Emergency Shutdown Procedures
- SOP-BFP-001: Boiler Feed Pump Operation
- MP-BFP-003: BFP Mechanical Seal Replacement
- CS-001: Compressor Shutdown Procedure
- EL-M501-001: Motor M-501 Electrical Specification

