import React, { useEffect, useRef } from "react";
import { ChatMessageDTO } from "../../../dtos/index";
import { ActiveChatViewModel } from "./chatViewTypes";

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
    <div style={{ display: "flex", flex: 1, minWidth: 0, flexDirection: "column" }}>
      <div
        ref={chatContainerRef}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "15px",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          background: "#fff",
        }}
      >
        {messages.length === 0 ? (
          <div style={{ textAlign: "center", color: "#888", fontStyle: "italic", marginTop: "20px" }}>
            No messages yet.
          </div>
        ) : (
          messages.map((message) => {
            const isMe = message.from_id === playerId;

            return (
              <div
                key={message.id}
                style={{ alignSelf: isMe ? "flex-end" : "flex-start", maxWidth: "80%" }}
              >
                {!isMe && activeChat.showSenderNames && (
                  <div
                    style={{
                      fontSize: "0.7rem",
                      color: "#666",
                      marginBottom: "2px",
                      marginLeft: "2px",
                    }}
                  >
                    {getPlayerName(message.from_id)}
                  </div>
                )}
                <div
                  style={{
                    background: isMe ? "#e3f2fd" : "#f1f3f4",
                    border: isMe ? "1px solid #bbdefb" : "1px solid #e0e0e0",
                    padding: "8px 12px",
                    borderRadius: "12px",
                    fontSize: "0.9rem",
                    wordWrap: "break-word",
                  }}
                >
                  {message.content}
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="send_bar">
        <input
          className="send_input"
          placeholder={`Message ${activeChat.label}...`}
          value={inputValue}
          onChange={(event) => onInputChange(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && onSend()}
        />
        <button className="btn send_button" onClick={onSend}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ActiveChat;
