import { ChatDTO, ChatMessageDTO } from "../../../dtos/index";

export type ActiveChatId = "global" | string;

export interface ChatTabViewModel {
  id: ActiveChatId;
  label: string;
  unread: number;
  lastMessageTime: number;
}

export interface ActiveChatViewModel {
  id: ActiveChatId;
  label: string;
  recipientId: string;
  showSenderNames: boolean;
}

export const GLOBAL_CHAT_ID = "global";
export const GLOBAL_RECIPIENT_ID = "GLOBAL";

export const getMessageTime = (message: ChatMessageDTO): number => {
  if (typeof message.timestamp === "number") {
    return message.timestamp;
  }

  if (message.created_at) {
    const createdAtTime = new Date(message.created_at).getTime();
    return Number.isNaN(createdAtTime) ? 0 : createdAtTime;
  }

  return 0;
};

export const getChatLastMessageTime = (
  messages: ChatMessageDTO[],
  chatId: string,
): number => {
  return messages
    .filter((message) => message.to_id === chatId)
    .reduce((latest, message) => Math.max(latest, getMessageTime(message)), 0);
};

export const getActiveChatView = (
  activeChatId: ActiveChatId,
  chats: ChatDTO[],
): ActiveChatViewModel => {
  if (activeChatId === GLOBAL_CHAT_ID) {
    return {
      id: GLOBAL_CHAT_ID,
      label: "Village Square",
      recipientId: GLOBAL_RECIPIENT_ID,
      showSenderNames: true,
    };
  }

  const activeChat = chats.find((chat) => chat.id === activeChatId);

  return {
    id: activeChatId,
    label: activeChat ? `#${activeChat.name}` : "Chat",
    recipientId: activeChatId,
    showSenderNames: true,
  };
};
