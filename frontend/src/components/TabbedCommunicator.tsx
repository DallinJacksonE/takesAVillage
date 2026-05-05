import React, { useState, useEffect, useMemo } from "react";
import { MessageDTO, PlayerDTO, TextMessageDTO } from "../../../dtos/index";

interface Props {
  messages: MessageDTO[];
  playerId: string;
  players: PlayerDTO[];
  onSend: (payload: Record<string, any>) => void;
}

const TabbedCommunicator: React.FC<Props> = ({ messages, playerId, players, onSend }) => {
  const [activeTab, setActiveTab] = useState<string>("global");
  const [chatInput, setChatInput] = useState("");
  const [readMessages, setReadMessages] = useState<Set<string>>(new Set());

  // Filter down to only chat messages (ignore TRADE and EMPLOYMENT)
  const chatMessages = messages.filter((m) => m.type === "TEXT" || m.is_system) as TextMessageDTO[];

  // Mark visible messages as read when the tab changes or new messages arrive
  useEffect(() => {
    const newRead = new Set(readMessages);
    chatMessages.forEach(msg => {
      const isGlobal = !msg.to_id;
      const isCurrentPrivate = msg.from_id === activeTab || msg.to_id === activeTab;

      if ((activeTab === "global" && isGlobal) || (activeTab !== "global" && isCurrentPrivate)) {
        newRead.add(msg.id);
      }
    });
    setReadMessages(newRead);
  }, [messages, activeTab]);

  // Calculate unread counts for the tabs
  const getUnreadCount = (senderId: string) => {
    return chatMessages.filter(
      (m) => m.from_id === senderId && m.to_id === playerId && !readMessages.has(m.id)
    ).length;
  };

  // Sort players: Unread messages first, then alphabetical (or original order)
  const sortedPlayers = useMemo(() => {
    const others = players.filter(p => p.id !== playerId);
    return others.sort((a, b) => {
      const unreadA = getUnreadCount(a.id);
      const unreadB = getUnreadCount(b.id);

      if (unreadB !== unreadA) {
        return unreadB - unreadA; // Highest unread count goes to the front
      }
      return a.name.localeCompare(b.name); // Fallback to alphabetical sorting
    });
  }, [players, messages, readMessages, playerId]);

  const visibleMessages = chatMessages.filter((msg) => {
    if (activeTab === "global") {
      return !msg.to_id; // Global messages don't have a specific recipient
    }
    // Private messages between you and the active tab user
    return (msg.from_id === playerId && msg.to_id === activeTab) ||
      (msg.from_id === activeTab && msg.to_id === playerId);
  });

  const handleSendMessage = () => {
    if (!chatInput.trim()) return;

    const payload: Record<string, any> = {
      from_id: playerId,
      type: "TEXT",
      content: chatInput,
    };

    if (activeTab !== "global") {
      payload.to_id = activeTab;
    }

    onSend(payload);
    setChatInput("");
  };

  const getPlayerName = (id: string) => players.find((p) => p.id === id)?.name || "Unknown";

  return (
    <div className="card" style={{ flex: 1, margin: 0, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>

      {/* TABS ROW - Now a Side Scroller */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          overflowX: "auto",
          borderBottom: "2px solid #eee",
          paddingBottom: "10px",
          marginBottom: "10px",
          flexShrink: 0 // Prevents the tab row from shrinking vertically
        }}
      >
        <button
          className="btn-sm"
          style={{
            background: activeTab === "global" ? "#2196F3" : "#f0f0f0",
            color: activeTab === "global" ? "white" : "#333",
            fontWeight: "bold",
            flexShrink: 0, // Prevents button from squishing
            whiteSpace: "nowrap"
          }}
          onClick={() => setActiveTab("global")}
        >
          Global
        </button>

        {sortedPlayers.map((p) => {
          const unread = getUnreadCount(p.id);
          return (
            <button
              key={p.id}
              className="btn-sm"
              style={{
                position: "relative",
                background: activeTab === p.id ? "#2196F3" : "#f0f0f0",
                color: activeTab === p.id ? "white" : "#333",
                flexShrink: 0, // Prevents button from squishing
                whiteSpace: "nowrap" // Keeps the name on one line to enable horizontal scrolling
              }}
              onClick={() => setActiveTab(p.id)}
            >
              {p.name}
              {unread > 0 && (
                <span style={{
                  position: "absolute",
                  top: "-5px",
                  right: "-5px",
                  background: "#f44336",
                  color: "white",
                  borderRadius: "50%",
                  padding: "2px 6px",
                  fontSize: "0.6rem",
                  fontWeight: "bold"
                }}>
                  {unread}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* CHAT HISTORY */}
      <div style={{ flex: 1, overflowY: "auto", background: "#fafafa", padding: "10px", borderRadius: "4px", border: "1px solid #eee", display: "flex", flexDirection: "column", gap: "8px" }}>
        {visibleMessages.length === 0 ? (
          <p style={{ textAlign: "center", color: "#999", fontStyle: "italic", marginTop: "auto", marginBottom: "auto" }}>
            No messages yet.
          </p>
        ) : (
          visibleMessages.map((msg) => {
            const isMe = msg.from_id === playerId;
            if (msg.is_system) {
              return <div key={msg.id} style={{ textAlign: "center", fontSize: "0.8rem", color: "#888", fontStyle: "italic" }}>{msg.content}</div>;
            }
            return (
              <div key={msg.id} style={{ alignSelf: isMe ? "flex-end" : "flex-start", maxWidth: "80%" }}>
                {!isMe && activeTab === "global" && (
                  <div style={{ fontSize: "0.7rem", color: "#666", marginBottom: "2px", marginLeft: "2px" }}>{getPlayerName(msg.from_id)}</div>
                )}
                <div style={{ background: isMe ? "#e3f2fd" : "#fff", border: isMe ? "1px solid #bbdefb" : "1px solid #ddd", padding: "8px 12px", borderRadius: "12px", fontSize: "0.9rem", wordWrap: "break-word" }}>
                  {msg.content}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* INPUT ROW */}
      <div style={{ display: "flex", gap: "10px", marginTop: "10px", flexShrink: 0 }}>
        <input
          style={{ flex: 1, padding: "8px", borderRadius: "4px", border: "1px solid #ccc", minWidth: 0 }}
          placeholder={`Message ${activeTab === "global" ? "everyone" : getPlayerName(activeTab)}...`}
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
        />
        <button className="btn success" style={{ flexShrink: 0 }} onClick={handleSendMessage}>Send</button>
      </div>

    </div>
  );
};

export default TabbedCommunicator;
