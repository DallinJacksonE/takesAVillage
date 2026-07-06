import React from "react";
import { ChatTabViewModel } from "./chatViewTypes";

interface Props {
  activeChatId: string;
  globalTab: ChatTabViewModel;
  chatTabs: ChatTabViewModel[];
  onSelectChat: (chatId: string) => void;
  onCreateChat: () => void;
}

const ChatTabsRail: React.FC<Props> = ({
  activeChatId,
  globalTab,
  chatTabs,
  onSelectChat,
  onCreateChat,
}) => {
  const renderTab = (tab: ChatTabViewModel) => {
    const isActive = activeChatId === tab.id;

    return (
      <button
        key={tab.id}
        onClick={() => onSelectChat(tab.id)}
        style={{
          width: "100%",
          padding: "10px 12px",
          border: "none",
          borderLeft: isActive ? "4px solid #2196F3" : "4px solid transparent",
          background: isActive ? "#fff" : "transparent",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "8px",
          textAlign: "left",
          color: "#333",
        }}
      >
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {tab.label}
        </span>
        <span style={{ width: "28px", display: "flex", justifyContent: "center", flexShrink: 0 }}>
          {tab.unread > 0 && (
            <span
              style={{
                background: "red",
                color: "white",
                borderRadius: "10px",
                padding: "2px 6px",
                fontSize: "0.7rem",
                whiteSpace: "nowrap",
              }}
            >
              {tab.unread}
            </span>
          )}
        </span>
      </button>
    );
  };

  return (
    <aside
      style={{
        width: "150px",
        flexShrink: 0,
        borderLeft: "1px solid #eee",
        background: "#ddd8d8",
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
      }}
    >
      <button
        onClick={onCreateChat}
        style={{
          padding: "10px 12px",
          border: "none",
          borderBottom: "1px solid #c9c3c3",
          background: "#f7f7f7",
          cursor: "pointer",
          fontWeight: "bold",
          color: "#333",
        }}
      >
        + New Chat
      </button>

      <div style={{ overflowY: "auto", minHeight: 0 }}>
        {renderTab(globalTab)}
        {chatTabs.map(renderTab)}
      </div>
    </aside>
  );
};

export default ChatTabsRail;
