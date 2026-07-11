<<<<<<< HEAD
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
=======
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
        games_per_generation: 5,
        games_completed: 2,
        games_failed: 1,
        current_generation_game_index: 3,
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
      games_per_generation: 5,
      games_completed: 2,
      games_failed: 1,
      current_generation_game_index: 3,
      generation_statistics: [{ generation: 1, best_fitness: 10, average_fitness: 7 }],
      progress_tooltip: "Generation 2 • 3 remaining • Game 3/5 • 1 failed • Game g_1 • Best fitness 10",
    }]);
  });

  it("passes explicit games-per-generation settings when starting training", async () => {
    jest.spyOn(ResearchService, "fetchGameList").mockResolvedValue([]);
    jest.spyOn(ResearchService, "fetchTrainingBatchList").mockResolvedValue([]);
    jest.spyOn(ResearchService, "subscribeToTrainingSessions").mockReturnValue(() => undefined);
    const startTraining = jest.spyOn(ResearchService, "startTrainingLoop").mockResolvedValue();

    const view = createView();
    const presenter = new ResearchPresenter(view);
    await flushPromises();

    await presenter.handleStartTraining({
      ruleset: "default",
      botCount: 5,
      generations: 10,
      gamesPerGeneration: 5,
      baseGenome: "random",
      botModel: "GOAPGenetic",
      mutationStrength: 0.25,
      mutationRate: 0.15,
      randomImmigrantCount: 1,
    });

    expect(startTraining).toHaveBeenCalledWith(expect.objectContaining({
      gamesPerGeneration: 5,
      mutationStrength: 0.25,
      mutationRate: 0.15,
      randomImmigrantCount: 1,
    }));
  });
});
>>>>>>> 5aae65484608285345edeb4ee838d500ef4f5a69
