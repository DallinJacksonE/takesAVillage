import { GameplayService } from "../src/service/GameplayService";
import { ResearchService } from "../src/service/ResearchService";
import { UserService } from "../src/service/UserService";

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSED = 3;
  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: (() => void) | null = null;
  send = jest.fn();
  close = jest.fn();
  constructor(readonly url: string) { sockets.push(this); }
}

const sockets: MockWebSocket[] = [];
const originalFetch = global.fetch;
const originalWebSocket = global.WebSocket;

beforeEach(() => {
  sockets.length = 0;
  global.WebSocket = MockWebSocket as unknown as typeof WebSocket;
});

afterEach(() => {
  global.fetch = originalFetch;
  global.WebSocket = originalWebSocket;
  jest.useRealTimers();
  jest.restoreAllMocks();
});

describe("frontend network boundary validation", () => {
  it("rejects malformed research HTTP payloads", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => [{ game_id: "missing-required-fields" }] }) as typeof fetch;
    await expect(ResearchService.fetchGameList()).rejects.toThrow();
  });

  it("returns null when consent succeeds with a malformed payload", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ message: "missing user" }) }) as typeof fetch;
    await expect(new UserService().consent()).resolves.toBeNull();
  });

  it("does not deliver malformed gameplay WebSocket packets", () => {
    jest.useFakeTimers();
    const service = new GameplayService();
    const gameState = jest.fn();
    const error = jest.fn();
    service.setOnGameState(gameState);
    service.setOnError(error);
    service.connect(jest.fn());

    sockets[0]!.onmessage?.({ data: JSON.stringify({ event: "game_state", data: { status: "ACTIVE" } }) } as MessageEvent);

    expect(gameState).not.toHaveBeenCalled();
    expect(error).toHaveBeenCalledWith("Invalid server message");
    service.destroy();
  });

  it("does not deliver malformed training WebSocket packets", () => {
    const update = jest.fn();
    const onError = jest.fn();
    const unsubscribe = ResearchService.subscribeToTrainingSessions(update, onError);

    sockets[0]!.onmessage?.({ data: JSON.stringify({ event: "training_sessions", data: { sessions: [{ session_id: 1 }] } }) } as MessageEvent);

    expect(update).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalled();
    unsubscribe();
  });
});
