//Where the websocket connection with the backend should be defined with base functionality for the presenter to use to build gameplay functionality
//
import { io, Socket } from "socket.io-client";
import { GameStateDTO, GameActionPayload } from "../../../dtos";

export class GameplayService {
  private socket: Socket;

  // Callback references
  private _onGameState?: (state: GameStateDTO) => void;
  private _onPlayerCount?: (count: number) => void;
  private _onGameStarted?: () => void;
  private _onError?: (message: string) => void;

  constructor() {
    // Instantiate a new socket connection per game session
    this.socket = io({
      path: "/socket.io",
      transports: ["websocket", "polling"],
    });

    this.setupListeners();
  }

  /**
   * Binds the incoming socket events to our internal callback references.
   */
  private setupListeners() {
    this.socket.on("room_update", (data: { player_count: number }) => {
      if (this._onPlayerCount) this._onPlayerCount(data.player_count);
    });

    this.socket.on("game_state", (data: GameStateDTO) => {
      if (this._onGameState) this._onGameState(data);
    });

    this.socket.on("game_started", () => {
      if (this._onGameStarted) this._onGameStarted();
    });

    this.socket.on("error", (data: { message: string }) => {
      if (this._onError) this._onError(data.message);
    });
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
  // Outgoing Emits
  // --------------------------------------------------------

  public joinRoom(gameId: string, userId: string) {
    this.socket.emit("join_room", { gameId, userId });
  }

  public startGame(gameId: string, userId: string) {
    this.socket.emit("start_game_request", { gameId, userId });
  }

  public requestUpdate(gameId: string, userId: string) {
    this.socket.emit("request_update", { gameId, userId });
  }

  public sendChat(gameId: string, userId: string, content: string, toId: string) {
    this.socket.emit("send_chat", {
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
    this.socket.emit("submit_action", payload);
  }

  // --------------------------------------------------------
  // Cleanup
  // --------------------------------------------------------

  public destroy() {
    this.socket.off("room_update");
    this.socket.off("game_state");
    this.socket.off("game_started");
    this.socket.off("error");
    this.socket.disconnect(); // Fully sever the connection
  }
}
