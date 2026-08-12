import { timingSafeEqual } from "node:crypto";

import type { FastifyInstance } from "fastify";

import {
  inboundGameEventSchema,
  type InboundGameEvent,
  type OutboundGameEvent,
} from "@takes-a-village/shared";

import type { UserDatabase } from "../../db.js";
import type { Game } from "../../game/game.js";
import { ConnectionManager, type SocketConnection } from "./connection-manager.js";
import { processGameEvent, type GameEventMessenger } from "./game-events.js";

export interface GameRouterDependencies {
  games: Map<string, Game>;
  connections: ConnectionManager;
  database: UserDatabase;
  botSecret: string;
  botServiceUrl?: string;
}

export function sameSecret(supplied: string, expected: string): boolean {
  const left = Buffer.from(supplied);
  const right = Buffer.from(expected);
  return left.length === right.length && timingSafeEqual(left, right);
}

function send(socket: SocketConnection, packet: OutboundGameEvent): void {
  socket.send(JSON.stringify(packet));
}

export function createGameEventMessenger(connections: ConnectionManager): GameEventMessenger {
  return {
    broadcast(gameId, packet) {
      connections.broadcast(gameId, packet);
    },
    sendPersonal(gameId, userId, packet) {
      connections.sendPersonal(gameId, userId, packet);
    },
    broadcastStates(game) {
      for (const [playerId] of connections.entries(game.id)) {
        const state = game.getStateForPlayer(playerId);
        if (state) connections.sendPersonal(game.id, playerId, { event: "game_state", data: state });
      }
    },
  };
}

export function cleanupDisconnectedPlayer(
  gameId: string,
  userId: string,
  dependencies: Pick<GameRouterDependencies, "games" | "connections" | "botSecret" | "botServiceUrl">,
): void {
  const game = dependencies.games.get(gameId);
  if (!game || game.status !== "WAITING") return;
  game.removePlayer(userId);
  dependencies.connections.broadcast(gameId, {
    event: "room_update",
    data: { player_count: game.players.size },
  });
  if (userId.startsWith("bot_") && dependencies.botServiceUrl) {
    void fetch(`${dependencies.botServiceUrl}/api/spawn_bots`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        gameId,
        botCount: 1,
        botSecret: dependencies.botSecret,
        botModel: "genetic",
        baseGenome: null,
      }),
    }).catch(() => undefined);
  }
}

export function registerGameWebSocketRoute(
  app: FastifyInstance,
  dependencies: GameRouterDependencies,
): void {
  const messenger = createGameEventMessenger(dependencies.connections);

  app.get("/ws", { websocket: true }, (socket, request) => {
    let joinedGameId: string | undefined;
    let joinedUserId: string | undefined;

    socket.on("message", async (raw) => {
      let packet: unknown;
      try {
        packet = JSON.parse(raw.toString());
      } catch {
        send(socket, { event: "error", data: { message: "Invalid WebSocket packet." } });
        return;
      }
      if (!packet || typeof packet !== "object" || Array.isArray(packet)) {
        send(socket, { event: "error", data: { message: "Invalid WebSocket packet." } });
        return;
      }
      const parsed = inboundGameEventSchema.safeParse(packet);
      if (!parsed.success) {
        send(socket, { event: "error", data: { message: "Malformed WebSocket packet." } });
        return;
      }

      if (joinedGameId && joinedUserId && dependencies.connections.get(joinedGameId, joinedUserId) !== socket) {
        send(socket, { event: "error", data: { message: "WebSocket connection was replaced." } });
        socket.close(4001);
        return;
      }

      if (parsed.data.event === "join_room") {
        if (joinedGameId) {
          send(socket, { event: "error", data: { message: "WebSocket is already joined to a game." } });
          return;
        }
        const { data } = parsed.data;
        const game = dependencies.games.get(data.gameId);
        if (!game) {
          send(socket, { event: "error", data: { message: "Game not found." } });
          return;
        }
        const browserAuthenticated = request.cookies.user_session === data.userId
          && await dependencies.database.userExists(data.userId);
        const botAuthenticated = data.userId.startsWith("bot_")
          && typeof data.botSecret === "string"
          && sameSecret(data.botSecret, dependencies.botSecret)
          && game.players.has(data.userId);
        if (!browserAuthenticated && !botAuthenticated) {
          send(socket, { event: "error", data: { message: "WebSocket authentication failed." } });
          return;
        }
        if (game.status !== "WAITING" && !game.players.has(data.userId)) {
          send(socket, { event: "error", data: { message: "Player is not a member of this game." } });
          return;
        }

        joinedGameId = data.gameId;
        joinedUserId = data.userId;
        game.addPlayer(data.userId);
        dependencies.connections.connect(socket, data.gameId, data.userId);
        if (game.hostId === data.userId && !game.hostConnected) {
          game.hostConnected = true;
          messenger.broadcastStates(game);
        }
        dependencies.connections.sendPersonal(data.gameId, data.userId, {
          event: "chat_history",
          data: game.getPrivateChatHistory(data.userId),
        });
        const state = game.getStateForPlayer(data.userId);
        if (state) dependencies.connections.sendPersonal(data.gameId, data.userId, { event: "game_state", data: state });
        messenger.broadcast(data.gameId, { event: "room_update", data: { player_count: game.players.size } });
        if (game.training && game.status === "RUNNING") {
          messenger.broadcast(game.id, { event: "game_started", data: { day: 1 } });
          messenger.broadcastStates(game);
        }
        return;
      }

      if (!joinedGameId || !joinedUserId) return;
      const game = dependencies.games.get(joinedGameId);
      if (!game) return;
      processGameEvent(game, joinedUserId, parsed.data as Exclude<InboundGameEvent, { event: "join_room" }>, messenger);
    });

    socket.on("close", () => {
      if (!joinedGameId || !joinedUserId) return;
      if (dependencies.connections.disconnect(socket, joinedGameId, joinedUserId)) {
        cleanupDisconnectedPlayer(joinedGameId, joinedUserId, dependencies);
      }
    });
  });
}
