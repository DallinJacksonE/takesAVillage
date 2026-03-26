import { ResearchService } from "../service/ResearchService";
import { ResearchGameDTO } from "../../../dtos";
import { Presenter } from "./Presenter";
import { View } from "./View";

export interface ResearchView extends View {
	setIsLoggedIn(isLoggedIn: boolean): void;
	setSelectedGame(selectedGame: ResearchGameDTO | null): void;
	setGames(games: ResearchGameDTO[]): void;
}

export class ResearchPresenter extends Presenter<ResearchView> {
	constructor(view: ResearchView) {
		super(view);
		this.loadGames();
	}

	private async loadGames() {
		try {
			const games = await ResearchService.getResearchData();
			this._view.setGames(games);
		} catch (error) {
			console.error("Failed to load games:", error);
			// Optionally, display an error message to the user
		}
	}

	public handleLogin() {
		// In a real application, you would have authentication logic here.
		this._view.setIsLoggedIn(true);
	}

	public handleSelectGame(game: ResearchGameDTO) {
		this._view.setSelectedGame(game);
	}
}
