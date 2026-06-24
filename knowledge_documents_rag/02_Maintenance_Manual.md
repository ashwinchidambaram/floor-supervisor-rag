# EQUIPMENT MAINTENANCE MANUAL

**Meridian Precision Manufacturing — Plant 7, Rockford, Illinois**

| | |
|---|---|
| Document Number | MPM-MNT-002 |
| Revision | 5.4 |
| Effective Date | February 1, 2026 |
| Document Owner | Maintenance Department |
| Approved By | Maintenance Manager; Reliability Engineer |
| Review Cycle | Annual |
| Classification | Controlled — printed copies are uncontrolled |

---

## FOREWORD

This manual is the working reference for maintaining the primary production equipment at Plant 7. It is written to be used at the machine, by the people who keep it running: maintenance technicians performing scheduled work, operators performing first-line checks, and supervisors deciding whether a fault can be cleared on the line or requires a technician and a work order.

Throughout this manual, tasks are marked **(O)** where they may be performed by a trained operator or supervisor, and **(T)** where they require a qualified maintenance technician. Respect that distinction. A task marked (T) is marked that way because doing it wrong creates a hazard or damages the machine.

**WARNING:** Every maintenance task in this manual begins with the same prerequisite: apply and verify lockout/tagout in accordance with manual MPM-EHS-001, Section 3, before any guard is opened or any hand enters a danger zone. This instruction is not repeated at every step. Treat it as standing.

---

## SECTION 1 — EQUIPMENT COVERED

This manual covers the MPS-400 stamping press on Press Line A, the four CNC VF-4 machining cells, the robotic welding cells WC-1 and WC-2, and the powder coat line consisting of the conveyor, spray booth, and cure oven. Asset identification numbers are stenciled on each machine and match the records in the computerized maintenance management system (CMMS).

---

## SECTION 2 — PREVENTIVE MAINTENANCE

Preventive maintenance, or PM, is scheduled and tracked in the CMMS. The intervals below are minimums. If conditions are harsh — heavy production, high ambient temperature, abrasive material — the interval is shortened on the advice of the Reliability Engineer.

**NOTE:** An asset whose PM is overdue by more than ten percent of its interval is placed in restricted status. It may continue to run only with supervisor review and a documented plan to bring the PM current.

### 2.1 MPS-400 Stamping Press

Each day, before production, the operator checks the hydraulic oil level, walks the machine for leaks, confirms the light-curtain test passes, and drains the pneumatic filter bowl. The operator also performs the brake-monitor stopping-time test and records the result; if the stopping time has lengthened, the press is removed from service immediately.

Each week, a technician greases the ram gibs and connection points per Section 3 and inspects the die clamps for tightness. Each month, a technician inspects the clutch and brake air valves, checks the counterbalance pressure, and verifies the bolster bolt torque. Each quarter, a hydraulic oil sample is drawn for analysis, the drive belts are inspected, and the two-hand control timing is verified. Annually, the hydraulic filter is replaced, the clutch and brake friction surfaces are inspected, and a full geometry check of ram-to-bolster parallelism is performed.

### 2.2 CNC VF-4 Machining Cells

Each day, the operator checks coolant concentration with a refractometer (target 8 to 10 percent), clears chips, and confirms the way-lube reservoir is filled. Each week, the operator cleans the coolant tank screen, checks spindle air pressure, and inspects the axis way covers for damage.

Each month, a technician lubricates the way surfaces, inspects the spindle drawbar tension, and backs up the machine parameters. Each quarter, the technician checks spindle runout (which must be 0.0002 inch total indicator reading or less), checks ballscrew backlash compensation, and performs a full coolant change. Annually, the spindle bearings are assessed by vibration analysis, the axis geometry is calibrated, and the control-memory backup battery is replaced.

### 2.3 Welding Cells WC-1 and WC-2

Each day, the operator checks shielding-gas flow (target 25 to 30 cubic feet per hour), inspects the torch consumables, and cleans spatter from the nozzle. Each week, the operator inspects the wire feed rollers and liner, checks clamp air pressure at 90 psi, and tests the emergency stops and gate interlocks.

Each month, a technician verifies the robot tool center point, lubricates the robot axes per the manufacturer's schedule, and inspects the ground cable. Each quarter, the torch liner is replaced, weld parameters are verified against the approved golden program, and the robot encoders are mastered. Annually, the robot reducer oil is changed, a full payload and repeatability test is run, and the gas regulator is calibrated.

### 2.4 Powder Coat Line

Each day, the operator checks the oven temperature setpoint and ramp, inspects the booth filters, and verifies conveyor speed. Each week, the booth filters are cleaned or replaced, gun voltage is checked (target 60 to 90 kV), and the spray nozzles are cleaned. Each month, a technician titrates the pretreatment chemistry, inspects the conveyor chain lubrication, and verifies ground continuity from the part to ground (which must read less than 1 megohm). Each quarter, an oven temperature uniformity survey is performed (zones must agree within ±10°F) and the pump seals are inspected.

---

## SECTION 3 — LUBRICATION

Use only the lubricant specified for each point. Lubrication points are color-tagged at the machine to match the specification.

**CAUTION:** Do not mix incompatible greases. Combining a lithium-base grease with a polyurea-base grease, for example, breaks down both and causes premature bearing failure. When changing grease types, the old grease must be fully purged first.

| Equipment | Point | Lubricant | Specification | Interval |
|---|---|---|---|---|
| MPS-400 | Ram gibs / slides | Way oil | ISO VG 220 | Weekly |
| MPS-400 | Main bearings | EP grease, lithium | NLGI 2 | Monthly |
| MPS-400 | Hydraulic reservoir | AW hydraulic oil | ISO VG 46 | Top off daily; replace annually |
| CNC VF-4 | Way surfaces | Way lube | ISO VG 68 | Auto-lube; check reservoir daily |
| CNC VF-4 | Spindle | Sealed, no service | — | — |
| Welding robots | Axis gearboxes | Robot reducer oil | Manufacturer-specified | Annually |
| Powder conveyor | Chain | High-temp chain oil | NLGI 1, rated 400°F | Monthly |

---

## SECTION 4 — TORQUE SPECIFICATIONS

Torque values below are for dry threads unless noted. Always use a torque wrench with current calibration; calibration is verified quarterly and cross-referenced to the quality records in MPM-QC-003, Section 6.

**CAUTION:** Never reuse a single-use locking fastener. Replace it. Where a thread-locking compound is specified, apply the specified grade — substituting a stronger grade can make later removal impossible without damage.

| Application | Fastener | Torque | Notes |
|---|---|---|---|
| MPS-400 die clamp bolts | M20 grade 10.9 | 410 N·m (302 ft·lb) | Tighten in a star pattern; re-check after the first stroke |
| MPS-400 bolster mounting | M24 grade 10.9 | 710 N·m (524 ft·lb) | — |
| CNC VF-4 tool holder retention | Per drawbar spec | 1,200 lbf draw | Verify with drawbar gauge |
| CNC VF-4 vise jaw bolts | M12 grade 8.8 | 80 N·m (59 ft·lb) | — |
| Welding fixture clamp base | M16 grade 8.8 | 195 N·m (144 ft·lb) | Apply Loctite 243 (blue) |
| Conveyor drive coupling | M10 grade 8.8 | 47 N·m (35 ft·lb) | — |

---

## SECTION 5 — TROUBLESHOOTING

This section guides first-response diagnosis. For each symptom, the likely cause and the corrective action are given. Actions marked (O) may be performed by an operator or supervisor; actions marked (T) require a technician and a work order. When in doubt, raise the work order.

### 5.1 MPS-400 Stamping Press

If the press will not initiate a stroke, the light curtain is most likely blocked or the two-hand controls are outside their timing window. Clear the light-curtain field (O). If the press still will not stroke, the control timing has drifted; raise a work order (T).

If the ram is slow or tonnage is weak, suspect low hydraulic oil, pump wear, or relief-valve drift. Check and top off the oil (O). If the gauge still reads low pressure, raise a work order (T).

If there is excessive noise or a knock at the bottom of the stroke, suspect worn gibs or loose die clamps. Stop the press, apply lockout, and verify the die clamp torque (O); if the noise persists with clamps correct, raise a work order (T).

**WARNING:** A brake-monitor fault or a lengthening stopping time is safety-critical. Remove the press from service immediately, red-tag it, and raise a Priority 1 work order. Do not attempt to run the press until the brake system is verified by a technician.

If the hydraulic oil is overheating above 130°F, suspect a fouled cooler, low oil, or pump bypass. Check the cooler and oil level (O); if it persists, raise a work order (T).

### 5.2 CNC VF-4

A poor surface finish usually means a dull tool, low coolant concentration, or spindle runout. Replace the tool and confirm coolant at 8 to 10 percent (O). If runout is suspected, raise a work order (T).

Alarm 144, way lube low, means the way-lube reservoir is empty; refill with ISO VG 68 (O). Alarm 117, spindle overload, usually means the feed or depth of cut is too aggressive or the tool is binding; reduce the feed and inspect the tool (O).

If parts are drifting out of tolerance over a run, suspect thermal growth, axis backlash, or a loose fixture. Allow a proper warm-up cycle and check the fixture (O). If backlash is suspected, raise a work order for compensation (T).

If coolant is not reaching the cut, the nozzle is likely clogged or the pump pressure is low. Clear the nozzle (O); if the pump is weak, raise a work order (T).

### 5.3 Welding Cells

Porosity in the weld points to low gas flow, dirty base metal, or a spatter-clogged nozzle. Confirm gas flow at 25 to 30 CFH and clean the nozzle and part (O).

Wire feed stutter or birdnesting at the feeder usually means worn drive rollers, a clogged liner, or incorrect tension. Adjust the tension and inspect the liner (O); replace the liner if worn (T).

A robot position fault or an off-seam weld can be caused by tool-center-point drift or by a clamp that is not seating the part. Re-verify the tool center point (T) and confirm clamp air at 90 psi (O).

Burn-through on thin sections means excessive current or travel speed too slow. Restore the approved golden-program parameters (O); if it persists, raise a work order (T).

### 5.4 Powder Coat

Thin or uneven coating points to low gun voltage, a poor part ground, or a worn nozzle. Confirm voltage at 60 to 90 kV and verify the ground reads less than 1 megohm (O). **NOTE:** Coating thickness problems are frequently a process fault rather than a part defect — see the cross-reference to quality in MPM-QC-003, Section 3, before scrapping parts.

Orange-peel texture or poor flow-out points to an oven temperature or time problem, or contaminated powder. Verify the oven setpoint and uniformity (O, escalating to T). Fisheyes or craters indicate oil contamination on the part or moisture in the compressed air; check the pretreatment line and drain the air dryer (O).

---

## SECTION 6 — FAULT CODE QUICK REFERENCE (CNC VF-4)

| Code | Meaning | First Action |
|---|---|---|
| 102 | Servo overheat | Check the enclosure cooling fan; allow to cool (O) |
| 117 | Spindle overload | Reduce load; inspect the tool (O) |
| 144 | Way lube low | Refill the reservoir (O) |
| 159 | Low air pressure | Verify the 85 psi supply (O) |
| 201 | Axis travel limit | Jog off the limit in handle mode (O) |
| 9999 | Control battery low | Schedule the battery PM; do not power off until parameters are backed up (T) |

---

## SECTION 7 — CRITICAL SPARE PARTS

The following parts are held in critical stock so that a failure does not become extended downtime. When stock falls below the minimum, the storeroom reorders automatically.

| Part | Used On | Minimum Stock | CMMS Number |
|---|---|---|---|
| Hydraulic filter element | MPS-400 | 2 | SP-MPS-FLT-10 |
| Light curtain transmitter/receiver pair | MPS-400 | 1 | SP-MPS-LC-04 |
| Way-lube cartridge | CNC VF-4 | 6 | SP-VF4-LUBE-68 |
| Spindle drawbar spring kit | CNC VF-4 | 1 | SP-VF4-DB-22 |
| Torch nozzle / contact tip kit | WC-1/WC-2 | 12 | SP-WC-TORCH-A |
| Wire feed drive roller | WC-1/WC-2 | 4 | SP-WC-ROLL-035 |
| Booth filter, primary | Powder line | 8 | SP-PC-FLT-PRI |

---

## SECTION 8 — WORK ORDERS AND ESCALATION

When a fault is found, first attempt the operator-level corrective action in Section 5. If it cannot be resolved at that level, or the task is technician-level, the supervisor raises a CMMS work order recording the asset, the symptom, any fault code, and a priority.

Priorities are assigned as follows. Priority 1 is a safety-critical fault or a full line stoppage and requires a response within 30 minutes. Priority 2 is a single station down and requires a response within two hours. Priority 3 is a machine degraded but still running and is addressed the same shift. Priority 4 is scheduled or preventive work.

**WARNING:** Any safety-critical fault — a brake-monitor fault, a defeated guard, or a light-curtain failure — is automatically Priority 1, and the equipment is red-tagged out of service until a technician clears it. See MPM-EHS-001, Section 4.

---

## SECTION 9 — RECORDS

All preventive-maintenance completions, work orders, oil analysis reports, and calibration records are retained in the CMMS for a minimum of five years. Torque-wrench and gauge calibration certificates are cross-referenced to the quality records in MPM-QC-003, Section 6, so that a measurement taken on the floor can always be traced back to a calibrated instrument.

---

*End of Document MPM-MNT-002, Revision 5.4. Verify the current revision against the CMMS before use. Printed copies are uncontrolled.*
