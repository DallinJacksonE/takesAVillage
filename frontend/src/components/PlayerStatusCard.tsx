import React from "react";
import { GameStateDTO } from "../../../dtos/index";
import { useGameState } from "./hooks/useGameState"; // Import the hook


const PlayerStatusCard: React.FC = () => {
  const gameState = useGameState();
  const { me } = gameState;
  return (
    <div
      className='card bar'
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "1rem",
        marginBottom: "20px",
      }}
    >
      {/* Resources Section */}
      <div style={{ flex: 2 }}>
        <h3 style={{ marginTop: 0 }}>My Resources</h3>
        <ul style={{
          listStyle: "none",
          padding: 0,
          display: "flex",
          gap: "1.5rem",
          margin: 0
        }}>
          <li>
            🪵 Wood: <strong>{me.resources?.wood || 0}</strong>
          </li>
          <li>
            🍖 Food: <strong>{me.resources?.food || 0}</strong>
          </li>
          <li>
            ⛏️ Iron: <strong>{me.resources?.iron || 0}</strong>
          </li>
        </ul>
      </div>

      {/* Vertical Divider */}
      <div style={{ width: "1px", height: "60px", background: "#eee" }}></div>

      {/* Health Section */}
      <div style={{ flex: 1, minWidth: "200px", paddingLeft: "20px" }}>
        <h3 style={{ marginTop: 0 }}>Health Status</h3>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <p style={{ margin: 0 }}>
            State:{" "}
            <strong style={{ color: me.health === "healthy" ? "#2e7d32" : "#c62828" }}>
              {me.health ? me.health.toUpperCase() : "UNKNOWN"}
            </strong>
          </p>
          <p style={{ margin: 0 }}>
            Sickness: {((me.sickness_chance || 0) * 100).toFixed(0)}%
          </p>
        </div>
      </div>
    </div>
  );
};

export default PlayerStatusCard;
