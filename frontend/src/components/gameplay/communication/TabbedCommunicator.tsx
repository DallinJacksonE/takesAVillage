import React, { useEffect, useMemo, useState } from "react";
import { ChatDTO, ChatMessageDTO, PublicPlayerDTO } from "../../../dtos/index";
import { usePlayerName } from "../../hooks/usePlayerName";
import ActiveChat from "./ActiveChat";
import ChatTabsRail from "./ChatTabsRail";
import CreateChatModal from "./CreateChatModal";
import styles from "./TabbedCommunicator.module.css";
import {
  GLOBAL_CHAT_ID,
  GLOBAL_RECIPIENT_ID,
  ChatTabViewModel,
  getActiveChatView,
  getChatLastMessageTime,
} from "./chatViewTypes";

interface Props {
  messages: ChatMessageDTO[];
  playerId: string;
  players: PublicPlayerDTO[];
  chats: ChatDTO[];
  onSend: (content: string, toId: string) => void;
  onCreateChat: (name: string, memberIds: string[]) => void;
}

const TabbedCommunicator: React.FC<Props> = ({
  messages,
  playerId,
  players,
  chats,
  onSend,
  onCreateChat,
}) => {
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
    const recipientId =
      activeChatId === GLOBAL_CHAT_ID ? GLOBAL_RECIPIENT_ID : activeChatId;

    return messages.filter((message) => {
      return message.to_id === recipientId;
    });
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

  const getUnreadCount = (recipientId: string) => {
    return messages.filter(
      (message) =>
        message.to_id === recipientId &&
        message.from_id !== playerId &&
        !readMessageIds.has(message.id),
    ).length;
  };

  const globalTab: ChatTabViewModel = {
    id: GLOBAL_CHAT_ID,
    label: "Village Square",
    unread: getUnreadCount(GLOBAL_RECIPIENT_ID),
    lastMessageTime: getChatLastMessageTime(messages, GLOBAL_RECIPIENT_ID),
  };

  const chatTabs = chats
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

  const handleSend = () => {
    const trimmedMessage = messageInput.trim();
    if (!trimmedMessage) return;

    onSend(trimmedMessage, activeChat.recipientId);
    setMessageInput("");
  };

  return (
    <>
      <div
        className={`card ${styles.communicatorLayout}`}
      >
        <ActiveChat
          activeChat={activeChatView}
          messages={activeChatMessages}
          playerId={playerId}
          inputValue={messageInput}
          onInputChange={setMessageInput}
          onSend={handleSend}
          getPlayerName={getPlayerName}
        />

        <ChatTabsRail
          activeChatId={activeChatId}
          globalTab={globalTab}
          chatTabs={chatTabs}
          isExpanded={isSidebarExpanded}
          onSelectChat={setActiveChatId}
          onToggleExpanded={() => setIsSidebarExpanded((isExpanded) => !isExpanded)}
          onCreateChat={() => setIsCreateChatModalOpen(true)}
        />
      </div>

      {isCreateChatModalOpen && (
        <CreateChatModal
          players={players}
          playerId={playerId}
          onCreateChat={onCreateChat}
          onClose={() => setIsCreateChatModalOpen(false)}
        />
      )}
    </>
  );
};

export default TabbedCommunicator;
