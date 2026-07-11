import { render, screen } from "@testing-library/react";
import { TrainingProgressBadge } from "../src/components/research/TrainingProgressBadge";
import { ResearchTrainingBatchRow } from "../src/presenters/ResearchPresenter";

describe("TrainingProgressBadge", () => {
  it("surfaces stalled training sessions with their last error", () => {
    const batch: ResearchTrainingBatchRow = {
      batch_id: "batch-1",
      status: "stalled",
      last_error: "Training batch is running in persistence but not active",
    };

    render(<TrainingProgressBadge batch={batch} />);

    const badge = screen.getByText("Stalled");
    expect(badge.getAttribute("title")).toBe("Training batch is running in persistence but not active");
  });
});
