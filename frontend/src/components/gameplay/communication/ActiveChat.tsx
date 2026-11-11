import { useEffect, useRef, type KeyboardEvent } from "react";
import type { ChatMessageDTO } from "../../../dtos";
import type { ActiveChatViewModel } from "./chatViewTypes";
import styles from "./ActiveChat.module.css";

export interface ActiveChatProps {
  activeChat: ActiveChatViewModel;
  messages: ChatMessageDTO[];
  playerId: string;
  inputValue: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  getPlayerName: (playerId: string | undefined) => string;
}

const ActiveChat = ({
  activeChat,
  messages,
  playerId,
  inputValue,
  onInputChange,
  onSend,
  getPlayerName,
}: ActiveChatProps) => {
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = chatContainerRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, [messages.length, activeChat.id]);

  const memberDisplayNames = activeChat.memberIds?.length
    ? activeChat.memberIds.map(getPlayerName).join(" · ")
    : "No members";

  const handleInputKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      onSend();
    }
  };

  return (
    <div className={styles.chatPanel}>
      <header className={styles.chatHeader}>
        <span className={styles.eyebrow}>Members</span>
        <span className={styles.memberNames}>{memberDisplayNames}</span>
      </header>

      <div
        aria-label="Message history"
        className={styles.messageList}
        ref={chatContainerRef}
      >
        {messages.length === 0 ? (
          <div className={styles.emptyState}>No messages yet.</div>
        ) : (
          messages.map((message) => {
            const isSentByMe = message.from_id === playerId;
            const messageClassName = `${styles.message} ${
              isSentByMe ? styles.messageMine : styles.messageTheirs
            }`;
            const bubbleClassName = `${styles.bubble} ${
              isSentByMe ? styles.bubbleMine : styles.bubbleTheirs
            }`;

            return (
              <div className={messageClassName} key={message.id}>
                {!isSentByMe && activeChat.showSenderNames && (
                  <div className={styles.senderName}>
                    {getPlayerName(message.from_id)}
                  </div>
                )}
                <div className={bubbleClassName}>{message.content}</div>
              </div>
            );
          })
        )}
      </div>

      <div className={styles.sendBar}>
        <input
          className={styles.sendInput}
          onChange={(event) => onInputChange(event.target.value)}
          onKeyDown={handleInputKeyDown}
          placeholder={`Message ${activeChat.label}...`}
          type="text"
          value={inputValue}
        />
        <button
          className={`btn ${styles.sendButton}`}
          onClick={onSend}
          type="button"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ActiveChat;
