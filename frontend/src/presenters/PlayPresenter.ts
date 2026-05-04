import { Presenter } from "./Presenter";
import { View } from "./View";
import { JoinableGameDTO } from "../../../dtos";
import { UserService } from "../service/UserService";

export interface PlayView extends View {
  setJoinableGames(games: JoinableGameDTO[]): void;
  setHasConsented(hasConsented: boolean): void;
  navigateToGame(gameId: string): void;
  showAlert(message: string): void;
}

export class PlayPresenter extends Presenter<PlayView> {
  private userService: UserService;
  private gamesRefreshTimer: NodeJS.Timeout | null = null;

  constructor(view: PlayView) {
    super(view);
    this.userService = new UserService();
  }

  public async handleConsent(is18Plus: boolean) {
    if (is18Plus) {
      const consented = await this.userService.consent();
      if (consented) {
        this._view.setHasConsented(true);
        this.startFetchingGames();
      } else {
        this._view.showAlert("Server rejected consent request");
      }
    } else {
      this._view.showAlert("You must be 18 or older to participate.");
    }
  }

  public startFetchingGames() {
    this.fetchGames();
    this.gamesRefreshTimer = setInterval(() => this.fetchGames(), 10000);
  }

  public stopFetchingGames() {
    if (this.gamesRefreshTimer) {
      clearInterval(this.gamesRefreshTimer);
    }
  }

  private async fetchGames() {
    const activeGamesDTO = await this.userService.getActiveGames();
    this._view.setJoinableGames(activeGamesDTO.games);
  }

  public async startNewGame() {
    const newGame = await this.userService.newGame();
    if (newGame) {
      this._view.navigateToGame(newGame.gameId);
    }
  }

  public async joinGame(gameId: string) {
    const joinedGame = await this.userService.joinGame(gameId);
    if (joinedGame) {
      this._view.navigateToGame(joinedGame.gameId);
    }
  }

  public destroy() {
    this.stopFetchingGames();
  }
}
