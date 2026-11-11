export { default as TabbedCommunicator } from "./TabbedCommunicator";
export type { TabbedCommunicatorProps } from "./TabbedCommunicator";

export { default as ActiveChat } from "./ActiveChat";
export type { ActiveChatProps } from "./ActiveChat";

export { default as ChatTabsRail } from "./ChatTabsRail";
export type { ChatTabsRailProps } from "./ChatTabsRail";

export { default as CreateChatModal } from "./CreateChatModal";
export type { CreateChatModalProps } from "./CreateChatModal";

export {
  GLOBAL_CHAT_ID,
  GLOBAL_RECIPIENT_ID,
  GLOBAL_CHAT_LABEL,
  getActiveChatView,
  getChatLastMessageTime,
  getMessageTime,
} from "./chatViewTypes";
export type {
  ActiveChatId,
  ActiveChatViewModel,
  ChatTabViewModel,
} from "./chatViewTypes";

