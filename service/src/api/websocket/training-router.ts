import type { FastifyInstance } from "fastify";

import {
  trainingSessionsEventSchema,
  trainingSessionsSchema,
  type TrainingSessionsDTO,
  type TrainingSessionsEvent,
} from "@takes-a-village/shared";

export interface TrainingSocket {
  send(data: string): void;
}

export class TrainingUpdateHub {
  private readonly connections = new Set<TrainingSocket>();

  get size(): number {
    return this.connections.size;
  }

  connect(socket: TrainingSocket): void {
    this.connections.add(socket);
  }

  disconnect(socket: TrainingSocket): void {
    this.connections.delete(socket);
  }

  sendCurrent(socket: TrainingSocket, sessions: TrainingSessionsDTO): boolean {
    const packet = this.packet(sessions);
    try {
      socket.send(JSON.stringify(packet));
      return true;
    } catch {
      this.disconnect(socket);
      return false;
    }
  }

  broadcast(sessions: TrainingSessionsDTO): void {
    const packet = JSON.stringify(this.packet(sessions));
    for (const socket of [...this.connections]) {
      try {
        socket.send(packet);
      } catch {
        this.disconnect(socket);
      }
    }
  }

  private packet(sessions: TrainingSessionsDTO): TrainingSessionsEvent {
    return trainingSessionsEventSchema.parse({
      event: "training_sessions",
      data: trainingSessionsSchema.parse(sessions),
    });
  }
}

export function registerTrainingWebSocketRoute(
  app: FastifyInstance,
  hub: TrainingUpdateHub,
  listSessions: () => TrainingSessionsDTO,
): void {
  app.get("/ws/research/training-sessions", { websocket: true }, (socket) => {
    hub.connect(socket);
    hub.sendCurrent(socket, listSessions());
    socket.on("close", () => hub.disconnect(socket));
  });
}
