import { Presenter } from "./Presenter";
import { View } from "./View";
import { JoinableGameDTO } from "../../../dtos";
import { UserService } from "../service/UserService";

export interface PlayView extends View {
  setJoinableGames(games: JoinableGameDTO[]): void;
  setHasConsented(hasConsented: boolean): void;
  navigateToGame(gameId: string): void;
  showAlert(message: string): void;
  // New UI controls for the modal
  showNewGameModal(options: Record<string, Record<string, any>>): void;
  hideNewGameModal(): void;
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

  // Updated to trigger the modal sequence
  public async getNewGameOptions() {
    const response = await this.userService.newGameOptions();
    if (response && response.options) {
      this._view.showNewGameModal(response.options);
    } else {
      this._view.showAlert("Failed to load game rulesets from the server.");
    }
  }

  // Updated to take the modal's configuration parameters
  public async startNewGame(ruleset: string, botCount: number) {
    const newGame = await this.userService.newGame(ruleset, botCount);
    if (newGame) {
      this._view.hideNewGameModal();
      this._view.navigateToGame(newGame.gameId);
    } else {
      this._view.showAlert("Failed to start the game.");
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
