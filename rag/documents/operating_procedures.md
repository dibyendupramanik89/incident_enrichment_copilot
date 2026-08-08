# Operating Procedures — Equipment Normal Ranges and Standards

## 1. Boiler Feed Pump 101 (BFP-101) Operating Specifications

**Equipment Tag**: BFP-101
**Asset ID**: ASSET-001
**Type**: Centrifugal multistage pump
**Design Flow**: 120 m³/h
**Design Head**: 280 m
**Driver**: Electric motor, 75 kW, 2-pole, 2980 RPM

### Normal Operating Ranges

| Parameter | Normal Range | Alarm Low | Alarm High | Trip |
|-----------|-------------|-----------|------------|------|
| Suction Pressure | 2.5–3.5 bar | 2.0 bar | — | 1.5 bar |
| Discharge Pressure | 28–32 bar | 22 bar | 36 bar | 38 bar |
| Bearing Temperature (drive end) | 45–65°C | — | 80°C | 90°C |
| Bearing Temperature (non-drive end) | 40–60°C | — | 75°C | 85°C |
| Vibration (bearing housing) | 1.0–3.5 mm/s | — | 7.1 mm/s | 11.2 mm/s |
| Motor Current | 85–100 A | — | 115 A | 125 A |
| Flow Rate | 80–130 m³/h | 40 m³/h | — | 35 m³/h |

### Standard Start-up Procedure (SOP-BFP-001)
1. Verify suction valve is 100% open and discharge valve is closed
2. Ensure mechanical seal flush system is operating (flush pressure: 0.5 bar above suction)
3. Prime pump if idle > 8 hours (open vent valve, wait for continuous liquid flow)
4. Start motor — verify motor current normalises within 10 seconds
5. Slowly open discharge valve over 30 seconds
6. Verify flow rate, pressure, vibration, and temperature within normal ranges within 2 minutes
7. Log start time and initial readings in equipment logbook

### Standard Shutdown Procedure
1. Slowly close discharge valve over 20 seconds
2. Stop motor
3. Close suction valve if pump will be isolated for > 4 hours
4. Leave seal flush running until pump temperature drops below 50°C

### Maintenance Schedule
| Item | Interval |
|------|----------|
| Visual inspection (leaks, vibration, temperature) | Daily |
| Vibration analysis (route-based) | Monthly |
| Suction strainer cleaning | 6 months (or on dP > 0.4 bar) |
| Mechanical seal inspection | 12 months (or 8,000 operating hours) |
| Bearing replacement | 24 months (or 20,000 operating hours) |
| Impeller inspection | Major shutdown (every 3 years) |

---

## 2. Compressor C-201 Operating Specifications

**Equipment Tag**: C-201
**Asset ID**: ASSET-003
**Type**: Centrifugal compressor, 2-stage
**Capacity**: 15,000 Nm³/h
**Driver**: Gas turbine + electric motor helper

### Normal Operating Ranges

| Parameter | Normal Range | Alarm Low | Alarm High | Trip |
|-----------|-------------|-----------|------------|------|
| Suction Pressure | 2.8–3.2 bar | 2.2 bar | — | 1.8 bar |
| Discharge Pressure | 18–22 bar | 15 bar | 24 bar | 26 bar |
| Discharge Temperature | 85–125°C | — | 135°C | 155°C |
| Lube Oil Inlet Temp | 40–50°C | 35°C | 60°C | 65°C |
| Cooling Water Inlet Temp | 25–32°C | — | 40°C | — |
| Vibration (radial) | 1.5–3.5 mm/s | — | 7.1 mm/s | 11.0 mm/s |
| Axial Displacement | 0–0.15 mm | — | 0.30 mm | 0.45 mm |
| Speed | 9,500–10,500 RPM | 8,500 RPM | — | 11,000 RPM |

### Anti-Surge Control
- Anti-surge valve opens automatically when operating point approaches surge line
- Surge margin: 10% minimum separation from surge curve at all times
- If anti-surge valve opens > 30% during normal operation: investigate root cause (suction flow drop or discharge pressure rise)

### Operating Restrictions
- Do not operate at > 85% load when cooling water inlet temperature > 38°C
- Do not start if lube oil temperature < 30°C (risk of journal bearing damage)
- Minimum operating load: 30% to avoid stall/surge

---

## 3. Motor M-501 Operating Specifications

**Equipment Tag**: M-501
**Asset ID**: ASSET-006
**Type**: AC induction motor
**Rating**: 200 kW, 380V, 3-phase, 50 Hz
**Full Load Amps (FLA)**: 380 A

### Normal Operating Ranges

| Parameter | Normal Range | Alarm | Trip |
|-----------|-------------|-------|------|
| Current (per phase) | 320–360 A | 400 A | 420 A |
| Phase imbalance | < 3% | 5% | — |
| Winding temperature | 40–75°C | 100°C | 130°C |
| Bearing temperature | 35–65°C | 80°C | 90°C |
| Vibration | 1.0–3.0 mm/s | 6.0 mm/s | 9.5 mm/s |

### Overload Relay Settings
- Class 10 thermal overload relay
- Trip current: 110% FLA = 418 A
- Trip time: < 10 seconds at 600% FLA (starting current), adjustable for trip class

---

## 4. Heat Exchanger HX-101 Operating Specifications

**Equipment Tag**: HX-101
**Asset ID**: ASSET-004 (associated)
**Type**: Shell-and-tube, fixed tubesheet
**Service**: Compressor inter-stage cooling
**Design heat duty**: 2.8 MW

### Normal Operating Ranges

| Parameter | Normal Range | Alarm |
|-----------|-------------|-------|
| Tube-side outlet temperature | 35–45°C | > 55°C |
| Shell-side pressure drop | 0.15–0.35 bar | > 0.55 bar |
| Tube-side pressure drop | 0.08–0.20 bar | > 0.35 bar |
| Cooling water flow | 180–220 m³/h | < 140 m³/h |

### Fouling Management
- Design fouling factor: 0.0002 m²·K/W (tube side), 0.0001 m²·K/W (shell side)
- Clean when calculated U-value drops > 20% below design U-value
- Inspection interval: annually during planned turnaround

---

## 5. Alarm Management System Philosophy

### Alarm Design Criteria (aligned with ISA-18.2 / IEC 62682)
- Operator response time available: minimum 10 minutes for priority 2 alarms
- Maximum alarm rate during normal operations: ≤ 1 alarm per 10 minutes per operator
- Maximum alarm rate during major upsets: ≤ 10 alarms per 10 minutes per operator
- Alarm activation must require a defined operator response (no informational-only alarms without action)

### Setpoint Rationalisation Criteria
An alarm is a rationalization candidate if it meets ANY of the following:
- Fires > 5 times per month without resulting in a process intervention
- Auto-clears (activates and clears) within 30 seconds more than 50% of the time
- Has the same setpoint as another alarm on the same variable (duplicate)
- Has no defined operator response in the alarm response manual

### Alarm Suppression Rules
- Suppression is only permitted for consequential alarms when root cause is identified
- Time-limited suppression: maximum 4 hours, requires shift engineer authorisation
- Alarm bypass (maintenance): maximum 24 hours, requires engineer and safety authorisation
- All suppressions and bypasses must be logged in the MOC (management of change) system

---

## 6. Incident Ticket Priority Standards

### Priority 1 (Critical) — Response Within 5 Minutes
**Criteria**: Active alarm on critical asset with severity = critical, OR immediate safety hazard identified
**Required Actions**:
- Immediate notification to shift engineer
- Assessment and initial response within 5 minutes
- Hourly status updates until resolved
- Post-incident review mandatory within 24 hours

### Priority 2 (High) — Response Within 15 Minutes
**Criteria**: Active alarm on high-criticality asset, OR critical alarm on medium-criticality asset
**Required Actions**:
- Notification to shift engineer within 5 minutes
- Physical assessment within 15 minutes
- Status update every 4 hours
- Post-incident review within 5 working days

### Priority 3 (Medium) — Response Within 2 Hours
**Criteria**: Medium severity alarm, or high severity alarm on low-criticality equipment
**Required Actions**:
- Included in next shift handover
- Planned investigation within working day
- Resolution target: 5 working days

### Priority 4 (Low) — Scheduled Response
**Criteria**: Low severity or advisory alarm
**Required Actions**:
- Logged for weekly maintenance planning meeting
- Resolution target: next planned maintenance window
