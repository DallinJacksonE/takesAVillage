export interface SocketConnection {
  send(data: string, callback?: (error?: Error) => void): void;
  close(code?: number, reason?: string): void;
}

export class ConnectionManager {
  private readonly connections = new Map<string, Map<string, SocketConnection>>();

  constructor(
    private readonly onFailedConnection?: (gameId: string, userId: string) => void,
  ) {}

  connect(socket: SocketConnection, gameId: string, userId: string): void {
    const gameConnections = this.connections.get(gameId) ?? new Map<string, SocketConnection>();
    const previous = gameConnections.get(userId);
    gameConnections.set(userId, socket);
    this.connections.set(gameId, gameConnections);
    if (previous && previous !== socket) previous.close(4001, "WebSocket connection was replaced.");
  }

  disconnect(socket: SocketConnection, gameId: string, userId: string): boolean {
    const gameConnections = this.connections.get(gameId);
    if (!gameConnections || gameConnections.get(userId) !== socket) return false;
    gameConnections.delete(userId);
    if (gameConnections.size === 0) this.connections.delete(gameId);
    return true;
  }

  get(gameId: string, userId: string): SocketConnection | undefined {
    return this.connections.get(gameId)?.get(userId);
  }

  entries(gameId: string): Array<[string, SocketConnection]> {
    return [...(this.connections.get(gameId)?.entries() ?? [])];
  }

  sendPersonal(gameId: string, userId: string, packet: unknown): boolean {
    const socket = this.get(gameId, userId);
    if (!socket) return false;
    return this.send(socket, gameId, userId, packet);
  }

  broadcast(gameId: string, packet: unknown): void {
    for (const [userId, socket] of this.entries(gameId)) this.send(socket, gameId, userId, packet);
  }

  private send(
    socket: SocketConnection,
    gameId: string,
    userId: string,
    packet: unknown,
  ): boolean {
    try {
      let failed = false;
      socket.send(JSON.stringify(packet), (error) => {
        if (!error) return;
        failed = true;
        this.removeFailed(socket, gameId, userId);
      });
      return !failed;
    } catch {
      this.removeFailed(socket, gameId, userId);
      return false;
    }
  }

  private removeFailed(socket: SocketConnection, gameId: string, userId: string): void {
    if (this.disconnect(socket, gameId, userId)) this.onFailedConnection?.(gameId, userId);
  }
}
