import type { ChatTabViewModel } from "./chatViewTypes";
import styles from "./ChatTabsRail.module.css";

export interface ChatTabsRailProps {
  activeChatId: string;
  globalTab: ChatTabViewModel;
  chatTabs: ChatTabViewModel[];
  isExpanded: boolean;
  onSelectChat: (chatId: string) => void;
  onToggleExpanded: () => void;
  onCreateChat: () => void;
}

const ChatTabsRail = ({
  activeChatId,
  globalTab,
  chatTabs,
  isExpanded,
  onSelectChat,
  onToggleExpanded,
  onCreateChat,
}: ChatTabsRailProps) => {
  const renderTab = (tab: ChatTabViewModel) => {
    const isActive = activeChatId === tab.id;
    const tabClassName = isActive
      ? `${styles.tab} ${styles.tabActive}`
      : styles.tab;

    return (
      <button
        aria-selected={isActive}
        className={tabClassName}
        key={tab.id}
        onClick={() => onSelectChat(tab.id)}
        role="tab"
        type="button"
      >
        <span className={styles.tabLabel}>{tab.label}</span>
        <span className={styles.unreadCount}>
          {tab.unread > 0 && (
            <span className={styles.unreadBadge}>{tab.unread}</span>
          )}
        </span>
      </button>
    );
  };

  const railClassName = `${styles.rail} ${
    isExpanded ? styles.railExpanded : styles.railCollapsed
  }`;

  return (
    <aside className={railClassName}>
      <button
        aria-expanded={isExpanded}
        aria-label={isExpanded ? "Collapse chat sidebar" : "Expand chat sidebar"}
        className={styles.toggleButton}
        onClick={onToggleExpanded}
        type="button"
      >
        <span aria-hidden="true">{isExpanded ? "→" : "←"}</span>
      </button>

      <button
        className={styles.createChatButton}
        onClick={onCreateChat}
        type="button"
      >
        <span aria-hidden="true" className={styles.createChatIcon}>
          +
        </span>
        <span className={styles.createChatLabel}>New Chat</span>
      </button>

      <div className={styles.tabList} role="tablist">
        {renderTab(globalTab)}
        {chatTabs.map(renderTab)}
      </div>
    </aside>
  );
};

export default ChatTabsRail;
