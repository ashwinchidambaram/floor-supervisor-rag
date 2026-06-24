// ---------------------------------------------------------------------------
// sourceLabel — human-readable names for the DocSource enum.
//
// Role:     Map the screaming-snake `DocSource` values onto floor-readable labels
//           for citation chips ("SAFETY_PROCEDURES" -> "Safety Procedures"). Pure
//           presentation; the enum stays the source of truth.
// Contract: sourceLabel(source) -> string. Total over the union (UNKNOWN included).
// Failure:  none — exhaustive switch with a default echo.
// ---------------------------------------------------------------------------

import type { DocSource } from "@/lib/types";

export function sourceLabel(source: DocSource): string {
  switch (source) {
    case "SAFETY_PROCEDURES":
      return "Safety Procedures";
    case "MAINTENANCE_MANUALS":
      return "Maintenance Manuals";
    case "QUALITY_CONTROL":
      return "Quality Control";
    case "UNKNOWN":
    default:
      return "Unknown source";
  }
}
