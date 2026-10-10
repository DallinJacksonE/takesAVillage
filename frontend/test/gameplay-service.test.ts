import { GameplayService } from "../src/service/GameplayService";

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static instances: MockWebSocket[] = [];

  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(_url: string) {
    MockWebSocket.instances.push(this);
  }

  close() {}
  send(_payload: string) {}

  receive(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent);
  }
}

describe("GameplayService", () => {
  const originalWebSocket = global.WebSocket;

  beforeEach(() => {
    MockWebSocket.instances = [];
    global.WebSocket = MockWebSocket as unknown as typeof WebSocket;
  });

  afterEach(() => {
    global.WebSocket = originalWebSocket;
    jest.restoreAllMocks();
  });

  it("ignores game state snapshots older than the latest applied revision", () => {
    const service = new GameplayService();
    const received: number[] = [];
    service.setOnGameState((state) => received.push(state.state_revision));
    service.connect(() => undefined);
    const socket = MockWebSocket.instances[0];

    socket.receive({ event: "game_state", data: { state_revision: 2 } });
    socket.receive({ event: "game_state", data: { state_revision: 1 } });

    expect(received).toEqual([2]);
    service.destroy();
  });

  it("routes game-rule action rejections to an error toast instead of an alert", () => {
    const service = new GameplayService();
    const onError = jest.fn();
    const onNotification = jest.fn();
    service.setOnError(onError);
    service.setOnNotification(onNotification);
    service.connect(() => undefined);
    const socket = MockWebSocket.instances[0];

    socket.receive({
      event: "error",
      data: { message: "Action rejected by game rules.", action_command: "BUILD_DEV" },
    });

    expect(onNotification).toHaveBeenCalledWith({
      level: "error",
      message: "Action rejected by game rules.",
    });
    expect(onError).not.toHaveBeenCalled();
    service.destroy();
  });
});
