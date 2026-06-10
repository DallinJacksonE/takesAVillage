import { ResearchGameDTO } from "../../../dtos";

export class ResearchService {
	static async getResearchData(): Promise<ResearchGameDTO[]> {
		const response = await fetch("/api/research/games");
		if (!response.ok) {
			throw new Error("Failed to fetch research data");
		}
		return await response.json();
	}
}
