import React, { useEffect, useRef } from "react";
import { ChatMessageDTO } from "../../../dtos/index";
import { ActiveChatViewModel } from "./chatViewTypes";

import styles from "./ActiveChat.module.css";
interface Props {
  activeChat: ActiveChatViewModel;
  messages: ChatMessageDTO[];
  playerId: string;
  inputValue: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  getPlayerName: (playerId: string | undefined) => string;
}

const ActiveChat: React.FC<Props> = ({
  activeChat,
  messages,
  playerId,
  inputValue,
  onInputChange,
  onSend,
  getPlayerName,
}) => {
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages.length, activeChat.id]);

  return (
    <div className={styles.column2}>
      <div
        ref={chatContainerRef}
        className={styles.column}
      >
        {messages.length === 0 ? (
          <div className={styles.panel4}>
            No messages yet.
          </div>
        ) : (
          messages.map((message) => {
            const isMe = message.from_id === playerId;

            return (
              <div
                key={message.id}
                className={[styles.message, isMe ? styles.messageMine : styles.messageTheirs].join(" ")}
              >
                {!isMe && activeChat.showSenderNames && (
                  <div
                    className={styles.panel2}
                  >
                    {getPlayerName(message.from_id)}
                  </div>
                )}
                <div
                  className={[styles.bubble, isMe ? styles.bubbleMine : styles.bubbleTheirs].join(" ")}
                >
                  {message.content}
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className={styles.sendBar}>
        <input
          className={styles.sendInput}
          placeholder={`Message ${activeChat.label}...`}
          value={inputValue}
          onChange={(event) => onInputChange(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && onSend()}
        />
        <button className={`btn ${styles.sendButton}`} onClick={onSend}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ActiveChat;
