import { ResearchService, ResearchSortMode } from "../service/ResearchService";
import {
	ResearchGameDetailDTO,
	ResearchGameListItemDTO,
	TrainingBatchDetailDTO,
	TrainingBatchListItemDTO,
	TrainingSessionDTO,
} from "@takes-a-village/shared";
import { Presenter } from "./Presenter";
import { View } from "./View";

export type ResearchTab = "games" | "training-batches";
export type ResearchTrainingBatchRow = TrainingBatchListItemDTO & {
	progress_tooltip?: string;
};

export interface ResearchView extends View {
	setIsLoggedIn(isLoggedIn: boolean): void;
	setSelectedGame(selectedGame: ResearchGameDetailDTO | null): void;
	setSelectedTrainingBatch(selectedTrainingBatch: TrainingBatchDetailDTO | null): void;
	setGames(games: ResearchGameListItemDTO[]): void;
	setTrainingBatches(trainingBatches: ResearchTrainingBatchRow[]): void;
	setActiveTab(activeTab: ResearchTab): void;
	setSearchQuery(searchQuery: string): void;
	setSortMode(sortMode: ResearchSortMode): void;
	setIsLoading(isLoading: boolean): void;
	setStatusMessage(statusMessage: string | null): void;
	setErrorMessage(errorMessage: string | null): void;
	setTrainingOptions(options: { gameOptions: Record<string, Record<string, any>>; genomes: any[]; models: string[] }): void;
	setIsTrainingModalOpen(isOpen: boolean): void;
}

export class ResearchPresenter extends Presenter<ResearchView> {
	private unsubscribeFromTrainingSessions: (() => void) | null = null;
	private searchQuery = "";
	private sortMode: ResearchSortMode = "time_desc";
	private persistedTrainingBatches: ResearchTrainingBatchRow[] = [];

	constructor(view: ResearchView) {
		super(view);
		this._view.setActiveTab("games");
		this._view.setSearchQuery(this.searchQuery);
		this._view.setSortMode(this.sortMode);
		this.loadInitialData();
		this.subscribeToTrainingSessions();
	}

	public handleLogin() {
		this._view.setIsLoggedIn(true);
	}

	public async handleSearchQueryChanged(searchQuery: string) {
		this.searchQuery = searchQuery;
		this._view.setSearchQuery(searchQuery);
		await this.loadGames();
	}

	public async handleSortModeChanged(sortMode: ResearchSortMode) {
		this.sortMode = sortMode;
		this._view.setSortMode(sortMode);
		await this.loadGames();
	}

	public handleTabChanged(tab: ResearchTab) {
		this._view.setActiveTab(tab);
	}

	public async handleSelectGame(game: ResearchGameListItemDTO) {
		this._view.setIsLoading(true);
		this._view.setErrorMessage(null);
		try {
			const detail = await ResearchService.fetchGameDetail(game.game_id);
			this._view.setSelectedGame(detail);
			this._view.setSelectedTrainingBatch(null);
		} catch (error) {
			this._view.setErrorMessage(this.messageFromError(error));
		} finally {
			this._view.setIsLoading(false);
		}
	}

	public async handleSelectTrainingBatch(batch: TrainingBatchListItemDTO) {
		this._view.setIsLoading(true);
		this._view.setErrorMessage(null);
		try {
			const detail = await ResearchService.fetchTrainingBatchDetail(batch.batch_id);
			this._view.setSelectedTrainingBatch(detail);
			this._view.setSelectedGame(null);
		} catch (error) {
			this._view.setErrorMessage(this.messageFromError(error));
		} finally {
			this._view.setIsLoading(false);
		}
	}

	public async handleOpenTrainingMenu() {
		this._view.setIsLoading(true);
		this._view.setErrorMessage(null);
		try {
			const options = await ResearchService.fetchTrainingOptions();
			this._view.setTrainingOptions(options);
			this._view.setIsTrainingModalOpen(true);
		} catch (error) {
			this._view.setErrorMessage(this.messageFromError(error));
		} finally {
			this._view.setIsLoading(false);
		}
	}

	public async handleStartTraining(options: Record<string, any>) {
		this._view.setStatusMessage(null);
		this._view.setErrorMessage(null);
		try {
			await ResearchService.startTrainingLoop({
				ruleset: options.ruleset,
				botCount: options.botCount,
				generations: options.generations,
				baseGenome: options.baseGenome,
				botModel: options.botModel,
				gamesPerGeneration: options.gamesPerGeneration,
				mutationStrength: options.mutationStrength,
				mutationRate: options.mutationRate,
				randomImmigrantCount: options.randomImmigrantCount,
			});
			this._view.setStatusMessage("Training sequence initiated.");
			this._view.setIsTrainingModalOpen(false);
			this._view.setActiveTab("training-batches");
			await this.loadTrainingBatches();
		} catch (error) {
			this._view.setErrorMessage(this.messageFromError(error));
		}
	}

	public dispose() {
		this.disconnectTrainingSessions();
	}

	private async loadInitialData() {
		this._view.setIsLoading(true);
		try {
			await Promise.all([this.loadGames(), this.loadTrainingBatches()]);
		} finally {
			this._view.setIsLoading(false);
		}
	}

	private async loadGames() {
		try {
			const games = await ResearchService.fetchGameList(this.searchQuery, this.sortMode);
			this._view.setGames(games);
		} catch (error) {
			this._view.setErrorMessage(this.messageFromError(error));
		}
	}

	private async loadTrainingBatches() {
		try {
			this.persistedTrainingBatches = await ResearchService.fetchTrainingBatchList();
			this._view.setTrainingBatches(this.persistedTrainingBatches);
		} catch (error) {
			this._view.setErrorMessage(this.messageFromError(error));
		}
	}

	private subscribeToTrainingSessions() {
		if (this.unsubscribeFromTrainingSessions) {
			return;
		}

		this.unsubscribeFromTrainingSessions = ResearchService.subscribeToTrainingSessions(
			(payload) => this.mergeTrainingSessionUpdates(payload.sessions),
			(error) => this._view.setErrorMessage(`Training session websocket failed: ${error.type}`),
		);
	}

	private disconnectTrainingSessions() {
		this.unsubscribeFromTrainingSessions?.();
		this.unsubscribeFromTrainingSessions = null;
	}

	private mergeTrainingSessionUpdates(sessions: TrainingSessionDTO[]) {
		const activeRows = sessions.map((session) => this.sessionToBatchRow(session));
		const activeIds = new Set(activeRows.map((row) => row.batch_id));
		const inactivePersistedRows = this.persistedTrainingBatches.filter(
			(batch) => !activeIds.has(batch.batch_id),
		);
		this._view.setTrainingBatches([...activeRows, ...inactivePersistedRows]);
	}

	private sessionToBatchRow(session: TrainingSessionDTO): ResearchTrainingBatchRow {
		const latestStats = session.generation_statistics.at(-1);
		const bestFitness = latestStats?.best_fitness;
		const totalGenerations = session.generation + session.generations_left;
		const gameProgress = session.games_per_generation
			? `Game ${session.current_generation_game_index || session.games_completed || 0}/${session.games_per_generation}`
			: null;
		const failureProgress = session.games_failed
			? `${session.games_failed} failed`
			: null;
		return {
			batch_id: session.session_id,
			status: "running",
			current_game_id: session.current_game_id,
			ruleset: session.ruleset,
			bot_count: session.bot_count,
			current_generation: session.generation,
			total_generations: totalGenerations,
			games_per_generation: session.games_per_generation,
			games_completed: session.games_completed,
			games_failed: session.games_failed,
			current_generation_game_index: session.current_generation_game_index,
			generation_statistics: session.generation_statistics,
			progress_tooltip: [
				`Generation ${session.generation}`,
				`${session.generations_left} remaining`,
				gameProgress,
				failureProgress,
				session.current_game_id ? `Game ${session.current_game_id}` : null,
				bestFitness !== undefined ? `Best fitness ${bestFitness}` : null,
			].filter(Boolean).join(" • "),
		};
	}

	private messageFromError(error: unknown): string {
		return error instanceof Error ? error.message : String(error);
	}
}
