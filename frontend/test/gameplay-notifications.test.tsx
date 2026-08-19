import { render, screen } from "@testing-library/react";
import ConnectionBanner from "../src/components/gameplay/layout/ConnectionBanner";
import ToastStack from "../src/components/gameplay/layout/ToastStack";

describe("gameplay notifications", () => {
  it("hides the connection banner once connected", () => {
    const { rerender } = render(<ConnectionBanner state="CONNECTING" />);
    expect(screen.getByRole("status").textContent).toContain("Negotiating connection");

    rerender(<ConnectionBanner state="CONNECTED" />);
    expect(screen.queryByText(/Negotiating connection/)).toBeNull();
  });

  it("renders queued toast messages", () => {
    render(<ToastStack toasts={[{ id: 1, level: "warning", message: "Choose again" }]} />);
    expect(screen.getByRole("status").textContent).toContain("Choose again");
  });
});
