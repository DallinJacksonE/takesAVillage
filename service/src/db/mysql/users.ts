import type { SqlExecutor, SqlResult } from "./sql.js";
import { rows } from "./sql.js";

export class UsersRepository {
  constructor(private readonly database: SqlExecutor) {}

  async createUser(userId: string, consentAgreed = true): Promise<boolean> {
    const [result] = await this.database.execute(
      "INSERT INTO users (uuid, consent_agreed, created_at) VALUES (?, ?, NOW()) ON DUPLICATE KEY UPDATE consent_agreed = VALUES(consent_agreed)",
      [userId, consentAgreed],
    );
    return ((result as SqlResult).affectedRows ?? 0) > 0;
  }

  async userExists(userId: string): Promise<boolean> {
    const [result] = await this.database.execute("SELECT 1 FROM users WHERE uuid = ? LIMIT 1", [userId]);
    return rows(result).length > 0;
  }
}
