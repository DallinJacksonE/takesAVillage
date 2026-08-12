import type { InboundGameEvent, OutboundGameEvent } from "@takes-a-village/shared";

import type { Game } from "../../game/game.js";

export interface GameEventMessenger {
  broadcast(gameId: string, packet: OutboundGameEvent): void;
  sendPersonal(gameId: string, userId: string, packet: OutboundGameEvent): void;
  broadcastStates(game: Game): void;
}

type RoutedGameEvent = Exclude<InboundGameEvent, { event: "join_room" }>;

export function processGameEvent(
  game: Game,
  userId: string,
  packet: RoutedGameEvent,
  messenger: GameEventMessenger,
): void {
  switch (packet.event) {
    case "start_game_request":
      if (game.hostId === userId && game.startGame()) {
        messenger.broadcast(game.id, { event: "game_started", data: { day: 1 } });
        messenger.broadcastStates(game);
      }
      return;
    case "request_update": {
      const state = game.getStateForPlayer(userId);
      if (state) messenger.sendPersonal(game.id, userId, { event: "game_state", data: state });
      return;
    }
    case "send_chat":
      deliverChatEvent(game, userId, packet.data, messenger);
      return;
    case "create_chat":
      if (game.createChat(userId, packet.data.name, packet.data.memberIds)) messenger.broadcastStates(game);
      return;
    case "submit_action": {
      if (game.status === "WAITING") return;
      const player = game.players.get(userId);
      if (packet.data.action_command === "FINISH_PHASE" && player?.finishedPhase) return;
      const accepted = game.handleAction(userId, {
        action_command: packet.data.action_command,
        payload: packet.data.payload,
      });
      if (accepted) messenger.broadcastStates(game);
      else messenger.sendPersonal(game.id, userId, {
        event: "error",
        data: {
          message: "Action rejected by game rules.",
          action_command: packet.data.action_command,
        },
      });
    }
  }
}

export function deliverChatEvent(
  game: Game,
  userId: string,
  data: { content: string; to_id: string },
  messenger: GameEventMessenger,
): boolean {
  const message = game.handleChat(userId, data.content, data.to_id);
  if (!message) return false;
  const packet = { event: "new_chat_message", data: message } satisfies OutboundGameEvent;
  if (message.to_id === "GLOBAL") {
    messenger.broadcast(game.id, packet);
    return true;
  }

  const group = game.chats.find((chat) => chat.id === message.to_id);
  const recipients = group?.member_ids ?? [message.from_id, message.to_id];
  for (const recipientId of new Set(recipients)) {
    if (recipientId) messenger.sendPersonal(game.id, recipientId, packet);
  }
  return true;
}
