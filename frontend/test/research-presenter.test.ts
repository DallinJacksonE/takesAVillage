import { ResearchPresenter, ResearchView } from "../src/presenters/ResearchPresenter";
import { ResearchService } from "../src/service/ResearchService";
import {
  ResearchGameDetailDTO,
  ResearchGameListItemDTO,
  TrainingBatchDetailDTO,
  TrainingBatchListItemDTO,
  TrainingSessionsDTO,
} from "../src/dtos";

function flushPromises() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

function createView(): ResearchView & { calls: Record<string, unknown[]> } {
  const calls: Record<string, unknown[]> = {};
  const record = (name: string) => (value: unknown) => {
    calls[name] = [...(calls[name] ?? []), value];
  };
  return {
    calls,
    setIsLoggedIn: record("isLoggedIn"),
    setGames: record("games"),
    setTrainingBatches: record("trainingBatches"),
    setSelectedGame: record("selectedGame"),
    setSelectedTrainingBatch: record("selectedTrainingBatch"),
    setActiveTab: record("activeTab"),
    setSearchQuery: record("searchQuery"),
    setSortMode: record("sortMode"),
    setIsLoading: record("isLoading"),
    setStatusMessage: record("statusMessage"),
    setErrorMessage: record("errorMessage"),
    setTrainingOptions: record("trainingOptions"),
    setIsTrainingModalOpen: record("isTrainingModalOpen"),
  };
}

describe("ResearchPresenter", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("loads game and training batch lists on startup", async () => {
    const games: ResearchGameListItemDTO[] = [{
      game_id: "g_1",
      day_num: 2,
      phase: "NIGHT",
      created_at: "2026-01-01T00:00:00",
      game_type: "training",
    }];
    const batches: TrainingBatchListItemDTO[] = [{
      batch_id: "batch-1",
      status: "running",
      ruleset: "default",
    }];
    jest.spyOn(ResearchService, "fetchGameList").mockResolvedValue(games);
    jest.spyOn(ResearchService, "fetchTrainingBatchList").mockResolvedValue(batches);
    jest.spyOn(ResearchService, "subscribeToTrainingSessions").mockReturnValue(() => undefined);

    const view = createView();
    new ResearchPresenter(view);
    await flushPromises();

    expect(view.calls.games.at(-1)).toEqual(games);
    expect(view.calls.trainingBatches.at(-1)).toEqual(batches);
  });

  it("fetches details when a game or batch is selected", async () => {
    const game = {
      game_id: "g_1",
      day_num: 2,
      phase: "NIGHT",
      created_at: "2026-01-01T00:00:00",
      game_type: "training",
      visualizations: [],
      data: { map: {}, players: {} },
    } as ResearchGameDetailDTO;
    const batch = {
      batch_id: "batch-1",
      status: "running",
      visualizations: [],
    } as TrainingBatchDetailDTO;
    jest.spyOn(ResearchService, "fetchGameList").mockResolvedValue([]);
    jest.spyOn(ResearchService, "fetchTrainingBatchList").mockResolvedValue([]);
    jest.spyOn(ResearchService, "fetchGameDetail").mockResolvedValue(game);
    jest.spyOn(ResearchService, "fetchTrainingBatchDetail").mockResolvedValue(batch);
    jest.spyOn(ResearchService, "subscribeToTrainingSessions").mockReturnValue(() => undefined);

    const view = createView();
    const presenter = new ResearchPresenter(view);
    await flushPromises();

    await presenter.handleSelectGame({ game_id: "g_1" } as ResearchGameListItemDTO);
    expect(view.calls.selectedGame.at(-1)).toEqual(game);

    await presenter.handleSelectTrainingBatch({ batch_id: "batch-1" } as TrainingBatchListItemDTO);

    expect(view.calls.selectedTrainingBatch.at(-1)).toEqual(batch);
  });

  it("converts websocket training sessions into in-progress batch rows", async () => {
    let onUpdate: ((payload: TrainingSessionsDTO) => void) | undefined;
    jest.spyOn(ResearchService, "fetchGameList").mockResolvedValue([]);
    jest.spyOn(ResearchService, "fetchTrainingBatchList").mockResolvedValue([]);
    jest.spyOn(ResearchService, "subscribeToTrainingSessions").mockImplementation((handler) => {
      onUpdate = handler;
      return () => undefined;
    });

    const view = createView();
    new ResearchPresenter(view);
    await flushPromises();
    onUpdate?.({
      sessions: [{
        session_id: "session-1",
        current_game_id: "g_1",
        ruleset: "default",
        bot_count: 4,
        generation: 2,
        generations_left: 3,
        population_size: 4,
        generation_statistics: [{ generation: 1, best_fitness: 10, average_fitness: 7 }],
      }],
    });

    expect(view.calls.trainingBatches.at(-1)).toEqual([{ 
      batch_id: "session-1",
      status: "running",
      current_game_id: "g_1",
      ruleset: "default",
      bot_count: 4,
      current_generation: 2,
      total_generations: 5,
      generation_statistics: [{ generation: 1, best_fitness: 10, average_fitness: 7 }],
      progress_tooltip: "Generation 2 • 3 remaining • Game g_1 • Best fitness 10",
    }]);
  });
});
