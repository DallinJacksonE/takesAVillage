import { fireEvent, render, screen, within } from "@testing-library/react";
import { TrainingBatchDetail } from "../src/components/research/TrainingBatchDetail";
import { TrainingBatchDetailDTO } from "../src/dtos";

const batch: TrainingBatchDetailDTO = {
  batch_id: "batch-1",
  status: "running",
  ruleset: "default",
  current_generation: 2,
  total_generations: 5,
  games_per_generation: 2,
  games_completed: 1,
  games_failed: 1,
  generation_statistics: [],
  visualizations: [],
  games: [
    {
      game_id: "game-1",
      generation: 1,
      status: "completed",
      genome_count: 3,
      best_fitness: 12,
      average_fitness: 8.5,
      error_message: null,
    },
    {
      game_id: "game-2",
      generation: 1,
      status: "failed",
      genome_count: 0,
      best_fitness: null,
      average_fitness: null,
      error_message: "No genome entries returned",
    },
  ],
};

describe("TrainingBatchDetail", () => {
  it("groups game attempts by generation and shows attempt state", () => {
    const onSelectGame = jest.fn();

    render(<TrainingBatchDetail batch={batch} onSelectGame={onSelectGame} />);

    const table = screen.getByRole("table", { name: /training game attempts/i });
    expect(within(table).getAllByText("Generation 1")).toHaveLength(2);
    expect(within(table).getByText("completed")).not.toBeNull();
    expect(within(table).getByText("failed")).not.toBeNull();
    expect(within(table).getByText("3")).not.toBeNull();
    expect(within(table).getByText("12")).not.toBeNull();
    expect(within(table).getByText("8.5")).not.toBeNull();
    expect(within(table).getByText("No genome entries returned")).not.toBeNull();

    fireEvent.click(within(table).getByRole("button", { name: /open game game-1/i }));

    expect(onSelectGame).toHaveBeenCalledWith("game-1");
  });

  it("sorts attempts by persisted attempt index instead of response order", () => {
    const outOfOrderBatch: TrainingBatchDetailDTO = {
      ...batch,
      games: [
        { game_id: "game-3", generation: 1, attempt: 3, status: "running" },
        { game_id: "game-1", generation: 1, attempt: 1, status: "running" },
        { game_id: "game-2", generation: 1, attempt: 2, status: "running" },
      ],
    };

    render(<TrainingBatchDetail batch={outOfOrderBatch} onSelectGame={jest.fn()} />);

    const table = screen.getByRole("table", { name: /training game attempts/i });
    const rows = within(table).getAllByRole("row").slice(1);

    expect(rows.map((row) => within(row).getByRole("button").textContent)).toEqual([
      "Open game game-1",
      "Open game game-2",
      "Open game game-3",
    ]);
  });
});
