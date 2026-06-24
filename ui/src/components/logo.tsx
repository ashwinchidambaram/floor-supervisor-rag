// ---------------------------------------------------------------------------
// logo.tsx — the Orbit AC mark (ported from personal-website). Role · contract · failure:
//   Role:     the brand mark — geometric "AC" inside a tilted orbit with one terracotta
//             planet. Replaces the old "M" wordmark.
//   Contract: <OrbitMark size color accent animated/> · <ACMonogram size variant/>.
//   Failure:  pure SVG, no data; honors prefers-reduced-motion (renders the resting planet).
// ---------------------------------------------------------------------------

import React from "react";

const _SGf = "'Space Grotesk', 'Inter', sans-serif";

/** Orbit hero mark (SVG, optional slow spin). */
export function OrbitMark({
  size = 160, color = "#0B1E36", accent = "#D4745E", animated = false, sw,
}: { size?: number; color?: string; accent?: string; animated?: boolean; sw?: number }) {
  const s = size, cx = s / 2, cy = s / 2;
  const stroke = sw || s * 0.022;
  const rx = s * 0.46, ry = s * 0.235, tilt = -22, tt = -0.62;
  const rad = (tilt * Math.PI) / 180;
  const ex = rx * Math.cos(tt), ey = ry * Math.sin(tt);
  const px = cx + ex * Math.cos(rad) - ey * Math.sin(rad);
  const py = cy + ex * Math.sin(rad) + ey * Math.cos(rad);
  const pr = s * 0.05;
  const uid = "om" + Math.round(s * 131);

  const [reduce, setReduce] = React.useState(false);
  React.useEffect(() => {
    const m = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduce(m.matches);
    const on = () => setReduce(m.matches);
    m.addEventListener?.("change", on);
    return () => m.removeEventListener?.("change", on);
  }, []);
  const moving = animated && !reduce;

  const cosR = Math.cos(rad), sinR = Math.sin(rad);
  const Lx = cx - rx * cosR, Ly = cy - rx * sinR;
  const Rx = cx + rx * cosR, Ry = cy + rx * sinR;
  const f = (n: number) => n.toFixed(2);
  const orbitPath = `M ${f(Rx)} ${f(Ry)} A ${f(rx)} ${f(ry)} ${tilt} 0 1 ${f(Lx)} ${f(Ly)} A ${f(rx)} ${f(ry)} ${tilt} 0 1 ${f(Rx)} ${f(Ry)}`;

  const Planet = () => (
    <circle r={pr} fill={accent}>
      <animateMotion dur="9s" repeatCount="indefinite" path={orbitPath} />
    </circle>
  );

  return (
    <svg viewBox={`0 0 ${s} ${s}`} width={s} height={s} style={{ display: "block", overflow: "visible" }}>
      {moving && (
        <defs>
          <clipPath id={`${uid}-far`} clipPathUnits="userSpaceOnUse">
            <rect x={cx - s} y={cy - s} width={s * 2} height={s} transform={`rotate(${tilt} ${cx} ${cy})`} />
          </clipPath>
          <clipPath id={`${uid}-near`} clipPathUnits="userSpaceOnUse">
            <rect x={cx - s} y={cy} width={s * 2} height={s} transform={`rotate(${tilt} ${cx} ${cy})`} />
          </clipPath>
        </defs>
      )}
      <ellipse cx={cx} cy={cy} rx={rx * 0.74} ry={ry * 1.16} fill="none" stroke={color} strokeWidth={stroke * 0.6} opacity={0.16} transform={`rotate(${tilt + 38} ${cx} ${cy})`} />
      <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="none" stroke={color} strokeWidth={stroke} opacity={0.55} transform={`rotate(${tilt} ${cx} ${cy})`} />
      {moving && (<g clipPath={`url(#${uid}-far)`}><Planet /></g>)}
      <text x={cx} y={cy + s * 0.012} fill={color} fontFamily={_SGf} fontWeight={500} fontSize={s * 0.46} letterSpacing={-s * 0.012} textAnchor="middle" dominantBaseline="middle">AC</text>
      {moving && (<g clipPath={`url(#${uid}-near)`}><Planet /></g>)}
      {!moving && <circle cx={px} cy={py} r={pr} fill={accent} />}
    </svg>
  );
}

/** Circular badge monogram — used in the top app-bar. */
export function ACMonogram({
  size = 64, variant = "light",
}: { size?: number; variant?: "dark" | "light" | "mono-dark" | "mono-light" }) {
  const pal = {
    dark: { bg: "#0B1E36", fg: "#F4EFE6", accent: "#D4745E" },
    light: { bg: "#F4EFE6", fg: "#0B1E36", accent: "#D4745E" },
    "mono-dark": { bg: "#0B1E36", fg: "#F4EFE6", accent: "#F4EFE6" },
    "mono-light": { bg: "#F4EFE6", fg: "#0B1E36", accent: "#0B1E36" },
  }[variant];
  const s = size, cx = s / 2, cy = s / 2, r = s * 0.48;
  const rx = s * 0.355, ry = s * 0.178, tilt = -22, tt = -0.6;
  const ex = rx * Math.cos(tt), ey = ry * Math.sin(tt);
  const rad = (tilt * Math.PI) / 180;
  const px = cx + ex * Math.cos(rad) - ey * Math.sin(rad);
  const py = cy + ex * Math.sin(rad) + ey * Math.cos(rad);
  return (
    <svg viewBox={`0 0 ${s} ${s}`} width={s} height={s} style={{ display: "block" }}>
      <circle cx={cx} cy={cy} r={r} fill={pal.bg} />
      <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="none" stroke={pal.fg} strokeWidth={s * 0.022} opacity={0.5} transform={`rotate(${tilt} ${cx} ${cy})`} />
      <text x={cx} y={cy + s * 0.012} fill={pal.fg} fontFamily={_SGf} fontWeight={500} fontSize={s * 0.4} letterSpacing={-s * 0.01} textAnchor="middle" dominantBaseline="middle">AC</text>
      <circle cx={px} cy={py} r={s * 0.05} fill={pal.accent} />
    </svg>
  );
}
