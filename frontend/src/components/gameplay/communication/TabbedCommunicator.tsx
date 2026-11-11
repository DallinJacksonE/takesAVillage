import { useEffect, useMemo, useState } from "react";
import type { ChatDTO, ChatMessageDTO, PublicPlayerDTO } from "../../../dtos";
import { usePlayerName } from "../../hooks/usePlayerName";
import ActiveChat from "./ActiveChat";
import ChatTabsRail from "./ChatTabsRail";
import CreateChatModal from "./CreateChatModal";
import styles from "./TabbedCommunicator.module.css";
import {
  GLOBAL_CHAT_ID,
  GLOBAL_CHAT_LABEL,
  GLOBAL_RECIPIENT_ID,
  type ChatTabViewModel,
  getActiveChatView,
  getChatLastMessageTime,
} from "./chatViewTypes";

export interface TabbedCommunicatorProps {
  messages: ChatMessageDTO[];
  playerId: string;
  players: PublicPlayerDTO[];
  chats: ChatDTO[];
  onSend: (content: string, toId: string) => void;
  onCreateChat: (name: string, memberIds: string[]) => void;
}

const TabbedCommunicator = ({
  messages,
  playerId,
  players,
  chats,
  onSend,
  onCreateChat,
}: TabbedCommunicatorProps) => {
  const [activeChatId, setActiveChatId] = useState<string>(GLOBAL_CHAT_ID);
  const [messageInput, setMessageInput] = useState("");
  const [readMessageIds, setReadMessageIds] = useState<Set<string>>(new Set());
  const [isCreateChatModalOpen, setIsCreateChatModalOpen] = useState(false);
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);
  const getPlayerName = usePlayerName();

  const availableChatIds = useMemo(
    () => new Set(chats.map((chat) => chat.id)),
    [chats],
  );

  useEffect(() => {
    if (activeChatId !== GLOBAL_CHAT_ID && !availableChatIds.has(activeChatId)) {
      setActiveChatId(GLOBAL_CHAT_ID);
    }
  }, [activeChatId, availableChatIds]);

  const activeChatMessages = useMemo(() => {
    const activeRecipientId =
      activeChatId === GLOBAL_CHAT_ID ? GLOBAL_RECIPIENT_ID : activeChatId;

    return messages.filter((message) => message.to_id === activeRecipientId);
  }, [messages, activeChatId]);

  useEffect(() => {
    setReadMessageIds((previous) => {
      let hasChanges = false;
      const updated = new Set(previous);

      for (const message of activeChatMessages) {
        if (!updated.has(message.id)) {
          updated.add(message.id);
          hasChanges = true;
        }
      }

      return hasChanges ? updated : previous;
    });
  }, [activeChatMessages]);

  const getUnreadCount = (recipientId: string) =>
    messages.filter(
      (message) =>
        message.to_id === recipientId &&
        message.from_id !== playerId &&
        !readMessageIds.has(message.id),
    ).length;

  const globalTab: ChatTabViewModel = {
    id: GLOBAL_CHAT_ID,
    label: GLOBAL_CHAT_LABEL,
    unread: getUnreadCount(GLOBAL_RECIPIENT_ID),
    lastMessageTime: getChatLastMessageTime(messages, GLOBAL_RECIPIENT_ID),
  };

  const chatTabs: ChatTabViewModel[] = chats
    .map((chat) => ({
      id: chat.id,
      label: `#${chat.name}`,
      unread: getUnreadCount(chat.id),
      lastMessageTime: getChatLastMessageTime(messages, chat.id),
    }))
    .sort((a, b) => b.lastMessageTime - a.lastMessageTime);

  const activeChat = getActiveChatView(activeChatId, chats);
  const activeChatView = {
    ...activeChat,
    memberIds: activeChat.memberIds ?? players.map((player) => player.id),
  };

  const handleSendMessage = () => {
    const trimmedMessage = messageInput.trim();
    if (!trimmedMessage) {
      return;
    }

    onSend(trimmedMessage, activeChat.recipientId);
    setMessageInput("");
  };

  const handleToggleSidebar = () =>
    setIsSidebarExpanded((isExpanded) => !isExpanded);
  const handleOpenCreateChatModal = () => setIsCreateChatModalOpen(true);
  const handleCloseCreateChatModal = () => setIsCreateChatModalOpen(false);

  return (
    <>
      <div className={`card ${styles.communicatorLayout}`}>
        <ActiveChat
          activeChat={activeChatView}
          getPlayerName={getPlayerName}
          inputValue={messageInput}
          messages={activeChatMessages}
          onInputChange={setMessageInput}
          onSend={handleSendMessage}
          playerId={playerId}
        />

        <ChatTabsRail
          activeChatId={activeChatId}
          chatTabs={chatTabs}
          globalTab={globalTab}
          isExpanded={isSidebarExpanded}
          onCreateChat={handleOpenCreateChatModal}
          onSelectChat={setActiveChatId}
          onToggleExpanded={handleToggleSidebar}
        />
      </div>

      {isCreateChatModalOpen && (
        <CreateChatModal
          onCreateChat={onCreateChat}
          onClose={handleCloseCreateChatModal}
          playerId={playerId}
          players={players}
        />
      )}
    </>
  );
};

export default TabbedCommunicator;
