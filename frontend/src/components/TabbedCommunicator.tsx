import React, { useState, useEffect, useRef } from "react";
import { ChatMessageDTO, PlayerDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface ChatDTO {
  id: string;
  name: string;
  member_ids: string[];
}

interface Props {
  messages: ChatMessageDTO[];
  playerId: string;
  players: PlayerDTO[];
  chats: ChatDTO[];

  onSend: (content: string, toId: string) => void;

  onCreateChat: (
    name: string,
    memberIds: string[]
  ) => void;
}

const TabbedCommunicator: React.FC<Props> = ({
  messages,
  playerId,
  players,
  chats,
  onSend,
  onCreateChat
}) => {
  const [activeTab, setActiveTab] = useState<string>("global"); // "global", playerId, or groupId
  const [chatInput, setChatInput] = useState("");
  const [readMessages, setReadMessages] = useState<Set<string>>(new Set());
  const getPlayerName = usePlayerName();
  const playerIds = new Set(players.map(p => p.id));

  const isPlayerTab = (id: string) =>
    playerIds.has(id);

  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [showCreateChat, setShowCreateChat] = useState(false);
  const [newChatName, setNewChatName] = useState("");
  const [selectedPlayers, setSelectedPlayers] = useState<string[]>([]);

  // Mark visible messages as read when the tab changes or new messages arrive
  useEffect(() => {
    setReadMessages(prev => {
      let hasChanges = false;
      const updated = new Set(prev);

      for (const msg of messages) {
        const isGlobal = msg.to_id === "GLOBAL";

        const isPrivate =
          isPlayerTab(activeTab) &&
          (
            (msg.from_id === activeTab && msg.to_id === playerId) ||
            (msg.from_id === playerId && msg.to_id === activeTab)
          );

        const isGroup =
          chats.some(c => c.id === activeTab) &&
          msg.to_id === activeTab;

        if (
          (activeTab === "global" && isGlobal) ||
          isPrivate ||
          isGroup
        ) {
          // Only flag as changed if it wasn't already in the Set
          if (!updated.has(msg.id)) {
            updated.add(msg.id);
            hasChanges = true;
          }
        }
      }

      // CRITICAL: If no new messages were marked as read, return the original Set reference.
      // This tells React to cancel the re-render, instantly breaking the infinite loop!
      return hasChanges ? updated : prev;
    });
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

  const getGlobalUnreadCount = () => {
    return messages.filter(m =>
      m.to_id === "GLOBAL" &&
      m.from_id !== playerId &&
      !readMessages.has(m.id)
    ).length;
  };

  const getGroupUnreadCount = (chatId: string) => {
    return messages.filter(
      m =>
        m.to_id === chatId &&
        m.from_id !== playerId &&
        !readMessages.has(m.id)
    ).length;
  };

  const handleSend = () => {
    if (!chatInput.trim()) return;
    onSend(chatInput, activeTab === "global" ? "GLOBAL" : activeTab);
    setChatInput("");
  };

  // Ensure we don't try to render tabs for ourselves
  const otherPlayers = players
    .filter(p => p.id !== playerId)
    .sort((a, b) => {
      const unreadA = getUnreadCount(a.id, playerId);
      const unreadB = getUnreadCount(b.id, playerId);

      return unreadB - unreadA;
    });

  const playerTabs = otherPlayers.map(p => ({
    id: p.id,
    label: p.name,
    unread: getUnreadCount(p.id, playerId),
    type: "player" as const
  }));

  const chatTabs = chats.map(c => ({
    id: c.id,
    label: `#${c.name}`,
    unread: getGroupUnreadCount(c.id),
    type: "chat" as const
  }));

  const sortedTabs = [...playerTabs, ...chatTabs].sort(
    (a, b) => b.unread - a.unread
  );

  // Filter messages for the currently active tab
  const displayMessages = messages.filter(msg => {
    if (activeTab === "global") {
      return msg.to_id === "GLOBAL";
    }

    // private chat
    if (playerIds.has(activeTab)) {
      return (
        (msg.from_id === activeTab && msg.to_id === playerId) ||
        (msg.from_id === playerId && msg.to_id === activeTab)
      );
    }

    // group chat (NOW uses to_id ONLY)
    return msg.to_id === activeTab;
  });

  // 2. Trigger the instant snap ONLY when the amount of messages changes
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [displayMessages.length]); // <-- Check the length, not the array reference

  return (
  <>
    <div className="card" style={{
      display: "flex",
      flexDirection: "column",
      height: "100%",
      minHeight: "337px",
      maxHeight: "337px",
      padding: 0,
      overflow: "hidden"
    }}>
      {/* TABS ROW */}
      <div
        style={{
          display: "flex",
          overflowX: "auto",
          borderBottom: "1px solid #eee",
          background: "#ddd8d8",

          flexShrink: 0,
          minHeight: "40px",
          maxHeight: "40px"
        }}
      >
        <button
          style={{
            flexShrink: 0,
            padding: "10px 15px",
            border: "none",
            background: activeTab === "global" ? "#fff" : "transparent",
            borderBottom: activeTab === "global"
              ? "3px solid #2196F3"
              : "3px solid transparent",
            cursor: "pointer",
            fontWeight: "normal",
            // SAME STRUCTURE AS PLAYER TABS
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            minWidth: "140px"
          }}
          onClick={() => setActiveTab("global")}
        >
          {/* left spacer */}
          <span style={{ width: "20px" }} />

          {/* center label */}
          <span style={{ whiteSpace: "nowrap" }}>
            Village Square
          </span>

          {/* right badge */}
          <span style={{ width: "20px", display: "flex", justifyContent: "center" }}>
            {getGlobalUnreadCount() > 0 && (
              <span
                style={{
                  background: "red",
                  color: "white",
                  borderRadius: "10px",
                  padding: "2px 6px",
                  fontSize: "0.7rem",
                  whiteSpace: "nowrap"
                }}
              >
                {getGlobalUnreadCount()}
              </span>
            )}
          </span>
        </button>
        {sortedTabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              flexShrink: 0,
              padding: "10px 15px",
              border: "none",
              background: activeTab === tab.id ? "#fff" : "transparent",
              borderBottom:
                activeTab === tab.id
                  ? "3px solid #2196F3"
                  : "3px solid transparent",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              minWidth: "140px"
            }}
          >
            <span style={{ width: "24px" }} />
            <span>{tab.label}</span>

            <span style={{ width: "24px", display: "flex", justifyContent: "center" }}>
              {tab.unread > 0 && (
                <span style={{
                  background: "red",
                  color: "white",
                  borderRadius: "10px",
                  padding: "2px 6px",
                  fontSize: "0.7rem"
                }}>
                  {tab.unread}
                </span>
              )}
            </span>
          </button>
        ))}

        <button
          onClick={() => setShowCreateChat(true)}
          style={{
            flexShrink: 0,
            padding: "10px 15px",
            border: "none",
            background: "transparent",
            cursor: "pointer",
            fontWeight: "bold",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            minWidth: "120px"
          }}
        >
          <span style={{ width: "24px" }} />
          <span>+ Chat</span>
          <span style={{ width: "24px" }} />
        </button>
      </div>

      {/* CHAT AREA */}
      <div
        ref={chatContainerRef} // <-- Attach the ref here
        style={{ flex: 1, overflowY: "auto", padding: "15px", display: "flex", flexDirection: "column", gap: "10px", background: "#fff" }}
      >
        {displayMessages.length === 0 ? (
          <div style={{ textAlign: "center", color: "#888", fontStyle: "italic", marginTop: "20px" }}>
            No messages yet.
          </div>
        ) : (
          displayMessages.map((msg) => {
            const isMe = msg.from_id === playerId;
            return (
              <div key={msg.id} style={{ alignSelf: isMe ? "flex-end" : "flex-start", maxWidth: "80%" }}>
                {!isMe &&
                (activeTab === "global" || msg.to_id !== playerId) && (
                <div
                  style={{
                    fontSize: "0.7rem",
                    color: "#666",
                    marginBottom: "2px",
                    marginLeft: "2px"
                  }}
                >
                  {getPlayerName(msg.from_id)}
                </div>
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
      <div className="send_bar">
        <input
          className="send_input"
          placeholder={`Message ${
            activeTab === "global"
              ? "everyone"
              : isPlayerTab(activeTab)
                ? getPlayerName(activeTab)
                : chats.find(c => c.id === activeTab)?.name ?? "group"
          }...`}
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button className="btn send_button" onClick={handleSend}>
          Send
        </button>
      </div>
    </div>

    {showCreateChat && (
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.5)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          zIndex: 1000
        }}
      >
        <div
          style={{
            background: "white",
            padding: "20px",
            borderRadius: "8px",
            width: "400px",
            maxHeight: "80vh",
            overflowY: "auto"
          }}
        >
          <h3>Create Group Chat</h3>

          <input
            value={newChatName}
            onChange={e => setNewChatName(e.target.value)}
            placeholder="Chat name"
            style={{
              width: "100%",
              marginBottom: "15px"
            }}
          />

          <div>
            {otherPlayers.map(player => (
              <label
                key={player.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  marginBottom: "5px",
                  color: "black"
                }}
              >
                <div
                  style={{
                    width: "40px",
                    display: "flex",
                    justifyContent: "center"
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedPlayers.includes(player.id)}
                    onChange={e => {
                      if (e.target.checked) {
                        setSelectedPlayers(prev => [...prev, player.id]);
                      } else {
                        setSelectedPlayers(prev =>
                          prev.filter(id => id !== player.id)
                        );
                      }
                    }}
                  />
                </div>

                <span>{player.name}</span>
              </label>
            ))}
          </div>

          <div
            style={{
              display: "flex",
              gap: "10px",
              marginTop: "15px"
            }}
          >
            <button
              className="btn"
              onClick={() => {
                if (!newChatName.trim()) return;

                onCreateChat(
                  newChatName,
                  selectedPlayers
                );

                setShowCreateChat(false);
                setNewChatName("");
                setSelectedPlayers([]);
              }}
            >
              Create
            </button>

            <button
              className="btn"
              onClick={() => {
                setShowCreateChat(false);
                setNewChatName("");
                setSelectedPlayers([]);
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    )}
  </>
);
};

export default TabbedCommunicator;
