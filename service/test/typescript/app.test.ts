import { describe, expect, it } from "vitest";

import { consentSchema, newGameOptionsSchema } from "@takes-a-village/shared";
import { buildApp } from "../../src/app.js";

describe("TypeScript application shell", () => {
  it("issues a session and serves typed rule options", async () => {
    const app = await buildApp({ databaseType: "memory", botSecret: "test-secret" });
    try {
      const consent = await app.inject({ method: "POST", url: "/api/consent" });
      expect(consent.statusCode).toBe(200);
      expect(consentSchema.parse(consent.json()).userId).toBeTruthy();

      const options = await app.inject({ method: "GET", url: "/api/newGame" });
      expect(options.statusCode).toBe(200);
      expect(newGameOptionsSchema.parse(options.json()).options.default).toBeTruthy();
    } finally {
      await app.close();
    }
  });
});