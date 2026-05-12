import { GameStateDTO } from "../../../dtos";
import { Presenter } from "./Presenter";
import { View } from "./View";
import io from "socket.io-client";

const socket = io({
  path: "/socket.io",
  transports: ["websocket", "polling"],
});

export interface GameplayView extends View {
  setGameState(gameState: GameStateDTO | null): void;
  setPlayerCount(playerCount: number): void;
  setTimeLeft(timeLeft: number): void;
  setUserId(userId: string): void;
  showAlert(message: string): void;
}

export class GameplayPresenter extends Presenter<GameplayView> {
  private gameId: string;
  private userId: string | null = null;
  private timeLeft: number = 0;
  private timer: NodeJS.Timeout | null = null;

  constructor(view: GameplayView, gameId: string) {
    super(view);
    this.gameId = gameId;
    this.init();
  }

  private init() {
    this.userId = this.getCookie("user_session") || "anon";
    this._view.setUserId(this.userId);
    socket.emit("join_room", { gameId: this.gameId, userId: this.userId });

    socket.on("room_update", (data: { player_count: number }) =>
      this._view.setPlayerCount(data.player_count)
    );

    socket.on("game_state", (data: GameStateDTO) => {
      this.timeLeft = data.time_remaining;
      this._view.setGameState(data);
      this._view.setTimeLeft(data.time_remaining);
    });

    socket.on("game_started", () =>
      socket.emit("request_update", {
        gameId: this.gameId,
        userId: this.userId,
      })
    );

    socket.on("error", (data: { message: string }) =>
      this._view.showAlert(data.message)
    );

    const timer = setInterval(() => {
      this.timeLeft = this.timeLeft > 0 ? this.timeLeft - 1 : 0;
      this._view.setTimeLeft(this.timeLeft);
    }, 1000);
    this.timer = timer;
  }

  public destroy() {
    socket.off("room_update");
    socket.off("game_state");
    socket.off("game_started");
    socket.off("error");
    if (this.timer) {
      clearInterval(this.timer);
    }
  }

  private getCookie(name: string): string | undefined {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(";").shift();
  }

  public handleStartGame() {
    socket.emit("start_game_request", {
      gameId: this.gameId,
      userId: this.userId,
    });
  }

  /**
   * Pipeline for pure social interactions.
   * Bypasses the strict game state validator on the backend.
   */
  public sendChat(content: string, toId: string = "GLOBAL") {
    if (!this.userId) return;
    socket.emit("send_chat", {
      gameId: this.gameId,
      userId: this.userId,
      content: content,
      to_id: toId,
    });
  }

  /**
   * Pipeline for Game Mechanics, Actions, and Contracts.
   * e.g., "BUILD_DEV", "COMMIT_WORK", "FINALIZE", "ACCEPT"
   */
  public submitAction(actionCommand: string, payload: any = {}) {
    console.log(actionCommand)
    console.log(payload)
    if (!this.userId) return;
    socket.emit("submit_action", {
      gameId: this.gameId,
      userId: this.userId,
      action_command: actionCommand,
      payload: payload,
    });
  }
}
