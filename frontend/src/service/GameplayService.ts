import { GameStateDTO, GameActionPayload } from "../../../dtos";

export class GameplayService {
  private socket: WebSocket;

  // Callback references
  private _onGameState?: (state: GameStateDTO) => void;
  private _onPlayerCount?: (count: number) => void;
  private _onGameStarted?: () => void;
  private _onError?: (message: string) => void;

  constructor() {
    // Dynamically grab the frontend's current protocol and host (e.g., localhost:5173)
    // This routes the WS handshake perfectly through the Vite proxy with cookies attached
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;

    this.socket = new WebSocket(`${protocol}//${host}/ws`);

    this.setupListeners();
  }

  /**
   * Binds the incoming socket events to our internal callback references.
   */
  private setupListeners() {
    this.socket.onopen = () => {
      console.log("🔌 Native WebSocket Connected!");
    };

    this.socket.onmessage = (event) => {
      // Parse the raw string from FastAPI back into a JSON object
      const payload = JSON.parse(event.data);

      // Route the data based on the 'event' key we established in the backend
      switch (payload.event) {
        case "room_update":
          if (this._onPlayerCount) this._onPlayerCount(payload.data.player_count);
          break;
        case "game_state":
          if (this._onGameState) this._onGameState(payload.data);
          break;
        case "game_started":
          if (this._onGameStarted) this._onGameStarted();
          break;
        case "error":
          if (this._onError) this._onError(payload.data.message);
          break;
        default:
          console.warn("Unknown WebSocket event received:", payload.event);
      }
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket Error:", error);
    };
  }

  // --------------------------------------------------------
  // Callback Setters (Used by the Presenter to hook into UI)
  // --------------------------------------------------------

  public setOnGameState(callback: (state: GameStateDTO) => void) {
    this._onGameState = callback;
  }

  public setOnPlayerCount(callback: (count: number) => void) {
    this._onPlayerCount = callback;
  }

  public setOnGameStarted(callback: () => void) {
    this._onGameStarted = callback;
  }

  public setOnError(callback: (message: string) => void) {
    this._onError = callback;
  }

  // --------------------------------------------------------
  // Outgoing Emits (Native JSON Wrapper)
  // --------------------------------------------------------

  /**
   * Emulates the old Socket.io emit behavior by packaging the event name
   * and data into a single stringified JSON payload.
   */
  private emit(eventName: string, data: any) {
    const payload = JSON.stringify({ event: eventName, data: data });

    if (this.socket.readyState === WebSocket.OPEN) {
      // Send immediately if the pipe is ready
      this.socket.send(payload);
    } else if (this.socket.readyState === WebSocket.CONNECTING) {
      // If still handshaking, queue the message to fire the exact millisecond it opens
      this.socket.addEventListener("open", () => {
        this.socket.send(payload);
      });
    } else {
      console.warn(`WebSocket is closed. Dropping event: ${eventName}`);
    }
  }

  public joinRoom(gameId: string, userId: string) {
    // Because emit is now globally protected from race conditions, 
    // we can safely fire this directly!
    this.emit("join_room", { gameId, userId });
  }

  public startGame(gameId: string, userId: string) {
    this.emit("start_game_request", { gameId, userId });
  }

  public requestUpdate(gameId: string, userId: string) {
    this.emit("request_update", { gameId, userId });
  }

  public sendChat(gameId: string, userId: string, content: string, toId: string) {
    this.emit("send_chat", {
      gameId,
      userId,
      content,
      to_id: toId,
    });
  }

  /**
   * The standardized envelope dispatcher.
   */
  public submitAction(payload: GameActionPayload) {
    this.emit("submit_action", payload);
  }

  // --------------------------------------------------------
  // Cleanup
  // --------------------------------------------------------

  public destroy() {
    this.socket.close(); // Cleanly close the native connection
  }
}
