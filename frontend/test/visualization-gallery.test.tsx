import { fireEvent, render, screen, within } from "@testing-library/react";
import { VisualizationGallery } from "../src/components/research/VisualizationGallery";
import { ResearchVisualizationDTO } from "../src/dtos";

const visualization: ResearchVisualizationDTO = {
  id: "42",
  scope_type: "game",
  scope_id: "g_1",
  name: "inventory_over_time",
  title: "Inventory Over Time",
  mime_type: "image/png",
  url: "/api/research/visualizations/42",
  metadata: {},
  created_at: "2026-06-26T00:00:00",
};

describe("VisualizationGallery", () => {
  it("opens a larger modal when a visualization is clicked", () => {
    render(<VisualizationGallery visualizations={[visualization]} />);

    fireEvent.click(screen.getByRole("button", { name: /open inventory over time/i }));

    const dialog = screen.getByRole("dialog", { name: /inventory over time/i });
    expect(dialog).not.toBeNull();
    expect(within(dialog).getByAltText("Inventory Over Time").getAttribute("src"))
      .toBe("/api/research/visualizations/42");
  });

  it("provides a download link for the selected visualization", () => {
    render(<VisualizationGallery visualizations={[visualization]} />);

    fireEvent.click(screen.getByRole("button", { name: /open inventory over time/i }));

    const dialog = screen.getByRole("dialog", { name: /inventory over time/i });
    const download = within(dialog).getByRole("link", { name: /download image/i });
    expect(download.getAttribute("href")).toBe("/api/research/visualizations/42");
    expect(download.getAttribute("download")).toBe("inventory_over_time.png");
  });
});
