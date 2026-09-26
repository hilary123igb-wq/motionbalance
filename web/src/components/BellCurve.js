// Decorative header illustration: a smooth curve with four labeled peaks,
// one per BP position (OG/OO/CG/CO). Purely visual - it is not a
// statistical density plot - but the *relative* peak heights are driven by
// each position's real average points from analytics.json (position_stats),
// scaled into a pleasant visual range. If no data is supplied the four
// peaks render at equal height rather than inventing numbers.
//
// Colors match the fixed position palette used everywhere else on the site
// (see components/StrengthBandChart.js) so OG/OO/CG/CO always mean the same
// color anywhere they appear.
const POSITIONS = [
  { key: "OG", color: "#2a78d6" },
  { key: "OO", color: "#eb6834" },
  { key: "CG", color: "#1baf7a" },
  { key: "CO", color: "#eda100" },
];

const WIDTH = 640;
const BASELINE = 176;
const VALLEY = 140;
const PEAK_MIN_Y = 66; // tallest peak
const PEAK_MAX_Y = 118; // shortest peak
const PEAK_X = [96, 261, 379, 544];

function catmullRom2bezier(points) {
  let d = `M${points[0].x},${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i - 1] || points[i];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2] || p2;
    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2.x},${p2.y}`;
  }
  return d;
}

function peakHeights(positionStats) {
  const byPos = Object.fromEntries((positionStats || []).map((p) => [p.position, p.avg_points]));
  const values = POSITIONS.map((p) => byPos[p.key]);
  const known = values.filter((v) => typeof v === "number");
  if (known.length < 2) return POSITIONS.map(() => (PEAK_MIN_Y + PEAK_MAX_Y) / 2);

  const min = Math.min(...known);
  const max = Math.max(...known);
  const span = max - min || 1;
  return values.map((v) => {
    const ratio = typeof v === "number" ? (v - min) / span : 0.5;
    return PEAK_MAX_Y - ratio * (PEAK_MAX_Y - PEAK_MIN_Y);
  });
}

export default function BellCurve({ positionStats, className = "" }) {
  const peakY = peakHeights(positionStats);

  const points = [
    { x: -40, y: BASELINE + 12 },
    { x: 0, y: BASELINE },
    { x: PEAK_X[0], y: peakY[0] },
    { x: (PEAK_X[0] + PEAK_X[1]) / 2, y: VALLEY },
    { x: PEAK_X[1], y: peakY[1] },
    { x: (PEAK_X[1] + PEAK_X[2]) / 2, y: VALLEY },
    { x: PEAK_X[2], y: peakY[2] },
    { x: (PEAK_X[2] + PEAK_X[3]) / 2, y: VALLEY },
    { x: PEAK_X[3], y: peakY[3] },
    { x: WIDTH, y: BASELINE },
    { x: WIDTH + 40, y: BASELINE + 12 },
  ];

  const linePath = catmullRom2bezier(points);
  const areaPath = `${linePath} L${WIDTH},${BASELINE + 30} L0,${BASELINE + 30} Z`;

  return (
    <div className={className} aria-hidden="true">
      <svg viewBox={`0 0 ${WIDTH} 218`} className="w-full h-auto" preserveAspectRatio="none">
        <defs>
          <linearGradient id="bellCurveArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="bellCurveStroke" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#2a78d6" />
            <stop offset="35%" stopColor="#eb6834" />
            <stop offset="65%" stopColor="#1baf7a" />
            <stop offset="100%" stopColor="#eda100" />
          </linearGradient>
        </defs>

        <path d={areaPath} fill="url(#bellCurveArea)" />
        <path d={linePath} fill="none" stroke="url(#bellCurveStroke)" strokeWidth="2.5" strokeLinecap="round" />

        {POSITIONS.map((p, i) => (
          <g key={p.key}>
            <circle cx={PEAK_X[i]} cy={peakY[i]} r="5" fill="#fff" stroke={p.color} strokeWidth="2.5" />
            <text
              x={PEAK_X[i]}
              y={peakY[i] - 16}
              textAnchor="middle"
              fontSize="15"
              fontWeight="600"
              fill={p.color}
            >
              {p.key}
            </text>
          </g>
        ))}

        <line x1="0" y1={BASELINE} x2={WIDTH} y2={BASELINE} stroke="#e1e0d9" strokeWidth="1" />
      </svg>
    </div>
  );
}
