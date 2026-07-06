import {
	NewGameOptionsDTO,
	ResearchGameDetailDTO,
	ResearchGameListItemDTO,
	TrainingBatchDetailDTO,
	TrainingBatchListItemDTO,
	TrainingSessionsDTO,
} from "../dtos";

export type ResearchSortMode = "time_desc" | "name_asc" | "name_desc";
export type TrainingSessionsHandler = (sessions: TrainingSessionsDTO) => void;
export type TrainingSessionsErrorHandler = (error: Event) => void;

export class ResearchService {
	static async getResearchData(): Promise<ResearchGameListItemDTO[]> {
		return this.fetchGameList();
	}

	static async fetchGameList(
		searchQuery = "",
		sortMode: ResearchSortMode = "time_desc",
	): Promise<ResearchGameListItemDTO[]> {
		const params = new URLSearchParams();
		if (searchQuery.trim()) {
			params.set("search", searchQuery.trim());
		}
		params.set("sort", sortMode);
		return this.fetchJson<ResearchGameListItemDTO[]>(
			`/api/research/games?${params.toString()}`,
			"Failed to fetch research games",
		);
	}

	static async fetchGameDetail(gameId: string): Promise<ResearchGameDetailDTO> {
		return this.fetchJson<ResearchGameDetailDTO>(
			`/api/research/games/${encodeURIComponent(gameId)}`,
			"Failed to fetch game detail",
		);
	}

	static async fetchTrainingBatchList(): Promise<TrainingBatchListItemDTO[]> {
		const payload = await this.fetchJson<{ batches: TrainingBatchListItemDTO[] }>(
			"/api/research/training-batches",
			"Failed to fetch training batches",
		);
		return payload.batches ?? [];
	}

	static async fetchTrainingBatchDetail(batchId: string): Promise<TrainingBatchDetailDTO> {
		return this.fetchJson<TrainingBatchDetailDTO>(
			`/api/research/training-batches/${encodeURIComponent(batchId)}`,
			"Failed to fetch training batch detail",
		);
	}

	static async fetchTrainingOptions(): Promise<{
		gameOptions: NewGameOptionsDTO["options"];
		genomes: any[];
		models: string[];
	}> {
		const [rulesData, genomeData] = await Promise.all([
			this.fetchJson<NewGameOptionsDTO>("/api/newGame", "Failed to fetch rulesets"),
			this.fetchJson<{ genomes: any[]; models?: string[] }>(
				"/api/research/genomes",
				"Failed to fetch genomes",
			),
		]);
		return {
			gameOptions: rulesData.options || {},
			genomes: genomeData.genomes || [],
			models: genomeData.models || ["genetic"],
		};
	}

	static async startTrainingLoop(options: Record<string, any>): Promise<void> {
		await this.fetchJson<{ message: string }>(
			"/api/research/train",
			"Failed to start training loop",
			{
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(options),
			},
		);
	}

	static subscribeToTrainingSessions(
		onUpdate: TrainingSessionsHandler,
		onError?: TrainingSessionsErrorHandler,
	): () => void {
		const socket = new WebSocket(this.trainingSessionsWebSocketUrl());

		socket.onmessage = (event) => {
			const message = JSON.parse(event.data);
			if (message.event === "training_sessions") {
				onUpdate(message.data as TrainingSessionsDTO);
			}
		};

		socket.onerror = (event) => {
			onError?.(event);
		};

		return () => {
			socket.close();
		};
	}

	private static async fetchJson<T>(
		url: string,
		errorMessage: string,
		init?: RequestInit,
	): Promise<T> {
		const response = init ? await fetch(url, init) : await fetch(url);
		if (!response.ok) {
			throw new Error(`${errorMessage}: ${response.status} ${response.statusText}`);
		}
		return await response.json();
	}

	private static trainingSessionsWebSocketUrl(): string {
		const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
		return `${protocol}//${window.location.host}/ws/research/training-sessions`;
	}
}
