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
        type="button"
        key={tab.id}
        onClick={() => onSelectChat(tab.id)}
        className={[styles.tab, isActive ? styles.tabActive : ""].filter(Boolean).join(" ")}
      >
        <span className={styles.tabLabel}>
          {tab.label}
        </span>
        <span className={styles.unreadCount}>
          {tab.unread > 0 && (
            <span className={styles.unreadBadge}>
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
        styles.rail,
        isExpanded ? styles.railExpanded : styles.railCollapsed,
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
        type="button"
        onClick={onCreateChat}
        className={styles.createChatButton}
      >
        <span className={styles.createChatIcon} aria-hidden="true">+</span>
        <span className={styles.createChatLabel}>New Chat</span>
      </button>

      <div className={styles.tabList}>
        {renderTab(globalTab)}
        {chatTabs.map(renderTab)}
      </div>
    </aside>
  );
};

export default ChatTabsRail;
