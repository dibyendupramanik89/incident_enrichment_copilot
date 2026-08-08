# Historical Incident Resolutions

This document contains anonymised resolution summaries from past incidents.
Use these patterns to guide investigation and resolution of new alarms.

---

## INC-1001: BFP-101 Recurring Low Suction Pressure

**Date**: 2026-04-10 to 2026-04-11
**Asset**: Boiler Feed Pump 101 (ASSET-001), EastRefinery Unit 1
**Alarm**: Low Suction Pressure (threshold: 2.0 bar)
**Severity**: High | **Duration**: 22 hours total over 3 days

### Symptom Description
BFP-101 low suction pressure alarm triggered 7 times over 3 days. Each occurrence lasted 15–45 minutes before auto-clearing. Process team initially attributed to normal flow variation.

### Root Cause
Suction strainer partially blocked by scale deposits. Differential pressure across strainer was 0.65 bar (normal < 0.3 bar). Scale accumulation had built up over 8 months since last cleaning (scheduled annually). Continuous vibration from cavitation had also eroded the strainer mesh slightly.

### Contributing Factors
- Increased scaling tendency due to changes in feed water treatment chemistry (switched supplier 3 months prior)
- Cleaning interval not adjusted to account for new chemistry
- Suction strainer dP indicator not included in standard operator rounds checklist

### Actions Taken
1. Suction strainer removed and cleaned — found 60% blockage by scale deposits
2. Suction pressure transmitter PT-BFP101-001 calibration verified — within spec
3. Setpoint for suction pressure alarm adjusted from 2.0 bar to 2.2 bar to provide earlier warning
4. Feed water treatment parameters reviewed and scaling inhibitor dose increased
5. Cleaning interval revised from 12 months to 6 months for this service

### Preventive Measures
- Suction strainer differential pressure added to daily operator rounds checklist
- Predictive cleaning interval modelled: clean when dP > 0.4 bar rather than fixed calendar
- Alarm setpoint adjusted to give earlier indication before cavitation onset

### Recurrence Indicator
If low suction pressure alarm recurs within 6 months of cleaning: suspect feed water chemistry change, verify scaling inhibitor effectiveness.

---

## INC-1002: C-201 High Discharge Temperature (Ongoing)

**Date**: 2026-06-14 (open as of report date)
**Asset**: Compressor C-201 (ASSET-003), EastRefinery Unit 2
**Alarm**: High Discharge Temperature (threshold: 135°C)
**Severity**: Critical | **Status**: In Progress

### Symptom Description
Compressor C-201 discharge temperature gradually rising from normal 105°C to 148°C over a 6-hour period. Alarm activated at 135°C. Temperature continued rising slowly after alarm acknowledgement.

### Preliminary Findings
1. Cooling water inlet temperature elevated at 41°C (design: 25–32°C) — cooling tower performance degraded
2. Lube oil temperature in normal range — bearing condition not the primary cause
3. Anti-surge valve position confirmed fully closed — not recirculating hot gas
4. Inter-stage temperature normal — not inter-stage cooler fouling

### Working Hypothesis
Cooling tower fan No. 3 had been offline for planned maintenance for 5 days. Combined with high ambient temperature (38°C outdoor), remaining cooling tower fans could not maintain target cooling water temperature. This cascaded to elevated compressor discharge temperature.

### Actions Taken So Far
1. Compressor load reduced from 95% to 75% to reduce heat generation
2. Cooling tower fan No. 3 maintenance expedited — expected online in 12 hours
3. Additional portable cooling water recirculation unit deployed as temporary measure
4. Engineering review initiated for cooling tower capacity adequacy during high-ambient periods

### Pending Actions
- Restore cooling tower to full capacity
- Confirm C-201 discharge temperature returns to < 125°C
- Perform post-event vibration analysis on C-201 bearings (prolonged high temperature may affect bearing condition)
- Update SOP to restrict C-201 load to 80% when cooling water inlet temperature > 38°C

---

## INC-1003: BFP-101 Mechanical Seal Replacement

**Date**: 2026-05-20 to 2026-05-22
**Asset**: Boiler Feed Pump 101 (ASSET-001), EastRefinery Unit 1
**Issue**: Mechanical seal leakage
**Severity**: Medium | **Duration**: 48-hour planned outage

### Symptom Description
Routine inspection during a 2-week planned turnaround revealed seal face wear exceeding replacement criteria. No alarm had triggered (leak was not yet at alarm threshold) but visual inspection confirmed seal end-of-life.

### Root Cause
Normal wear after 18,000 operating hours. Seal MTBO (mean time between overhauls) for this service is 20,000 hours. Replaced proactively to prevent in-service failure.

### Inspection Findings
- Primary seal face: wear depth 0.35 mm (limit: 0.30 mm) — exceeded limit
- Secondary seal face: wear depth 0.12 mm — within specification  
- O-rings: hardened and showing compression set — replaced as a matter of course
- Seal flush filter: 40% blockage by fine particulates — cleaned

### Actions Taken
1. Mechanical seal replaced per procedure MP-BFP-003
2. New seal: OEM John Crane Type 28 (same as previous)
3. Seal flush system pressure adjusted to 0.8 bar above suction pressure
4. Commissioning test: 2-hour leak test at 1.2× operating pressure — passed
5. Equipment history updated with new seal serial number and replacement date

### Lesson Learned
Seal flush filter inspection interval extended from 6 months to 3 months — accumulated particulates were reducing flush effectiveness and contributing to premature wear.

---

## INC-1004: Motor M-501 Overload — Multiple Occurrences

**Date**: 2026-06-15 (open)
**Asset**: Motor M-501 (ASSET-006), SouthPlant Unit 3
**Alarm**: Motor Overload (current > 105% FLA)
**Severity**: High | **Occurrences**: 4 times in one week

### Symptom Description
Motor M-501 overload alarm triggered 4 times in 7 days. Each time the motor was tripped by the overload relay and restarted. The restart interval between events was decreasing: 72 hours, 48 hours, 24 hours, 18 hours.

### Diagnostic Findings
- Motor phase current: 3-phase balanced — no electrical fault
- Motor winding temperature: 72°C — within Class F limit (155°C) but elevated vs historical baseline (55°C)
- Vibration: elevated at coupling end, 6.2 mm/s RMS (normal: 2.5 mm/s)
- Coupling inspection: found significant wear in flexible coupling elements

### Root Cause (Preliminary)
Flexible coupling elastomeric inserts (spider) degraded — approximately 70% worn. Worn inserts causing torque spikes during conveyor start-up which trigger the overload relay. Vibration elevation at coupling frequency confirms coupling as primary cause.

### Actions Taken
1. Coupling elements (spider inserts) replaced with new OEM parts
2. Coupling alignment verified with laser alignment tool — within ± 0.05 mm tolerance
3. Motor restarted and monitored for 4 hours — current stable at 98% FLA
4. Vibration reduced to 2.8 mm/s RMS after coupling replacement

### Preventive Measures
- Flexible coupling spider inserts added to annual planned maintenance scope
- Vibration monitoring increased to weekly readings for M-501 for next 3 months

---

## INC-1005: Unit 2 Alarm Flood Investigation

**Date**: 2026-05-05 to 2026-05-06
**Assets**: C-201, HX-101, and related Unit 2 utilities
**Alarm flood**: 18 alarms in 8-minute window
**Severity**: High (multiple) | **Duration**: 12 hours total impact

### Event Description
At 09:14, cooling water supply pressure to Unit 2 dropped suddenly from 4.2 bar to 1.8 bar. Over the next 8 minutes, 18 alarms activated as various pieces of equipment dependent on cooling water lost adequate cooling.

### Alarm Sequence (Root Cause → Consequential)
1. **Root cause**: CW-PUMP-02 cooling water circulation pump tripped (electrical fault)
2. **Consequential alarms** (listed in activation order):
   - CW header pressure low
   - C-201 cooling water low flow
   - HX-101 process outlet temperature high
   - C-201 discharge temperature high (×2: first stage and second stage)
   - C-201 lube oil temperature high
   - [12 more consequential alarms on other Unit 2 equipment]

### Operator Response
Operators initially attempted to respond to each alarm individually, overwhelming the operator on duty. After 4 minutes, the shift engineer arrived and identified the root cause (CW pump trip) by correlating the first alarm timestamp with the CW header pressure trend.

### Resolution
1. CW-PUMP-02 electrical fault investigated — overload relay trip due to blocked pump inlet screen
2. Pump inlet screen cleaned, motor reset and tested
3. CW-PUMP-03 (standby) started to restore CW supply while primary pump was being restored
4. CW supply restored at 09:51 — 37 minutes after initial trip
5. All consequential alarms cleared within 12 minutes of CW restoration

### Lessons Learned
1. **Alarm rationalization**: 11 of the 18 alarms were consequential to the CW pump trip. Alarm rationalization review initiated to suppress or delay consequential alarms when root cause is identified.
2. **CW pump monitoring**: CW pump inlet screen added to monthly visual inspection rounds.
3. **Standby pump auto-start**: CW-PUMP-03 auto-start on header pressure low setpoint enabled (was previously manual).
4. **Alarm flood SOP**: New SOP created for alarm flood response — focus on root cause alarm, not consequential alarms.
5. **Operator training**: Tabletop exercise added to annual training based on this scenario.
