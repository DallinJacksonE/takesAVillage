import React, { useState, useEffect } from "react";
import { ChatMessageDTO, PlayerDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  messages: ChatMessageDTO[];
  playerId: string;
  players: PlayerDTO[];
  onSend: (content: string, toId: string) => void;
}

const TabbedCommunicator: React.FC<Props> = ({ messages = [], playerId, players, onSend }) => {
  const [activeTab, setActiveTab] = useState<string>("global");
  const [chatInput, setChatInput] = useState("");
  const [readMessages, setReadMessages] = useState<Set<string>>(new Set());
  const getPlayerName = usePlayerName();

  // Mark visible messages as read when the tab changes or new messages arrive
  useEffect(() => {
    const newRead = new Set(readMessages);
    messages.forEach(msg => {
      const isGlobal = msg.to_id === "GLOBAL";
      const isCurrentPrivate = msg.from_id === activeTab || msg.to_id === activeTab;

      if ((activeTab === "global" && isGlobal) || (activeTab !== "global" && isCurrentPrivate)) {
        newRead.add(msg.id);
      }
    });
    setReadMessages(newRead);
  }, [messages, activeTab]);

  // Calculate unread counts for the tabs
  const getUnreadCount = (senderId: string, toId: string) => {
    return messages.filter(
      m =>
        m.from_id === senderId &&
        m.to_id === toId &&
        !readMessages.has(m.id)
    ).length;
  };

  const handleSend = () => {
    if (!chatInput.trim()) return;
    onSend(chatInput, activeTab === "global" ? "GLOBAL" : activeTab);
    setChatInput("");
  };

  // Ensure we don't try to render tabs for ourselves
  const otherPlayers = players.filter(p => p.id !== playerId);

  // Filter messages for the currently active tab
  const displayMessages = messages.filter(msg => {
    if (activeTab === "global") {
      return msg.to_id === "GLOBAL";
    }
    return (msg.from_id === activeTab && msg.to_id === playerId) ||
      (msg.from_id === playerId && msg.to_id === activeTab);
  });

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", height: "100%", maxHeight: "500px", padding: 0, overflow: "hidden" }}>
      {/* TABS ROW */}
      <div style={{ display: "flex", overflowX: "auto", borderBottom: "1px solid #eee", background: "#fafafa" }}>
        <button
          style={{
            flexShrink: 0,
            padding: "10px 15px",
            border: "none",
            background: activeTab === "global" ? "#fff" : "transparent",
            borderBottom: activeTab === "global" ? "3px solid #2196F3" : "3px solid transparent",
            cursor: "pointer",
            fontWeight: activeTab === "global" ? "bold" : "normal"
          }}
          onClick={() => setActiveTab("global")}
        >
          Village Square
        </button>
        {otherPlayers.map(p => {
          const unread = getUnreadCount(p.id, playerId);
          return (
            <button
              key={p.id}
              style={{
                flexShrink: 0,
                padding: "10px 15px",
                border: "none",
                background: activeTab === p.id ? "#fff" : "transparent",
                borderBottom: activeTab === p.id ? "3px solid #2196F3" : "3px solid transparent",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "5px",
                fontWeight: activeTab === p.id ? "bold" : "normal"
              }}
              onClick={() => setActiveTab(p.id)}
            >
              {p.name} {unread > 0 && <span style={{ background: "red", color: "white", borderRadius: "10px", padding: "2px 6px", fontSize: "0.7rem" }}>{unread}</span>}
            </button>
          );
        })}
      </div>

      {/* CHAT AREA */}
      <div style={{ flex: 1, overflowY: "auto", padding: "15px", display: "flex", flexDirection: "column", gap: "10px", background: "#fff" }}>
        {displayMessages.length === 0 ? (
          <div style={{ textAlign: "center", color: "#888", fontStyle: "italic", marginTop: "20px" }}>
            No messages yet.
          </div>
        ) : (
          displayMessages.map((msg) => {
            const isMe = msg.from_id === playerId;
            return (
              <div key={msg.id} style={{ alignSelf: isMe ? "flex-end" : "flex-start", maxWidth: "80%" }}>
                {!isMe && activeTab === "global" && (
                  <div style={{ fontSize: "0.7rem", color: "#666", marginBottom: "2px", marginLeft: "2px" }}>{getPlayerName(msg.from_id)}</div>
                )}
                <div style={{ background: isMe ? "#e3f2fd" : "#f1f3f4", border: isMe ? "1px solid #bbdefb" : "1px solid #e0e0e0", padding: "8px 12px", borderRadius: "12px", fontSize: "0.9rem", wordWrap: "break-word" }}>
                  {msg.content}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* INPUT ROW */}
      <div style={{ display: "flex", gap: "10px", padding: "10px", borderTop: "1px solid #eee", background: "#fafafa" }}>
        <input
          style={{ flex: 1, padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
          placeholder={`Message ${activeTab === "global" ? "everyone" : getPlayerName(activeTab)}...`}
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button className="btn" style={{ padding: "8px 16px" }} onClick={handleSend}>
          Send
        </button>
      </div>
    </div>
  );
};

export default TabbedCommunicator;
