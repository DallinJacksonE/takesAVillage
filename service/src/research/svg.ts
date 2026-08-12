export interface ChartPoint {
  x: number;
  y: number;
}

export interface ChartSeries {
  name: string;
  color: string;
  points: ChartPoint[];
}

export interface LineChartOptions {
  title: string;
  xLabel: string;
  yLabel: string;
  series: ChartSeries[];
}

export interface BarChartSeries {
  name: string;
  color: string;
  values: number[];
}

export interface BarChartOptions {
  title: string;
  xLabel: string;
  yLabel: string;
  labels: string[];
  series: BarChartSeries[];
}

const WIDTH = 960;
const HEIGHT = 540;
const LEFT = 80;
const RIGHT = 920;
const TOP = 60;
const BOTTOM = 470;

export function renderLineChart(options: LineChartOptions): string {
  const points = options.series.flatMap((series) => series.points).filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));
  const xValues = points.map((point) => point.x);
  const yValues = points.map((point) => point.y);
  const xMin = xValues.length ? Math.min(...xValues) : 0;
  const xMax = xValues.length ? Math.max(...xValues) : 1;
  const yMin = Math.min(0, ...(yValues.length ? yValues : [0]));
  const yMax = Math.max(1, ...(yValues.length ? yValues : [1]));
  const xRange = xMax === xMin ? 1 : xMax - xMin;
  const yRange = yMax === yMin ? 1 : yMax - yMin;
  const x = (value: number) => LEFT + ((value - xMin) / xRange) * (RIGHT - LEFT);
  const y = (value: number) => BOTTOM - ((value - yMin) / yRange) * (BOTTOM - TOP);

  const grid = Array.from({ length: 6 }, (_, index) => {
    const ratio = index / 5;
    const py = BOTTOM - ratio * (BOTTOM - TOP);
    const value = yMin + ratio * yRange;
    return `<line x1="${LEFT}" y1="${py}" x2="${RIGHT}" y2="${py}" class="grid"/><text x="${LEFT - 12}" y="${py + 5}" text-anchor="end">${format(value)}</text>`;
  }).join("");

  const lines = options.series.map((series, index) => {
    const path = series.points
      .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y))
      .map((point) => `${x(point.x).toFixed(2)},${y(point.y).toFixed(2)}`)
      .join(" ");
    const legendY = 72 + index * 22;
    return `<polyline points="${path}" fill="none" stroke="${escapeAttribute(series.color)}" stroke-width="3"/><line x1="${RIGHT - 135}" y1="${legendY}" x2="${RIGHT - 105}" y2="${legendY}" stroke="${escapeAttribute(series.color)}" stroke-width="3"/><text x="${RIGHT - 95}" y="${legendY + 5}">${escapeText(series.name)}</text>`;
  }).join("");

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-labelledby="chart-title chart-description"><title id="chart-title">${escapeText(options.title)}</title><desc id="chart-description">Line chart with ${options.series.length} data series.</desc><style>text{font:14px system-ui,sans-serif;fill:#24313f}.title{font-size:24px;font-weight:700}.axis{stroke:#52606d;stroke-width:2}.grid{stroke:#d9e2ec;stroke-width:1}</style><rect width="100%" height="100%" fill="#fff"/><text class="title" x="${WIDTH / 2}" y="35" text-anchor="middle">${escapeText(options.title)}</text>${grid}<line class="axis" x1="${LEFT}" y1="${BOTTOM}" x2="${RIGHT}" y2="${BOTTOM}"/><line class="axis" x1="${LEFT}" y1="${TOP}" x2="${LEFT}" y2="${BOTTOM}"/><text x="${(LEFT + RIGHT) / 2}" y="520" text-anchor="middle">${escapeText(options.xLabel)}</text><text x="22" y="${(TOP + BOTTOM) / 2}" text-anchor="middle" transform="rotate(-90 22 ${(TOP + BOTTOM) / 2})">${escapeText(options.yLabel)}</text>${lines}</svg>`;
}

export function renderBarChart(options: BarChartOptions): string {
 const values = options.series.flatMap((series) => series.values).filter(Number.isFinite);
 const yMax = Math.max(1, ...(values.length ? values : [1]));
 const groupWidth = (RIGHT - LEFT) / Math.max(1, options.labels.length);
 const barWidth = Math.min(52, groupWidth * 0.72 / Math.max(1, options.series.length));
 const bars = options.labels.flatMap((_label, labelIndex) => options.series.map((series, seriesIndex) => {
   const value = Number.isFinite(series.values[labelIndex]) ? series.values[labelIndex]! : 0;
   const height = (Math.max(0, value) / yMax) * (BOTTOM - TOP);
   const x = LEFT + labelIndex * groupWidth + groupWidth * 0.14 + seriesIndex * barWidth;
   const y = BOTTOM - height;
   return `<rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${barWidth.toFixed(2)}" height="${height.toFixed(2)}" fill="${escapeAttribute(series.color)}"/><text x="${(x + barWidth / 2).toFixed(2)}" y="${Math.max(TOP, y - 6).toFixed(2)}" text-anchor="middle">${format(value)}</text>`;
 })).join("");
 const labels = options.labels.map((label, index) => `<text x="${(LEFT + (index + 0.5) * groupWidth).toFixed(2)}" y="493" text-anchor="middle">${escapeText(label)}</text>`).join("");
 const legend = options.series.map((series, index) => `<rect x="${RIGHT - 155}" y="${58 + index * 22}" width="14" height="14" fill="${escapeAttribute(series.color)}"/><text x="${RIGHT - 133}" y="${70 + index * 22}">${escapeText(series.name)}</text>`).join("");
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-labelledby="chart-title chart-description"><title id="chart-title">${escapeText(options.title)}</title><desc id="chart-description">Bar chart with ${options.series.length} data series.</desc><style>text{font:14px system-ui,sans-serif;fill:#24313f}.title{font-size:24px;font-weight:700}.axis{stroke:#52606d;stroke-width:2}</style><rect width="100%" height="100%" fill="#fff"/><text class="title" x="${WIDTH / 2}" y="35" text-anchor="middle">${escapeText(options.title)}</text><line class="axis" x1="${LEFT}" y1="${BOTTOM}" x2="${RIGHT}" y2="${BOTTOM}"/><line class="axis" x1="${LEFT}" y1="${TOP}" x2="${LEFT}" y2="${BOTTOM}"/><text x="${(LEFT + RIGHT) / 2}" y="530" text-anchor="middle">${escapeText(options.xLabel)}</text><text x="22" y="${(TOP + BOTTOM) / 2}" text-anchor="middle" transform="rotate(-90 22 ${(TOP + BOTTOM) / 2})">${escapeText(options.yLabel)}</text>${bars}${labels}${legend}</svg>`;
}

function escapeText(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function escapeAttribute(value: string): string {
  return escapeText(value).replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function format(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
