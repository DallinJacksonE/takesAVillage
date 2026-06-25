import { ResearchService } from "../service/ResearchService";
import { ResearchGameDTO, TrainingSessionDTO } from "../../../dtos";
import { Presenter } from "./Presenter";
import { View } from "./View";

export interface ResearchView extends View {
	setIsLoggedIn(isLoggedIn: boolean): void;
	setSelectedGame(selectedGame: ResearchGameDTO | null): void;
	setGames(games: ResearchGameDTO[]): void;
	setTrainingSessions(trainingSessions: TrainingSessionDTO[]): void;
}

export class ResearchPresenter extends Presenter<ResearchView> {
	private unsubscribeFromTrainingSessions: (() => void) | null = null;

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

	public setTrainingSessionsVisible(isVisible: boolean) {
		if (isVisible) {
			this.subscribeToTrainingSessions();
		} else {
			this.disconnectTrainingSessions();
			this._view.setTrainingSessions([]);
		}
	}

	public dispose() {
		this.disconnectTrainingSessions();
	}

	private subscribeToTrainingSessions() {
		if (this.unsubscribeFromTrainingSessions) {
			return;
		}

		this.unsubscribeFromTrainingSessions = ResearchService.subscribeToTrainingSessions(
			(payload) => this._view.setTrainingSessions(payload.sessions),
			(error) => console.error("Training session websocket failed:", error),
		);
	}

	private disconnectTrainingSessions() {
		this.unsubscribeFromTrainingSessions?.();
		this.unsubscribeFromTrainingSessions = null;
	}
}
