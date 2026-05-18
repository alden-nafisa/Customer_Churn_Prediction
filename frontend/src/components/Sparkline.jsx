export function Sparkline({ data, highlightIndex, colorClass = "indigo" }) {
  if (!data || data.length === 0) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const height = 40;
  const width = 120;
  const padding = 5;

  const scaleY = (val) =>
    height - padding - ((val - min) / (max - min)) * (height - 2 * padding);
  const scaleX = (idx) =>
    padding + (idx / (data.length - 1)) * (width - 2 * padding);
  const points = data
    .map((val, idx) => `${scaleX(idx)},${scaleY(val)}`)
    .join(" ");

  const colorMap = {
    indigo: "#6366f1",
    slate: "#64748b",
    rose: "#f43f5e",
    emerald: "#10b981",
  };

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={colorMap[colorClass] || colorMap.indigo}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {highlightIndex !== undefined && data[highlightIndex] !== undefined && (
        <circle
          cx={scaleX(highlightIndex)}
          cy={scaleY(data[highlightIndex])}
          r="4"
          fill="#f43f5e"
          className="shadow-sm"
        />
      )}
    </svg>
  );
}
