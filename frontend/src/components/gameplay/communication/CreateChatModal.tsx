import { useState, type KeyboardEvent, type MouseEvent } from "react";
import type { PublicPlayerDTO } from "../../../dtos";
import styles from "./CreateChatModal.module.css";

export interface CreateChatModalProps {
  players: PublicPlayerDTO[];
  playerId: string;
  onCreateChat: (name: string, memberIds: string[]) => void;
  onClose: () => void;
}

const CreateChatModal = ({
  players,
  playerId,
  onCreateChat,
  onClose,
}: CreateChatModalProps) => {
  const [chatName, setChatName] = useState("");
  const [selectedPlayerIds, setSelectedPlayerIds] = useState<string[]>([]);

  const availablePlayers = players
    .filter((player) => player.id !== playerId)
    .sort((a, b) => a.name.localeCompare(b.name));

  const resetAndClose = () => {
    setChatName("");
    setSelectedPlayerIds([]);
    onClose();
  };

  const trimmedChatName = chatName.trim();
  const isSubmitDisabled = !trimmedChatName || selectedPlayerIds.length === 0;

  const handleCreate = () => {
    if (isSubmitDisabled) {
      return;
    }

    onCreateChat(trimmedChatName, selectedPlayerIds);
    resetAndClose();
  };

  const togglePlayerSelection = (targetPlayerId: string, shouldSelect: boolean) => {
    setSelectedPlayerIds((current) =>
      shouldSelect
        ? [...current, targetPlayerId]
        : current.filter((id) => id !== targetPlayerId),
    );
  };

  const handleBackdropClick = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      resetAndClose();
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      resetAndClose();
    }
  };

  return (
    <div
      className={styles.modalBackdrop}
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      role="presentation"
    >
      <div
        aria-labelledby="create-chat-title"
        aria-modal="true"
        className={styles.modalPanel}
        role="dialog"
      >
        <h3 id="create-chat-title">Create Chat</h3>

        <label htmlFor="create-chat-name">Chat name</label>
        <input
          className={styles.nameInput}
          id="create-chat-name"
          onChange={(event) => setChatName(event.target.value)}
          placeholder="Chat name"
          type="text"
          value={chatName}
        />

        <div>
          {availablePlayers.map((player) => {
            const isPlayerSelected = selectedPlayerIds.includes(player.id);

            return (
              <label className={styles.playerOption} key={player.id}>
                <div className={styles.playerCheckbox}>
                  <input
                    checked={isPlayerSelected}
                    onChange={(event) =>
                      togglePlayerSelection(player.id, event.target.checked)
                    }
                    type="checkbox"
                  />
                </div>
                <span>{player.name}</span>
              </label>
            );
          })}
        </div>

        <div className={styles.modalActions}>
          <button
            className="btn"
            disabled={isSubmitDisabled}
            onClick={handleCreate}
            type="button"
          >
            Create
          </button>

          <button className="btn" onClick={resetAndClose} type="button">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateChatModal;
