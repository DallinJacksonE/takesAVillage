import {
  GameStateDTO,
  GameActionPayload,
  ChatMessageDTO
} from "../../../dtos";

export class GameplayService {

  private socket!: WebSocket;

  // --------------------------------------------------------
  // Callback references
  // --------------------------------------------------------

  private _onChatHistory?: (messages: ChatMessageDTO[]) => void;
  private _onNewChatMessage?: (message: ChatMessageDTO) => void;
  private _onGameState?: (state: GameStateDTO) => void;
  private _onPlayerCount?: (count: number) => void;
  private _onGameStarted?: () => void;
  private _onError?: (message: string) => void;
  private isDestroyed = false;
  constructor() { }

  // --------------------------------------------------------
  // LISTENERS
  // --------------------------------------------------------

  private setupListeners() {

    this.socket.onopen = () => {
      console.log("🔌 WebSocket Connected");
    };

    this.socket.onmessage = (event) => {
      console.log("RAW MESSAGE:", event.data);

      const payload = JSON.parse(event.data);

      console.log("PARSED:", payload);

      switch (payload.event) {

        case "room_update":
          this._onPlayerCount?.(payload.data.player_count);
          break;

        case "game_state":
          this._onGameState?.(payload.data);
          break;

        case "game_started":
          this._onGameStarted?.();
          break;

        case "chat_history":
          this._onChatHistory?.(payload.data);
          break;

        case "new_chat_message":
          this._onNewChatMessage?.(payload.data);
          break;

        case "error":
          this._onError?.(payload.data.message);
          break;

        default:
          console.warn("Unknown WS event:", payload.event);
      }
    };

    this.socket.onerror = (error) => {
      console.error(error);
    };

    this.socket.onclose = () => {
      console.log("❌ WebSocket Closed");
    };
  }

  // --------------------------------------------------------
  // CALLBACK SETTERS
  // --------------------------------------------------------
  public connect() {
    const protocol =
      window.location.protocol === "https:" ? "wss:" : "ws:";

    const host = window.location.host;

    this.socket = new WebSocket(`${protocol}//${host}/ws`);
    this.setupListeners();
  }
  public setOnChatHistory(
    callback: (messages: ChatMessageDTO[]) => void
  ) {
    this._onChatHistory = callback;
  }

  public setOnNewChatMessage(
    callback: (message: ChatMessageDTO) => void
  ) {
    this._onNewChatMessage = callback;
  }

  public setOnGameState(
    callback: (state: GameStateDTO) => void
  ) {
    this._onGameState = callback;
  }

  public setOnPlayerCount(
    callback: (count: number) => void
  ) {
    this._onPlayerCount = callback;
  }

  public setOnGameStarted(
    callback: () => void
  ) {
    this._onGameStarted = callback;
  }

  public setOnError(
    callback: (message: string) => void
  ) {
    this._onError = callback;
  }

  // --------------------------------------------------------
  // EMIT WRAPPER
  // --------------------------------------------------------

  private emit(eventName: string, data: any) {
    const payload = JSON.stringify({
      event: eventName,
      data: data
    });

    if (this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(payload);
    } else if (this.socket.readyState === WebSocket.CONNECTING) {
      this.socket.addEventListener(
        "open",
        () => {
          // Prevent ghost emissions if the service was destroyed while waiting
          if (!this.isDestroyed) {
            this.socket.send(payload);
          }
        },
        { once: true }
      );
    } else {
      console.warn(`WebSocket closed. Dropping ${eventName}`);
    }
  }

  // --------------------------------------------------------
  // OUTGOING EVENTS
  // --------------------------------------------------------

  public joinRoom(
    gameId: string,
    userId: string
  ) {

    this.emit("join_room", {
      gameId,
      userId
    });
  }

  public startGame(
    gameId: string,
    userId: string
  ) {

    this.emit("start_game_request", {
      gameId,
      userId
    });
  }

  public requestUpdate(
    gameId: string,
    userId: string
  ) {

    this.emit("request_update", {
      gameId,
      userId
    });
  }

  public sendChat(
    gameId: string,
    userId: string,
    content: string,
    toId: string
  ) {

    this.emit("send_chat", {
      gameId,
      userId,
      content,
      to_id: toId
    });
  }

  public submitAction(
    payload: GameActionPayload
  ) {

    this.emit(
      "submit_action",
      payload
    );
  }

  // --------------------------------------------------------
  // CLEANUP
  // --------------------------------------------------------

  public destroy() {
    this.isDestroyed = true;
    this.socket.close();
  }
}
