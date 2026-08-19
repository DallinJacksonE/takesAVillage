import { useState, type ReactNode } from "react";
import styles from "./GameplayShell.module.css";

interface Props {
  actionPanel: ReactNode;
  chatPanel: ReactNode;
  map: ReactNode;
  statusBar: ReactNode;
}

const GameplayShell = ({ actionPanel, chatPanel, map, statusBar }: Props) => {
  const [actionsOpen, setActionsOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <div className={styles.shell}>
      {statusBar}
      <main className={styles.stage}>
        <div className={styles.map}>{map}</div>

        <button
          aria-expanded={actionsOpen}
          aria-label={actionsOpen ? "Close phase actions" : "Open phase actions"}
          className={`${styles.toggle} ${styles.actionToggle}`}
          onClick={() => setActionsOpen((open) => !open)}
          type="button"
        >
          {actionsOpen ? "Close" : "Actions"}
        </button>
        {actionsOpen && (
          <aside aria-label="Phase actions" className={`${styles.panel} ${styles.actionPanel}`}>
            {actionPanel}
          </aside>
        )}

        <button
          aria-expanded={chatOpen}
          aria-label={chatOpen ? "Close village chat" : "Open village chat"}
          className={`${styles.toggle} ${styles.chatToggle}`}
          onClick={() => setChatOpen((open) => !open)}
          type="button"
        >
          {chatOpen ? "Close" : "Chat"}
        </button>
        {chatOpen && (
          <aside aria-label="Village chat" className={`${styles.panel} ${styles.chatPanel}`}>
            {chatPanel}
          </aside>
        )}
      </main>
    </div>
  );
};

export default GameplayShell;
