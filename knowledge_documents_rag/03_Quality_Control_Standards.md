# QUALITY CONTROL MANUAL

**Meridian Precision Manufacturing — Plant 7, Rockford, Illinois**

| | |
|---|---|
| Document Number | MPM-QC-003 |
| Revision | 4.1 |
| Effective Date | January 20, 2026 |
| Document Owner | Quality Department |
| Approved By | Quality Manager; Plant Director |
| Conformance | Aligned to IATF 16949 / ISO 9001 |
| Review Cycle | Annual |
| Classification | Controlled — printed copies are uncontrolled |

---

## FOREWORD

This manual defines how quality is measured, judged, and protected at Plant 7. It is written for the people who make the calls on the floor: inspectors performing measurements, operators reacting to a control chart, and supervisors deciding whether a part is good, whether a lot is held, and when to escalate.

The reference product used throughout this manual is the bracket assembly, part number MPM-4471 — a part that is stamped, welded, and powder-coated, and therefore touches every process in the plant. Where a procedure is illustrated with MPM-4471 numbers, the same procedure applies to other parts using their own drawings and control plans.

The central principle of this manual is simple: a part is conforming only when it meets every requirement of its drawing and control plan. "Close enough" is not a quality standard. When a part does not conform, this manual tells you what to do with it and who decides.

---

## SECTION 1 — INSPECTION STAGES

A part is inspected at defined points along its route through the plant, and each inspection is recorded in the quality management system (QMS) against the part's traceability lot.

Incoming raw material — steel coil and sheet — is inspected against its material certificate, and thickness is verified by micrometer, for every lot received. At each new setup or die change, a First Article Inspection is performed, in which every feature on the drawing is laid out and measured before a full lot is allowed to run. During stamping, key blank dimensions are checked along with burr and crack inspection. During welding, weld size, penetration, and position are checked. At final inspection, coating thickness, the full set of features, and function are verified. Before shipment, the pack, label, and lot are confirmed.

The inspection method and frequency for each stage are summarized below.

| Stage | What Is Inspected | Method | Frequency |
|---|---|---|---|
| Incoming material | Certificate, thickness | Cert review, micrometer | Every lot |
| First Article (FAI) | Full dimensional layout | CMM and gauges | Each new setup / die change |
| In-process stamping | Key dimensions, burr, cracks | Caliper, visual | Per sampling plan |
| In-process welding | Weld size, penetration, position | Weld gauge, visual | Per sampling plan |
| Final | Coating, all features, function | Gauges, fixture | Per sampling plan |
| Outgoing | Pack, label, lot | Visual, scan | Every shipment |

---

## SECTION 2 — DIMENSIONAL SPECIFICATIONS

The acceptance limits for part MPM-4471 are taken directly from the released engineering drawing and are reproduced below. A feature conforms only when its measured value falls within the stated limits, inclusive of the limit values themselves. Geometric callouts such as true position and flatness are verified at First Article and at the frequency stated in the control plan.

| Feature | Nominal | Tolerance | Limits | Gauge |
|---|---|---|---|---|
| Overall length | 142.0 mm | ±0.30 mm | 141.70 – 142.30 mm | Caliper / CMM |
| Mounting hole diameter | 10.50 mm | +0.10 / −0.00 mm | 10.50 – 10.60 mm | Pin gauge |
| Hole true position | — | Ø0.25 mm at MMC | — | CMM |
| Flange angle | 90.0° | ±0.5° | 89.5 – 90.5° | Angle fixture |
| Material thickness | 3.00 mm | ±0.08 mm | 2.92 – 3.08 mm | Micrometer |
| Weld leg size | 5.0 mm | +1.0 / −0.0 mm | 5.0 – 6.0 mm | Fillet weld gauge |
| Powder coat thickness | 75 µm | — | 60 – 110 µm | Eddy-current gauge |
| Base flatness | — | 0.20 mm | ≤ 0.20 mm | CMM / surface plate |

**NOTE:** Material thickness ties back to the incoming-material specification in Section 1. Coating thickness ties back to the powder-line process settings in MPM-MNT-002, Section 2.4. When coating thickness is out of range, suspect a process fault — gun voltage or part grounding — and have maintenance check the line before condemning parts as defective.

---

## SECTION 3 — SAMPLING PLANS

In-process inspection uses ANSI/ASQ Z1.4, general inspection level II, single sampling, unless the control plan calls for 100 percent inspection. The acceptance quality limit, or AQL, applied to a lot depends on the severity of the defect being inspected for.

Critical defects are inspected to an AQL of zero, meaning 100 percent inspection and zero acceptance. Major defects are inspected to an AQL of 1.0. Minor defects are inspected to an AQL of 2.5.

As a worked example, for a lot of between 1,201 and 3,200 pieces at inspection level II, the sample size is 125 pieces. For major defects at AQL 1.0, the lot is accepted with 3 or fewer defects in the sample and rejected with 4 or more. For minor defects at AQL 2.5, the lot is accepted with 7 or fewer and rejected with 8 or more.

**WARNING:** A single critical defect found in any sample rejects the entire lot and triggers 100 percent containment of that lot. There is no acceptance number for a critical defect.

---

## SECTION 4 — DEFECT CLASSIFICATION

Every defect is classified by severity, because severity determines both the sampling plan and what may be done with the part.

A **critical defect** is one that affects safety, violates a regulatory requirement, or causes the part to lose its function. For part MPM-4471 this includes any crack in the weld or base metal, lack of weld penetration or a missing weld, the wrong material or wrong part entirely, a mounting hole that is missing, mislocated beyond its true position, or undersized below 10.50 mm so that it will not accept its fastener, and any sharp burr that presents a laceration hazard on a handled edge. Critical defects are never shipped, are never reworked back into specification without engineering approval, and are always quarantined.

A **major defect** is one likely to cause a failure in service or a customer rejection, but which is not immediately a safety hazard. This includes any functional dimension out of tolerance — length, flange angle, or thickness — a weld leg under 5.0 mm or with excessive porosity, coating thickness outside the 60 to 110 µm range, and deformation that affects fit.

A **minor defect** is cosmetic and unlikely to affect function: a light surface scratch within cosmetic limits, minor coating orange-peel or gloss variation, or a small handling mark outside any functional or sealing area.

---

## SECTION 5 — MEASUREMENT SYSTEMS AND CALIBRATION

Every gauge and instrument used to accept product is calibrated on a defined interval and is traceable to the National Institute of Standards and Technology. When an instrument is found out of calibration, it is removed from service and every measurement taken with it since its last valid calibration is reviewed for impact.

| Equipment | Calibration Interval | Tolerance / Standard |
|---|---|---|
| Coordinate measuring machine (CMM) | Annual, plus monthly artifact check | Per manufacturer; ball-bar verification |
| Digital calipers | 6 months | ± 0.02 mm |
| Micrometers | 6 months | ± 0.002 mm |
| Pin / plug gauges | Annual | Class ZZ |
| Eddy-current coating gauge | Annual, plus daily shim check | NIST-traceable foils |
| Torque wrenches (quality use) | Quarterly | ± 4%; cross-reference MPM-MNT-002 Sec. 4 |

The capability of each measurement system is assessed by a gauge repeatability and reproducibility study. A gauge with a GRR below 10 percent of the tolerance is acceptable. A GRR between 10 and 30 percent is conditionally acceptable, and only with quality-management approval. A GRR above 30 percent is rejected; the gauge or the measurement method must be improved before it is used to accept product.

---

## SECTION 6 — STATISTICAL PROCESS CONTROL

Key characteristics — overall length, mounting-hole diameter, weld leg size, and coating thickness — are monitored on the floor using X-bar and R control charts. The subgroup size is 5, sampled at the frequency set in the control plan.

A launching process must demonstrate a performance index, Ppk, of at least 1.67 before it is released to ongoing production. Once in ongoing production, a process must maintain a capability index, Cpk, of at least 1.33. A process whose Cpk falls below 1.33 requires a corrective action and increased inspection until capability is restored.

The operator reacts to an out-of-control signal on the chart. A signal is any of the following: a single point outside the control limits, seven consecutive points trending steadily up or down, or seven consecutive points on one side of the centerline. When a signal appears, the operator stops, notifies the supervisor, and quarantines all product made since the last verified in-control point.

---

## SECTION 7 — NONCONFORMING PRODUCT

When nonconforming product is found, it is tagged with a red HOLD tag and physically moved to the quarantine area so that it cannot be used by mistake. The supervisor then opens a Nonconformance Report in the QMS.

The disposition of nonconforming product — the decision about what happens to it — is made by the Material Review Board, which brings together Quality, Engineering, and Production. The available dispositions are use-as-is (accept the deviation as it stands), rework (bring the part back into specification by a defined process), repair (bring it to a usable but not fully conforming condition), scrap (the part cannot be used and is destroyed or recycled), and return to supplier (for an incoming-material defect).

| Disposition | Meaning | Approval Required |
|---|---|---|
| Use-as-is | Accept despite the deviation | Material Review Board, plus customer if specified |
| Rework | Restore to full specification | Quality Engineer |
| Repair | Restore to usable, not full spec | Material Review Board, plus customer approval |
| Scrap | Destroy or recycle | Quality (a supervisor may initiate) |
| Return to supplier | Incoming material defect | Quality and Purchasing |

**NOTE:** A floor supervisor may quarantine product, and may initiate the scrapping of clearly critical-defect parts, but may NOT authorize a use-as-is or repair disposition. Those decisions belong to the Material Review Board. A critical defect is never dispositioned use-as-is under any circumstances.

---

## SECTION 8 — FIRST ARTICLE INSPECTION

A full First Article Inspection is required whenever the process changes in a way that could affect the product: a new part, a die or fixture change, a tooling repair that affects form, a material change, or a process relocation. The inspection documents every characteristic on the drawing with its actual measured value and a pass-or-fail result.

**WARNING:** Production may not run a full lot until the First Article Inspection has been approved by Quality. This requirement is the quality-side counterpart to the die-change procedure in MPM-MNT-002 — when maintenance changes a die, quality must approve the first article before the line runs.

---

## SECTION 9 — TRACEABILITY

Every lot carries a traceability record that links the raw-material certificate, the production date and shift, the operator, the equipment used (press, machining cell, and weld cell identifiers), the inspection records, and the SPC data. Records for safety-related characteristics are retained for 15 years; all other quality records are retained for 5 years. In the event of a containment action or a recall, the traceability system must allow the affected parts to be isolated within 4 hours.

---

## SECTION 10 — ESCALATION GUIDE FOR SUPERVISORS

This guide summarizes the actions a floor supervisor takes for the most common quality events.

When a critical defect is found, stop the process, quarantine the affected product, place the lot under 100 percent containment, open a Nonconformance Report, and notify Quality immediately. When an out-of-control signal appears on a control chart, stop, quarantine all product made since the last good check, and notify Quality. When a gauge appears to be reading wrong or out of calibration, remove the gauge from service, flag the measurements taken with it, and notify Quality.

When coating or weld defects begin trending, check the linked process parameters in MPM-MNT-002 before scrapping parts, because the cause is often in the process rather than the part, and raise a maintenance work order if so. And whenever a disposition beyond scrap is being considered — use-as-is, rework, or repair — escalate to the Material Review Board rather than deciding on the floor.

---

*End of Document MPM-QC-003, Revision 4.1. Verify the current revision against the QMS before use. Printed copies are uncontrolled.*
