import React, { useState } from "react";
import { PublicPlayerDTO } from "../../../dtos/index";

import styles from "./CreateChatModal.module.css";
interface Props {
  players: PublicPlayerDTO[];
  playerId: string;
  onCreateChat: (name: string, memberIds: string[]) => void;
  onClose: () => void;
}

const CreateChatModal: React.FC<Props> = ({
  players,
  playerId,
  onCreateChat,
  onClose,
}) => {
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

  const handleCreate = () => {
    const trimmedChatName = chatName.trim();
    if (!trimmedChatName || selectedPlayerIds.length === 0) return;

    onCreateChat(trimmedChatName, selectedPlayerIds);
    resetAndClose();
  };

  const togglePlayer = (targetPlayerId: string, isSelected: boolean) => {
    if (isSelected) {
      setSelectedPlayerIds((current) => [...current, targetPlayerId]);
      return;
    }

    setSelectedPlayerIds((current) => current.filter((id) => id !== targetPlayerId));
  };

  return (
    <div
      className={styles.modalBackdrop}
    >
      <div
        className={styles.modalPanel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-chat-title"
      >
        <h3 id="create-chat-title">Create Chat</h3>

        <label htmlFor="create-chat-name">Chat name</label>
        <input
          id="create-chat-name"
          value={chatName}
          onChange={(event) => setChatName(event.target.value)}
          placeholder="Chat name"
          className={styles.nameInput}
        />

        <div>
          {availablePlayers.map((player) => (
            <label
              key={player.id}
              className={styles.playerOption}
            >
              <div
                className={styles.playerCheckbox}
              >
                <input
                  type="checkbox"
                  checked={selectedPlayerIds.includes(player.id)}
                  onChange={(event) => togglePlayer(player.id, event.target.checked)}
                />
              </div>

              <span>{player.name}</span>
            </label>
          ))}
        </div>

        <div
          className={styles.modalActions}
        >
          <button
            type="button"
            className="btn"
            onClick={handleCreate}
            disabled={!chatName.trim() || selectedPlayerIds.length === 0}
          >
            Create
          </button>

          <button type="button" className="btn" onClick={resetAndClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateChatModal;
