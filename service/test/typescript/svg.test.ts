import { describe, expect, it } from "vitest";

import { renderLineChart } from "../../src/research/svg.js";

describe("SVG research visualizations", () => {
  it("renders accessible, scalable SVG without embedded raster data", () => {
    const svg = renderLineChart({
      title: "Inventory Over Time",
      xLabel: "Day",
      yLabel: "Resources",
      series: [
        { name: "wood", color: "#8b5e3c", points: [{ x: 1, y: 4 }, { x: 2, y: 7 }] },
        { name: "food", color: "#4f8a3d", points: [{ x: 1, y: 3 }, { x: 2, y: 2 }] },
      ],
    });

    expect(svg).toMatch(/^<svg[^>]+viewBox="0 0 960 540"/);
    expect(svg).toContain('<title id="chart-title">Inventory Over Time</title>');
    expect(svg).toContain("<polyline");
    expect(svg).not.toContain("data:image/");
    expect(svg).not.toContain("<script");
  });

  it("escapes user-visible labels", () => {
    const svg = renderLineChart({
      title: "<unsafe & title>",
      xLabel: "x",
      yLabel: "y",
      series: [],
    });
    expect(svg).toContain("&lt;unsafe &amp; title&gt;");
    expect(svg).not.toContain("<unsafe");
  });
});
