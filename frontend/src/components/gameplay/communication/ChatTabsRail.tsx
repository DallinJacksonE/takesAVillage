import React from "react";
import { ChatTabViewModel } from "./chatViewTypes";

import styles from "./ChatTabsRail.module.css";
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
      className={styles.column}
    >
      <button
        onClick={onCreateChat}
        className={styles.button}
      >
        + New Chat
      </button>

      <div className={styles.panel}>
        {renderTab(globalTab)}
        {chatTabs.map(renderTab)}
      </div>
    </aside>
  );
};

export default ChatTabsRail;
