import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NewGameModal } from "../src/components/NewGameModal";

describe("NewGameModal training settings", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ genomes: [], models: ["GOAPGenetic"] }),
    }) as jest.Mock;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("submits mutation and random immigrant settings in training mode", async () => {
    const onSubmit = jest.fn();

    render(
      <NewGameModal
        isOpen
        onClose={jest.fn()}
        onSubmit={onSubmit}
        gameOptions={{ default: {} }}
        isTrainingMode
      />,
    );

    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith("/api/research/genomes"));

    const spinButtons = screen.getAllByRole("spinbutton");
    fireEvent.change(spinButtons[3], { target: { value: "0.4" } });
    fireEvent.change(spinButtons[4], { target: { value: "0.2" } });
    fireEvent.change(spinButtons[5], { target: { value: "2" } });

    fireEvent.click(screen.getByRole("button", { name: /start training/i }));

    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
      mutationStrength: 0.4,
      mutationRate: 0.2,
      randomImmigrantCount: 2,
    }));
  });
});
