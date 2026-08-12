import { z } from "zod";

const portSchema = z.number().int().min(1).max(65_535);
export const portProfileSchema = z.object({
  database: portSchema,
  service: portSchema,
  bots: portSchema,
  frontend: portSchema,
}).superRefine((profile, context) => {
  const ports = Object.values(profile);
  if (new Set(ports).size !== ports.length) {
    context.addIssue({ code: "custom", message: "Ports must be unique within a profile" });
  }
});
export type PortProfile = z.infer<typeof portProfileSchema>;

export const rootConfigSchema = z.object({
  development: portProfileSchema,
  production: portProfileSchema,
}).superRefine((config, context) => {
  const ports = [...Object.values(config.development), ...Object.values(config.production)];
  if (new Set(ports).size !== ports.length) {
    context.addIssue({ code: "custom", message: "Development and production ports must not conflict" });
  }
});
export type RootConfig = z.infer<typeof rootConfigSchema>;

export const serviceConfigSchema = z.object({
  database: z.object({
    type: z.enum(["memory", "mysql"]),
    host: z.string().min(1),
    port: portSchema,
    user: z.string().min(1),
    password: z.string().min(1),
    name: z.string().min(1),
    rootPassword: z.string().min(1).optional(),
  }),
  bots: z.object({
    secret: z.string().min(1),
    httpUrl: z.url(),
    gameServerHttpUrl: z.url(),
    gameServerWsUrl: z.url(),
  }),
});
export type ServiceConfig = z.infer<typeof serviceConfigSchema>;

export const frontendConfigSchema = z.object({
  apiBaseUrl: z.string().default(""),
  websocketBaseUrl: z.string().default(""),
});
export type FrontendConfig = z.infer<typeof frontendConfigSchema>;
