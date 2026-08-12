import { ResearchService } from "../src/service/ResearchService";

describe("ResearchService", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  function mockJsonResponse(body: unknown) {
    return Promise.resolve({
      ok: true,
      json: async () => body,
    } as Response);
  }

  const game = {
    game_id: "g_1",
    day_num: 2,
    phase: "NIGHT",
    created_at: "2026-08-11T00:00:00.000Z",
    game_type: "training" as const,
  };

  it("fetches game lists with search and sort query parameters", async () => {
    const fetchMock = jest.fn(() => mockJsonResponse([game]));
    global.fetch = fetchMock as typeof fetch;

    const games = await ResearchService.fetchGameList("training", "name_asc");

    expect(games).toEqual([game]);
    expect(fetchMock).toHaveBeenCalledWith("/api/research/games?search=training&sort=name_asc");
  });

  it("fetches game and training batch details from detail endpoints", async () => {
    const fetchMock = jest
      .fn()
      .mockImplementationOnce(() => mockJsonResponse({ ...game, data: { map: {}, players: {} }, visualizations: [] }))
      .mockImplementationOnce(() => mockJsonResponse({ batch_id: "batch-1", status: "completed", visualizations: [] }));
    global.fetch = fetchMock as typeof fetch;

    const gameDetail = await ResearchService.fetchGameDetail("g_1");
    const batch = await ResearchService.fetchTrainingBatchDetail("batch-1");

    expect(gameDetail.game_id).toBe("g_1");
    expect(batch.batch_id).toBe("batch-1");
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/research/games/g_1");
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/research/training-batches/batch-1");
  });

  it("starts training loops through the research service", async () => {
    const fetchMock = jest.fn(() => mockJsonResponse({ message: "Training sequence initiated" }));
    global.fetch = fetchMock as typeof fetch;

    const request = {
      ruleset: "standard",
      botCount: 3,
      generations: 2,
      baseGenome: "random",
      botModel: "genetic",
      mutationStrength: 0.1,
      mutationRate: 0.2,
      randomImmigrantCount: 1,
      gamesPerGeneration: 1,
    };
    await ResearchService.startTrainingLoop(request);

    expect(fetchMock).toHaveBeenCalledWith("/api/research/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
  });

  it("sends operator control requests for cancelling and rerunning training batches", async () => {
    const fetchMock = jest
      .fn()
      .mockImplementationOnce(() => mockJsonResponse({ message: "cancelled" }))
      .mockImplementationOnce(() => mockJsonResponse({ message: "rerun" }));
    global.fetch = fetchMock as typeof fetch;

    await ResearchService.cancelTrainingBatch("batch-1", "operator stop");
    await ResearchService.rerunTrainingBatch("batch-1");

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/research/training-batches/batch-1/cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: "operator stop" }),
    });
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/research/training-batches/batch-1/rerun", {
      method: "POST",
    });
  });
});
