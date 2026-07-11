import React from "react";
import { ChatTabViewModel } from "./chatViewTypes";

import styles from "./ChatTabsRail.module.css";
interface Props {
  activeChatId: string;
  globalTab: ChatTabViewModel;
  chatTabs: ChatTabViewModel[];
  isExpanded: boolean;
  onSelectChat: (chatId: string) => void;
  onToggleExpanded: () => void;
  onCreateChat: () => void;
}

const ChatTabsRail: React.FC<Props> = ({
  activeChatId,
  globalTab,
  chatTabs,
  isExpanded,
  onSelectChat,
  onToggleExpanded,
  onCreateChat,
}) => {
  const renderTab = (tab: ChatTabViewModel) => {
    const isActive = activeChatId === tab.id;

    return (
      <button
        key={tab.id}
        onClick={() => onSelectChat(tab.id)}
        className={[styles.tab, isActive ? styles.tabActive : ""].filter(Boolean).join(" ")}
      >
        <span className={styles.text2}>
          {tab.label}
        </span>
        <span className={styles.row}>
          {tab.unread > 0 && (
            <span
              className={styles.text}
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
      className={[
        styles.column,
        isExpanded ? styles.columnExpanded : styles.columnCollapsed,
      ].join(" ")}
    >
      <button
        type="button"
        onClick={onToggleExpanded}
        className={styles.toggleButton}
        aria-label={isExpanded ? "Collapse chat sidebar" : "Expand chat sidebar"}
        aria-expanded={isExpanded}
      >
        <span aria-hidden="true">{isExpanded ? "→" : "←"}</span>
      </button>

      <button
        onClick={onCreateChat}
        className={styles.button}
      >
        <span className={styles.newChatIcon}>+</span>
        <span className={styles.labelText}>New Chat</span>
      </button>

      <div className={styles.panel}>
        {renderTab(globalTab)}
        {chatTabs.map(renderTab)}
      </div>
    </aside>
  );
};

export default ChatTabsRail;
