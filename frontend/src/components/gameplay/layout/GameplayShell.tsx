import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import styles from "./GameplayShell.module.css";
import { updatePanelAttention, type PanelAttentionState } from "./phaseAttention";

interface Props {
  actionAttentionKey?: string;
  actionPanel: ReactNode;
  chatPanel: ReactNode;
  map: ReactNode;
  statusBar: ReactNode;
}

const GameplayShell = ({ actionAttentionKey = "", actionPanel, chatPanel, map, statusBar }: Props) => {
  const [actionsOpen, setActionsOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const actionToggleRef = useRef<HTMLButtonElement | null>(null);
  const chatToggleRef = useRef<HTMLButtonElement | null>(null);
  const [actionAttention, setActionAttention] = useState<PanelAttentionState>(() =>
    updatePanelAttention(undefined, { contentKey: actionAttentionKey, isOpen: actionsOpen }),
  );

  useEffect(() => {
    setActionAttention((previous) =>
      updatePanelAttention(previous, { contentKey: actionAttentionKey, isOpen: actionsOpen }),
    );
  }, [actionAttentionKey, actionsOpen]);

  const closePanelFromKeyboard = (
    event: KeyboardEvent<HTMLElement>,
    close: () => void,
    focusTarget: HTMLButtonElement | null,
  ) => {
    if (event.key !== "Escape") {
      return;
    }

    event.stopPropagation();
    close();
    focusTarget?.focus();
  };

  return (
    <div className={styles.shell}>
      {statusBar}
      <main className={styles.stage}>
        <div className={styles.map}>{map}</div>

        <button
          aria-expanded={actionsOpen}
          aria-controls="phase-actions-panel"
          aria-label={actionsOpen ? "Close phase actions" : "Open phase actions"}
          className={`${styles.toggle} ${styles.actionToggle}`}
          onClick={() => setActionsOpen((open) => !open)}
          ref={actionToggleRef}
          type="button"
        >
          {actionsOpen ? "Close" : "Actions"}
          {actionAttention.hasAttention && !actionsOpen && (
            <span aria-label="Phase actions have updates" className={styles.attentionDot} />
          )}
        </button>
        {actionsOpen && (
          <aside
            aria-label="Phase actions"
            className={`${styles.panel} ${styles.actionPanel}`}
            id="phase-actions-panel"
            onKeyDown={(event) => closePanelFromKeyboard(
              event,
              () => setActionsOpen(false),
              actionToggleRef.current,
            )}
          >
            {actionPanel}
          </aside>
        )}

        <button
          aria-expanded={chatOpen}
          aria-controls="village-chat-panel"
          aria-label={chatOpen ? "Close village chat" : "Open village chat"}
          className={`${styles.toggle} ${styles.chatToggle}`}
          onClick={() => setChatOpen((open) => !open)}
          ref={chatToggleRef}
          type="button"
        >
          {chatOpen ? "Close" : "Chat"}
        </button>
        {chatOpen && (
          <aside
            aria-label="Village chat"
            className={`${styles.panel} ${styles.chatPanel}`}
            id="village-chat-panel"
            onKeyDown={(event) => closePanelFromKeyboard(
              event,
              () => setChatOpen(false),
              chatToggleRef.current,
            )}
          >
            {chatPanel}
          </aside>
        )}
      </main>
    </div>
  );
};

export default GameplayShell;
