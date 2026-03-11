import { View } from "./View";

interface ResearchGame {
  id: number;
  date: string;
  rounds: number;
  survivors: number;
  resource_total: number;
}

export interface ResearchView extends View {
  setIsLoggedIn(isLoggedIn: boolean): void;
  setSelectedGame(selectedGame: ResearchGame | null): void;
  setGames(games: ResearchGame[]): void;
}

export class ResearchPresenter extends Presenter<ResearchView> {
  private games: ResearchGame[] = [
    { id: 1, date: '2025-04-10', rounds: 45, survivors: 2, resource_total: 500 },
    { id: 2, date: '2025-04-11', rounds: 12, survivors: 0, resource_total: 120 },
    { id: 3, date: '2025-04-12', rounds: 88, survivors: 8, resource_total: 1200 },
  ];

  constructor(view: ResearchView) {
    super(view);
    this._view.setGames(this.games);
  }

  public handleLogin() {
    // In a real application, you would have authentication logic here.
    this._view.setIsLoggedIn(true);
  }

  public handleSelectGame(game: ResearchGame) {
    this._view.setSelectedGame(game);
  }
}
