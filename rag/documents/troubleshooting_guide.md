# Troubleshooting Guide — Industrial Equipment Alarms

## Boiler Feed Pump (BFP) Troubleshooting

### BFP-101 Low Suction Pressure Diagnosis

**Step 1: Rule out instrument fault**
- Compare DCS reading with local pressure gauge at suction nozzle
- If discrepancy > 0.2 bar: tag transmitter PT-BFP101-001 for calibration
- If readings agree: proceed to Step 2

**Step 2: Check suction strainer**
- Location: upstream of suction isolation valve, accessible at grade level
- Normal differential pressure: < 0.3 bar
- Action differential pressure: > 0.5 bar → schedule cleaning within 4 hours
- Emergency differential pressure: > 0.8 bar → stop pump, clean immediately

**Step 3: Verify upstream valve and tank level**
- Upstream gate valve should be 100% open (check valve position indicator)
- Feed tank T-101 level should be > 35% (low level setpoint: 20%)
- If tank level < 20%: notify process control for feed rate adjustment

**Step 4: Check for cavitation**
- Listen for crackling/grinding noise at pump casing
- Monitor pump vibration — cavitation increases vibration > 3x normal
- If cavitation suspected: reduce pump speed by 10% via VFD or switch to standby BFP-102

**Step 5: Review recent alarm history**
- Check if this alarm has triggered in the last 30 days
- Pattern: alarm + clear + alarm = instrument drift or intermittent flow restriction
- Pattern: alarm persisting > 30 min = genuine process issue requiring physical inspection

---

### BFP Mechanical Seal Troubleshooting

**Symptoms of seal failure:**
- Visible fluid leakage at pump seal housing
- Seal face temperature > 80°C (if temperature monitor installed)
- Pump vibration increase > 50% over baseline
- Low-level alarm on seal flush fluid reservoir

**Diagnostic Steps:**
1. Inspect seal area for fluid spray or drip during normal operation
2. Check seal flush system pressure (should be 0.5-1.0 bar above suction pressure)
3. Review vibration trend — continuous increase over days indicates progressive wear
4. Check seal face wear indicator if installed

**Resolution:**
- Minor leakage (drip): increase seal flush flow, plan replacement within 48 hours
- Moderate leakage (stream): transfer to BFP-102 standby, replace seal within 8 hours
- Severe leakage (spray): emergency shutdown, replace per procedure MP-BFP-003

---

### BFP Impeller Wear Diagnosis

**Indicators:**
- Reduced pump performance (lower head or flow at same speed)
- Increase in vibration at impeller pass frequency
- History of sand or debris in process fluid

**Diagnostic:**
1. Compare current head/flow curve against original pump curve (stored in equipment dossier)
2. If performance degraded > 10%: impeller inspection required at next planned shutdown
3. If performance degraded > 20%: expedite inspection

---

## Compressor Troubleshooting

### C-201 High Discharge Temperature Diagnosis

**Normal operating range**: 85–125°C at discharge nozzle

**Step 1: Verify cooling water**
- Cooling water inlet temperature: target 25–32°C
- Cooling water flow rate: should be within ± 10% of design (see datasheet CS-201-DS)
- If cooling water inlet temperature > 38°C: notify cooling tower operations
- If cooling water flow reduced: check header pressure and isolation valve positions

**Step 2: Check lube oil system**
- Lube oil inlet temperature to bearings: target 40–50°C
- Lube oil cooler outlet temperature: should be < 55°C
- High lube oil temperature → abnormal bearing heat generation → inspect bearings

**Step 3: Anti-surge valve inspection**
- Anti-surge valve should be fully CLOSED during normal operation
- If partially open: gas is recirculating at high temperature, increasing discharge temperature
- Check anti-surge valve positioner signal and physical position
- Recalibrate positioner if valve position does not match controller output

**Step 4: Inter-stage cooler check (if multi-stage compressor)**
- Measure inter-stage temperature
- If > 10% above design: inspect cooler for fouling
- Fouling schedule: clean every 6 months for normal duty

**Step 5: Suction condition review**
- If suction pressure has dropped, compression ratio increases, raising discharge temperature
- Check suction filter differential pressure
- Check upstream process conditions for abnormal pressure drop

---

### Compressor Vibration Elevated

**Normal vibration baseline**: 1.5–3.5 mm/s RMS (bearing housing, radial direction)

**Alarm threshold**: 7.1 mm/s RMS
**Trip threshold**: 11.0 mm/s RMS

**Possible causes and frequency signatures:**
| Frequency | Likely Cause |
|-----------|-------------|
| 1× running speed | Unbalance or misalignment |
| 2× running speed | Misalignment (angular) |
| Sub-synchronous | Oil whirl in journal bearings |
| Blade pass frequency | Fouled or damaged impeller/diffuser |
| High frequency broadband | Cavitation or surge |

**Actions:**
1. Trend vibration values over past 24 hours — gradual rise vs sudden rise have different causes
2. Check process conditions for incipient surge (suction/discharge pressure ratio)
3. If vibration > 7.1 mm/s and rising: reduce load by 15%, notify maintenance
4. If vibration > 9 mm/s: initiate controlled shutdown

---

## Motor Troubleshooting

### M-501 Motor Overload — Diagnostic Tree

```
Motor Overload Alarm
├── Check current on all 3 phases
│   ├── All phases similar (< 5% imbalance)
│   │   └── Driven load is the problem → check mechanical coupling
│   └── One phase significantly different
│       └── Electrical issue → check MCC, cable, connection
├── Check motor winding temperature
│   ├── Temperature normal (<80°C) → load issue
│   └── Temperature elevated (>80°C) → cooling or overload
└── Check driven equipment
    ├── Conveyor/pump jammed → clear obstruction
    ├── Bearing failure → vibration elevated, inspect bearing
    └── Normal mechanical resistance → review setpoint
```

**Electrical checks (require qualified electrician):**
- Verify supply voltage: should be within ± 5% of nameplate voltage
- Measure phase-to-phase voltages: imbalance > 2% can cause current imbalance
- Inspect MCC contacts for pitting or overheating evidence
- Check thermal overload relay calibration

**Mechanical checks:**
- Rotate driven equipment shaft by hand (locked out): should rotate freely
- Check coupling condition: worn flexible elements cause load fluctuation
- Inspect bearing housing for heat or unusual noise
- Measure motor shaft vibration

---

## Heat Exchanger HX-101 Troubleshooting

### Low Heat Transfer Performance

**Symptoms:**
- Process outlet temperature lower than design
- Higher pressure drop than normal
- Fouling factor increasing (compare with commissioning baseline)

**Diagnostic:**
1. Calculate overall heat transfer coefficient (U-value) from current temperatures and flows
2. Compare U-value to design U-value on datasheet HX-101-DS
3. If U-value reduced > 20%: cleaning required
4. If U-value reduced > 40%: tube bundle inspection for damage or fouling

**Cleaning schedule:**
- Normal duty: annually during planned shutdown
- High fouling service: every 6 months
- After process upsets: inspect and clean if U-value dropped > 15%

---

## General Diagnostic Principles

### Is the Alarm Real or Instrument-Related?

Use the **3-Point Check**:
1. Does a nearby independent sensor confirm the abnormal reading?
2. Does the field instrument (gauge, portable instrument) agree with the DCS reading?
3. Was the instrument recently calibrated or maintained?

If **2 or 3 answers are "No"**: suspect instrument fault, tag for maintenance.
If all answers are "Yes": the process condition is real.

### When to Escalate vs When to Resolve Locally

**Resolve locally (operator action sufficient):**
- Instrument drift confirmed → tag for maintenance
- Strainer blockage → schedule cleaning
- Process condition recoverable within normal operating procedure

**Escalate to shift engineer:**
- Root cause not identified after 30 minutes
- Multiple interacting alarms on same unit
- Physical inspection required beyond normal operator access

**Escalate to maintenance:**
- Equipment requires physical repair or replacement
- Seal, bearing, or coupling failure confirmed

**Escalate to engineering:**
- Alarm recurrence > 3 times in 30 days without identified root cause
- Process design limitation suspected
- Alarm setpoint possibly needs revision
