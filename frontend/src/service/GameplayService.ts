import {
  GameStateDTO,
  GameActionPayload,
  ChatMessageDTO
} from "../../../dtos";

export class GameplayService {

  private socket: WebSocket | null = null;
  private isIntentionalDisconnect = false;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private onConnectedCallback?: () => void;

  // --------------------------------------------------------
  // Callback references
  // --------------------------------------------------------

  private _onChatHistory?: (messages: ChatMessageDTO[]) => void;
  private _onNewChatMessage?: (message: ChatMessageDTO) => void;
  private _onGameState?: (state: GameStateDTO) => void;
  private _onPlayerCount?: (count: number) => void;
  private _onGameStarted?: () => void;
  private _onError?: (message: string) => void;

  constructor() { }

  // --------------------------------------------------------
  // CONNECTION LOGIC
  // --------------------------------------------------------

  public connect(onConnected: () => void) {
    this.onConnectedCallback = onConnected;
    this.isIntentionalDisconnect = false;
    this.establishConnection();
  }

  private establishConnection() {
    // Clean up any existing socket before making a new one
    if (this.socket) {
      this.socket.close();
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;

    this.socket = new WebSocket(`${protocol}//${host}/ws`);
    this.setupListeners();
  }

  // --------------------------------------------------------
  // LISTENERS
  // --------------------------------------------------------

  private setupListeners() {
    if (!this.socket) return;

    this.socket.onopen = () => {
      console.log("🔌 WebSocket Connected");
      // Fire the callback every time we (re)connect so we always join the room
      this.onConnectedCallback?.();
    };

    this.socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);

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
      console.error("WS Error:", error);
    };

    this.socket.onclose = () => {
      console.log("❌ WebSocket Closed");

      // Automatic Reconnection Logic
      if (!this.isIntentionalDisconnect) {
        console.log("♻️ Attempting to reconnect in 2 seconds...");
        this.reconnectTimer = setTimeout(() => {
          this.establishConnection();
        }, 2000);
      }
    };
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

    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(payload);
    } else {
      console.warn(`WebSocket not open. Dropping ${eventName}`);
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

  public createChat(
    gameId: string,
    userId: string,
    name: string,
    memberIds: string[]
  ) {
    this.emit("create_chat", {
      gameId,
      userId,
      name,
      memberIds
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
    this.isIntentionalDisconnect = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.socket) this.socket.close();
  }
}
