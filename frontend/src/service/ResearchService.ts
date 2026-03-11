import { ResearchGame } from '../types/game';

export class ResearchService {
  static async getResearchData(): Promise<ResearchGame[]> {
    const response = await fetch('/api/research/games');
    if (!response.ok) {
      throw new Error('Failed to fetch research data');
    }
    return await response.json();
  }
}
