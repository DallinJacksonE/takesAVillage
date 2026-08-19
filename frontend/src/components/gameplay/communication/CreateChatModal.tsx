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
  const [newChatName, setNewChatName] = useState("");
  const [selectedPlayers, setSelectedPlayers] = useState<string[]>([]);

  const otherPlayers = players
    .filter((player) => player.id !== playerId)
    .sort((a, b) => a.name.localeCompare(b.name));

  const resetAndClose = () => {
    setNewChatName("");
    setSelectedPlayers([]);
    onClose();
  };

  const handleCreate = () => {
    if (!newChatName.trim() || selectedPlayers.length === 0) return;

    onCreateChat(newChatName.trim(), selectedPlayers);
    resetAndClose();
  };

  const togglePlayer = (targetPlayerId: string, isSelected: boolean) => {
    if (isSelected) {
      setSelectedPlayers((current) => [...current, targetPlayerId]);
      return;
    }

    setSelectedPlayers((current) => current.filter((id) => id !== targetPlayerId));
  };

  return (
    <div
      className={styles.row4}
    >
      <div
        className={styles.panel}
      >
        <h3>Create Chat</h3>

        <input
          value={newChatName}
          onChange={(event) => setNewChatName(event.target.value)}
          placeholder="Chat name"
          className={styles.nameInput}
        />

        <div>
          {otherPlayers.map((player) => (
            <label
              key={player.id}
              className={styles.row3}
            >
              <div
                className={styles.row2}
              >
                <input
                  type="checkbox"
                  checked={selectedPlayers.includes(player.id)}
                  onChange={(event) => togglePlayer(player.id, event.target.checked)}
                />
              </div>

              <span>{player.name}</span>
            </label>
          ))}
        </div>

        <div
          className={styles.row}
        >
          <button
            className="btn"
            onClick={handleCreate}
            disabled={!newChatName.trim() || selectedPlayers.length === 0}
          >
            Create
          </button>

          <button className="btn" onClick={resetAndClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateChatModal;
