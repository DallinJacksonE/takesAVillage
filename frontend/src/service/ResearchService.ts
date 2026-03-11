export interface ResearchData {
  id: string;
  title: string;
  description: string;
  // Add other fields as necessary
}

export class ResearchService {
	static async getResearchData(): Promise<ResearchData[]> {
		const response = await fetch("/api/research");
		if (!response.ok) {
			throw new Error("Failed to fetch research data");
		}
		return await response.json();
	}
}
