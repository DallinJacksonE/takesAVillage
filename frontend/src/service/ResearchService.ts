import {
	ResearchGameDTO,
	TrainingSessionsDTO,
} from "../../../dtos";

type TrainingSessionsHandler = (sessions: TrainingSessionsDTO) => void;
type TrainingSessionsErrorHandler = (error: Event) => void;

export class ResearchService {
	static async getResearchData(): Promise<ResearchGameDTO[]> {
		const response = await fetch("/api/research/games");
		if (!response.ok) {
			throw new Error("Failed to fetch research data");
		}
		return await response.json();
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

	private static trainingSessionsWebSocketUrl(): string {
		const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
		return `${protocol}//${window.location.host}/ws/research/training-sessions`;
	}
}
