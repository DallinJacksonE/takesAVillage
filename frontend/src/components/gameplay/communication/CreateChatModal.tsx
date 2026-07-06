import React, { useState } from "react";
import { PlayerDTO } from "../../../dtos/index";

interface Props {
  players: PlayerDTO[];
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
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.5)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1000,
      }}
    >
      <div
        style={{
          background: "white",
          padding: "20px",
          borderRadius: "8px",
          width: "400px",
          maxHeight: "80vh",
          overflowY: "auto",
        }}
      >
        <h3>Create Chat</h3>

        <input
          value={newChatName}
          onChange={(event) => setNewChatName(event.target.value)}
          placeholder="Chat name"
          style={{
            width: "100%",
            marginBottom: "15px",
          }}
        />

        <div>
          {otherPlayers.map((player) => (
            <label
              key={player.id}
              style={{
                display: "flex",
                alignItems: "center",
                marginBottom: "5px",
                color: "black",
              }}
            >
              <div
                style={{
                  width: "40px",
                  display: "flex",
                  justifyContent: "center",
                }}
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
          style={{
            display: "flex",
            gap: "10px",
            marginTop: "15px",
          }}
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
