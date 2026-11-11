import {
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import styles from "./GameplayShell.module.css";
import {
  updatePanelAttention,
  type PanelAttentionState,
} from "./phaseAttention";

const SCROLL_TO_ACTION_DELAY_MS = 100;

export interface GameplayShellProps {
  actionAttentionKey?: string;
  chatAttentionKey?: string;
  autoOpenActionsKey?: string;
  actionPanel: ReactNode;
  chatPanel: ReactNode;
  map: ReactNode;
  statusBar: ReactNode;
}

const GameplayShell = ({
  actionAttentionKey = "",
  chatAttentionKey = "",
  autoOpenActionsKey = "",
  actionPanel,
  chatPanel,
  map,
  statusBar,
}: GameplayShellProps) => {
  const [actionsOpen, setActionsOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  const actionToggleRef = useRef<HTMLButtonElement | null>(null);
  const chatToggleRef = useRef<HTMLButtonElement | null>(null);

  const [actionAttention, setActionAttention] = useState<PanelAttentionState>(
    () =>
      updatePanelAttention(undefined, {
        contentKey: actionAttentionKey,
        isOpen: actionsOpen,
      }),
  );
  const [chatAttention, setChatAttention] = useState<PanelAttentionState>(() =>
    updatePanelAttention(undefined, {
      contentKey: chatAttentionKey,
      isOpen: chatOpen,
    }),
  );

  useEffect(() => {
    setActionAttention((previous) =>
      updatePanelAttention(previous, {
        contentKey: actionAttentionKey,
        isOpen: actionsOpen,
      }),
    );
  }, [actionAttentionKey, actionsOpen]);

  useEffect(() => {
    setChatAttention((previous) =>
      updatePanelAttention(previous, {
        contentKey: chatAttentionKey,
        isOpen: chatOpen,
      }),
    );
  }, [chatAttentionKey, chatOpen]);

  useEffect(() => {
    if (!autoOpenActionsKey) {
      return;
    }

    setActionsOpen(true);

    const scrollTimeoutId = setTimeout(() => {
      const actionIds = autoOpenActionsKey.split(",");
      for (const actionId of actionIds) {
        const actionElement = document.getElementById(`action-item-${actionId}`);
        if (actionElement) {
          actionElement.scrollIntoView({ behavior: "smooth", block: "center" });
          break;
        }
      }
    }, SCROLL_TO_ACTION_DELAY_MS);

    return () => clearTimeout(scrollTimeoutId);
  }, [autoOpenActionsKey]);

  const handleToggleActions = () => setActionsOpen((isOpen) => !isOpen);
  const handleCloseActions = () => setActionsOpen(false);

  const handleToggleChat = () => setChatOpen((isOpen) => !isOpen);
  const handleCloseChat = () => setChatOpen(false);

  const handlePanelKeyDown = (
    event: KeyboardEvent<HTMLElement>,
    closePanel: () => void,
    restoreFocusTarget: HTMLButtonElement | null,
  ) => {
    if (event.key !== "Escape") {
      return;
    }

    event.stopPropagation();
    closePanel();
    restoreFocusTarget?.focus();
  };

  const shouldShowActionAttention = actionAttention.hasAttention && !actionsOpen;
  const shouldShowChatAttention = chatAttention.hasAttention && !chatOpen;

  return (
    <div className={styles.shell}>
      {statusBar}
      <main className={styles.stage}>
        <div className={styles.map}>{map}</div>

        <button
          aria-controls="phase-actions-panel"
          aria-expanded={actionsOpen}
          aria-label={actionsOpen ? "Close phase actions" : "Open phase actions"}
          className={`${styles.toggle} ${styles.actionToggle}`}
          onClick={handleToggleActions}
          ref={actionToggleRef}
          type="button"
        >
          {actionsOpen ? "Close" : "Actions"}
          {shouldShowActionAttention && (
            <span
              aria-label="Phase actions have updates"
              className={styles.attentionDot}
            />
          )}
        </button>
        {actionsOpen && (
          <aside
            aria-label="Phase actions"
            className={`${styles.panel} ${styles.actionPanel}`}
            id="phase-actions-panel"
            onKeyDown={(event) =>
              handlePanelKeyDown(
                event,
                handleCloseActions,
                actionToggleRef.current,
              )
            }
          >
            {actionPanel}
          </aside>
        )}

        <button
          aria-controls="village-chat-panel"
          aria-expanded={chatOpen}
          aria-label={chatOpen ? "Close village chat" : "Open village chat"}
          className={`${styles.toggle} ${styles.chatToggle}`}
          onClick={handleToggleChat}
          ref={chatToggleRef}
          type="button"
        >
          {chatOpen ? "Close" : "Chat"}
          {shouldShowChatAttention && (
            <span
              aria-label="New chat messages"
              className={styles.attentionDot}
            />
          )}
        </button>
        {chatOpen && (
          <aside
            aria-label="Village chat"
            className={`${styles.panel} ${styles.chatPanel}`}
            id="village-chat-panel"
            onKeyDown={(event) =>
              handlePanelKeyDown(
                event,
                handleCloseChat,
                chatToggleRef.current,
              )
            }
          >
            {chatPanel}
          </aside>
        )}
      </main>
    </div>
  );
};

export default GameplayShell;
