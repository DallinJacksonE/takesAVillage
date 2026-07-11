import React, { useEffect, useMemo, useState } from "react";
import { ChatDTO, ChatMessageDTO, PlayerDTO } from "../../../dtos/index";
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
  getMessageTime,
} from "./chatViewTypes";

interface Props {
  messages: ChatMessageDTO[];
  playerId: string;
  players: PlayerDTO[];
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
  const [chatInput, setChatInput] = useState("");
  const [readMessages, setReadMessages] = useState<Set<string>>(new Set());
  const [showCreateChat, setShowCreateChat] = useState(false);
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(false);
  const getPlayerName = usePlayerName();

  const chatIds = useMemo(() => new Set(chats.map((chat) => chat.id)), [chats]);

  useEffect(() => {
    if (activeChatId !== GLOBAL_CHAT_ID && !chatIds.has(activeChatId)) {
      setActiveChatId(GLOBAL_CHAT_ID);
    }
  }, [activeChatId, chatIds]);

  const displayMessages = useMemo(() => {
    return messages.filter((message) => {
      if (activeChatId === GLOBAL_CHAT_ID) {
        return message.to_id === GLOBAL_RECIPIENT_ID;
      }

      return message.to_id === activeChatId;
    });
  }, [messages, activeChatId]);

  useEffect(() => {
    setReadMessages((previous) => {
      let hasChanges = false;
      const updated = new Set(previous);

      for (const message of displayMessages) {
        if (!updated.has(message.id)) {
          updated.add(message.id);
          hasChanges = true;
        }
      }

      return hasChanges ? updated : previous;
    });
  }, [displayMessages]);

  const getGlobalUnreadCount = () => {
    return messages.filter(
      (message) =>
        message.to_id === GLOBAL_RECIPIENT_ID &&
        message.from_id !== playerId &&
        !readMessages.has(message.id),
    ).length;
  };

  const getChatUnreadCount = (chatId: string) => {
    return messages.filter(
      (message) =>
        message.to_id === chatId &&
        message.from_id !== playerId &&
        !readMessages.has(message.id),
    ).length;
  };

  const globalTab: ChatTabViewModel = {
    id: GLOBAL_CHAT_ID,
    label: "Village Square",
    unread: getGlobalUnreadCount(),
    lastMessageTime: messages
      .filter((message) => message.to_id === GLOBAL_RECIPIENT_ID)
      .reduce((latest, message) => Math.max(latest, getMessageTime(message)), 0),
  };

  const chatTabs = chats
    .map((chat) => ({
      id: chat.id,
      label: `#${chat.name}`,
      unread: getChatUnreadCount(chat.id),
      lastMessageTime: getChatLastMessageTime(messages, chat.id),
    }))
    .sort((a, b) => b.lastMessageTime - a.lastMessageTime);

  const activeChat = getActiveChatView(activeChatId, chats);

  const handleSend = () => {
    if (!chatInput.trim()) return;

    onSend(chatInput.trim(), activeChat.recipientId);
    setChatInput("");
  };

  return (
    <>
      <div
        className={`card ${styles.row}`}
        
      >
        <ActiveChat
          activeChat={activeChat}
          messages={displayMessages}
          playerId={playerId}
          inputValue={chatInput}
          onInputChange={setChatInput}
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
          onCreateChat={() => setShowCreateChat(true)}
        />
      </div>

      {showCreateChat && (
        <CreateChatModal
          players={players}
          playerId={playerId}
          onCreateChat={onCreateChat}
          onClose={() => setShowCreateChat(false)}
        />
      )}
    </>
  );
};

export default TabbedCommunicator;
