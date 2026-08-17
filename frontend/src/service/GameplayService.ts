import {
  GameStateDTO,
  GameActionPayload,
  ChatMessageDTO
} from "../dtos";

export type ConnectionState = "CONNECTING" | "CONNECTED" | "DISCONNECTED" | "RECONNECTING";
export interface GameNotification {
  level?: "info" | "warning" | "error";
  message: string;
  reason?: string;
  development_id?: string;
}

export class GameplayService {
  private socket: WebSocket | null = null;
  private isIntentionalDisconnect = false;
  private onConnectedCallback?: () => void;

  // The Watchdog & Backoff Parameters
  private watchdogTimer: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private lastConnectAttempt = 0;
  private readonly maxReconnectDelay = 30000;

  // Callbacks
  private _onConnectionStateChange?: (state: ConnectionState) => void;
  private _onChatHistory?: (messages: ChatMessageDTO[]) => void;
  private _onNewChatMessage?: (message: ChatMessageDTO) => void;
  private _onGameState?: (state: GameStateDTO) => void;
  private _onPlayerCount?: (count: number) => void;
  private _onGameStarted?: () => void;
  private _onError?: (message: string) => void;
  private _onNotification?: (notification: GameNotification) => void;

  constructor() { }

  public connect(onConnected: () => void) {
    this.onConnectedCallback = onConnected;
    this.isIntentionalDisconnect = false;
    this.reconnectAttempts = 0;

    this.establishConnection();

    // Start the Watchdog Heartbeat (Checks every 2 seconds)
    if (!this.watchdogTimer) {
      this.watchdogTimer = setInterval(() => this.healthCheck(), 2000);
    }
  }
  private healthCheck() {
    if (this.isIntentionalDisconnect) return;

    const now = Date.now();

    // NEW: The "Proxy Hang" Trap Fix
    // If the socket is stuck connecting for more than 5 seconds, the proxy hung. Kill it.
    if (this.socket && this.socket.readyState === WebSocket.CONNECTING) {
      if (now - this.lastConnectAttempt > 5000) {
        console.warn("⚠️ WebSocket stuck in CONNECTING. Proxy hung. Forcing reconnect...");
        this.socket.close(); // This kills the hung socket
        this.establishConnection(); // Force a fresh request
      }
      return; // Give it 5 seconds to try and connect naturally
    }

    // If the socket is alive and fully open, do nothing.
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return;
    }

    // If the socket is dead, calculate the exponential backoff
    const backoffDelay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), this.maxReconnectDelay);

    // Only attempt to reconnect if enough time has passed since the last attempt
    if (now - this.lastConnectAttempt > backoffDelay) {
      console.log(`🐕 Watchdog detected dead socket. Initiating recovery (Attempt ${this.reconnectAttempts + 1})...`);
      this.reconnectAttempts++;
      this.establishConnection();
    }
  }

  private establishConnection() {
    if (this.socket) {
      this.socket.close();
    }

    this.lastConnectAttempt = Date.now();
    const state = this.reconnectAttempts > 0 ? "RECONNECTING" : "CONNECTING";
    this.updateConnectionState(state);

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    this.socket = new WebSocket(`${protocol}//${host}/ws`);

    this.setupListeners();
  }

  private setupListeners() {
    if (!this.socket) return;

    this.socket.onopen = () => {
      console.log("🔌 WebSocket Connected");
      this.reconnectAttempts = 0; // Reset backoff on success
      this.updateConnectionState("CONNECTED");
      this.onConnectedCallback?.(); // Re-send the JOIN_ROOM packet
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
        case "game_notification":
          this._onNotification?.(payload.data);
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
      this.updateConnectionState("DISCONNECTED");
      // We no longer rely on setTimeout here. The Watchdog will catch it on its next cycle.
    };
  }

  private updateConnectionState(state: ConnectionState) {
    this._onConnectionStateChange?.(state);
  }

  public setOnConnectionStateChange(callback: (state: ConnectionState) => void) { this._onConnectionStateChange = callback; }
  public setOnChatHistory(callback: (messages: ChatMessageDTO[]) => void) { this._onChatHistory = callback; }
  public setOnNewChatMessage(callback: (message: ChatMessageDTO) => void) { this._onNewChatMessage = callback; }
  public setOnGameState(callback: (state: GameStateDTO) => void) { this._onGameState = callback; }
  public setOnPlayerCount(callback: (count: number) => void) { this._onPlayerCount = callback; }
  public setOnGameStarted(callback: () => void) { this._onGameStarted = callback; }
  public setOnError(callback: (message: string) => void) { this._onError = callback; }
  public setOnNotification(callback: (notification: GameNotification) => void) { this._onNotification = callback; }

  private emit(eventName: string, data: any) {
    const payload = JSON.stringify({ event: eventName, data: data });
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(payload);
    }
  }

  public joinRoom(gameId: string, userId: string) { this.emit("join_room", { gameId, userId }); }
  public startGame(gameId: string, userId: string) { this.emit("start_game_request", { gameId, userId }); }
  public createChat(gameId: string, userId: string, name: string, memberIds: string[]) { this.emit("create_chat", { gameId, userId, name, memberIds }); }
  public requestUpdate(gameId: string, userId: string) { this.emit("request_update", { gameId, userId }); }
  public sendChat(gameId: string, userId: string, content: string, toId: string) { this.emit("send_chat", { gameId, userId, content, to_id: toId }); }
  public submitAction(payload: GameActionPayload) { this.emit("submit_action", payload); }

  public destroy() {
    this.isIntentionalDisconnect = true;
    if (this.watchdogTimer) {
      clearInterval(this.watchdogTimer);
      this.watchdogTimer = null;
    }
    if (this.socket) this.socket.close();
  }
}
