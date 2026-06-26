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

  it("fetches game lists with search and sort query parameters", async () => {
    const fetchMock = jest.fn(() => mockJsonResponse([{ game_id: "g_1" }]));
    global.fetch = fetchMock as typeof fetch;

    const games = await ResearchService.fetchGameList("training", "name_asc");

    expect(games).toEqual([{ game_id: "g_1" }]);
    expect(fetchMock).toHaveBeenCalledWith("/api/research/games?search=training&sort=name_asc");
  });

  it("fetches game and training batch details from detail endpoints", async () => {
    const fetchMock = jest
      .fn()
      .mockImplementationOnce(() => mockJsonResponse({ game_id: "g_1", visualizations: [] }))
      .mockImplementationOnce(() => mockJsonResponse({ batch_id: "batch-1", visualizations: [] }));
    global.fetch = fetchMock as typeof fetch;

    const game = await ResearchService.fetchGameDetail("g_1");
    const batch = await ResearchService.fetchTrainingBatchDetail("batch-1");

    expect(game.game_id).toBe("g_1");
    expect(batch.batch_id).toBe("batch-1");
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/research/games/g_1");
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/research/training-batches/batch-1");
  });

  it("starts training loops through the research service", async () => {
    const fetchMock = jest.fn(() => mockJsonResponse({ message: "Training sequence initiated" }));
    global.fetch = fetchMock as typeof fetch;

    await ResearchService.startTrainingLoop({ ruleset: "default", botCount: 4 });

    expect(fetchMock).toHaveBeenCalledWith("/api/research/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ruleset: "default", botCount: 4 }),
    });
  });
});
