import {
	genomesResponseSchema,
	httpContractSchemas,
	messageResponseSchema,
	newGameOptionsSchema,
	researchGameDetailSchema,
	researchGameListItemSchema,
	trainingBatchDetailSchema,
	trainingRequestSchema,
	trainingSessionsEventSchema,
	type GenomeDTO,
	type NewGameOptionsDTO,
	type ResearchGameDetailDTO,
	type ResearchGameListItemDTO,
	type TrainingBatchDetailDTO,
	type TrainingBatchListItemDTO,
	type TrainingRequest,
	type TrainingSessionsDTO,
} from "@takes-a-village/shared";

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
		return researchGameListItemSchema.array().parse(await this.fetchJson(
			`/api/research/games?${params.toString()}`,
			"Failed to fetch research games",
		));
	}

	static async fetchGameDetail(gameId: string): Promise<ResearchGameDetailDTO> {
		return researchGameDetailSchema.parse(await this.fetchJson(
			`/api/research/games/${encodeURIComponent(gameId)}`,
			"Failed to fetch game detail",
		));
	}

	static async fetchTrainingBatchList(): Promise<TrainingBatchListItemDTO[]> {
		const payload = httpContractSchemas.trainingBatches.parse(await this.fetchJson(
			"/api/research/training-batches",
			"Failed to fetch training batches",
		));
		return payload.batches ?? [];
	}

	static async fetchTrainingBatchDetail(batchId: string): Promise<TrainingBatchDetailDTO> {
		return trainingBatchDetailSchema.parse(await this.fetchJson(
			`/api/research/training-batches/${encodeURIComponent(batchId)}`,
			"Failed to fetch training batch detail",
		));
	}

	static async fetchTrainingOptions(): Promise<{
		gameOptions: NewGameOptionsDTO["options"];
		genomes: GenomeDTO[];
		models: string[];
	}> {
		const [rulesData, genomeData] = await Promise.all([
			this.fetchJson("/api/newGame", "Failed to fetch rulesets").then((value) => newGameOptionsSchema.parse(value)),
			this.fetchJson(
				"/api/research/genomes",
				"Failed to fetch genomes",
			).then((value) => genomesResponseSchema.parse(value)),
		]);
		return {
			gameOptions: rulesData.options || {},
			genomes: genomeData.genomes || [],
			models: genomeData.models || ["genetic"],
		};
	}

	static async startTrainingLoop(options: TrainingRequest): Promise<void> {
		const request = trainingRequestSchema.parse(options);
		messageResponseSchema.parse(await this.fetchJson(
			"/api/research/train",
			"Failed to start training loop",
			{
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(request),
			},
		));
	}

	static async cancelTrainingBatch(batchId: string, reason?: string): Promise<void> {
		messageResponseSchema.parse(await this.fetchJson(
			`/api/research/training-batches/${encodeURIComponent(batchId)}/cancel`,
			"Failed to cancel training batch",
			{
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ reason }),
			},
		));
	}

	static async rerunTrainingBatch(batchId: string): Promise<void> {
		messageResponseSchema.parse(await this.fetchJson(
			`/api/research/training-batches/${encodeURIComponent(batchId)}/rerun`,
			"Failed to rerun training batch",
			{ method: "POST" },
		));
	}

	static subscribeToTrainingSessions(
		onUpdate: TrainingSessionsHandler,
		onError?: TrainingSessionsErrorHandler,
	): () => void {
		const socket = new WebSocket(this.trainingSessionsWebSocketUrl());

		socket.onmessage = (event) => {
			try {
				const message = trainingSessionsEventSchema.parse(JSON.parse(event.data));
				onUpdate(message.data);
			} catch {
				onError?.(new Event("error"));
			}
		};

		socket.onerror = (event) => {
			onError?.(event);
		};

		return () => {
			socket.close();
		};
	}

	private static async fetchJson(
		url: string,
		errorMessage: string,
		init?: RequestInit,
	): Promise<unknown> {
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
