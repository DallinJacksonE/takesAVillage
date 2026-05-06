import React, { useState } from "react";
import { GameStateDTO, MapTileDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  map: MapTileDTO[];
  onAction: (action: string, payload: any) => void;
  onSend: (payload: Record<string, any>) => void;
}

const AvailableWorkCard: React.FC<Props> = ({ state, map, onAction, onSend }) => {
  const { me, phase, session_id } = state;
  const getPlayerName = usePlayerName();

  // Accordion State
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [wageOffer, setWageOffer] = useState(1);
  const [wageType, setWageType] = useState("food");

  // Broadcast State
  const [broadcastWage, setBroadcastWage] = useState(1);

  // 1. Filter the map for developments owned by OTHER players
  const publicJobBoard = map.filter((t) => t.owner_id && t.owner_id !== session_id);

  const handleToggleExpand = (devId: string) => {
    if (expandedId === devId) {
      setExpandedId(null);
    } else {
      setExpandedId(devId);
      setWageOffer(1); // Reset defaults when opening a new one
      setWageType("food");
    }
  };

  const handleSendApplication = (tile: MapTileDTO) => {
    onSend({
      to_id: tile.owner_id,
      from_id: me.id,
      type: "EMPLOYMENT",
      wage_offer: wageOffer,
      wage_type: wageType,
      dev_id: tile.id,
    });
    setExpandedId(null);
  };

  // 2. The Mass Broadcast Logic
  const handleBroadcast = (resource: string) => {
    // Map the requested resource to the development type that produces it
    const targetType = resource === "food" ? "Farm" : resource === "wood" ? "Woods" : "Mine";

    // Find all tiles owned by others that match this type
    const potentialJobs = publicJobBoard.filter(t => t.type === targetType);

    // Blast out an application to every single one
    potentialJobs.forEach(tile => {
      onSend({
        to_id: tile.owner_id,
        from_id: me.id,
        type: "EMPLOYMENT",
        wage_offer: broadcastWage,
        wage_type: resource,
        dev_id: tile.id,
      });
    });

    // Optional: Reset state after broadcast
    setBroadcastWage(1);
  };

  return (
    <div className='card' style={{ margin: 0, flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>

      {/* TOP SECTION: The Job Board */}
      <div style={{ flex: 1 }}>
        <h3 style={{ marginTop: 0 }}>The Job Board</h3>
        <p style={{ fontSize: "0.8rem", color: "#666" }}>Apply directly to a villager's development.</p>

        {publicJobBoard.length === 0 ? (
          <p style={{ color: "#888", fontStyle: "italic", fontSize: "0.85rem" }}>
            No public developments are available yet.
          </p>
        ) : (
          <ul style={{ paddingLeft: "0", listStyle: "none", margin: 0 }}>
            {publicJobBoard.map((tile) => {
              const isExpanded = expandedId === tile.id;

              return (
                <li
                  key={tile.id}
                  style={{
                    marginBottom: "8px",
                    background: "#f9f9f9",
                    border: isExpanded ? "2px solid #2196F3" : "1px solid #eee",
                    borderRadius: "6px",
                    overflow: "hidden"
                  }}
                >
                  <div
                    style={{ padding: "10px", cursor: "pointer", display: "flex", justifyContent: "space-between" }}
                    onClick={() => handleToggleExpand(tile.id)}
                  >
                    <span>
                      <strong>{tile.type}</strong>{" "}
                      <span style={{ fontSize: "0.8em", color: "#666" }}>
                        ({getPlayerName(tile.owner_id!)})
                      </span>
                    </span>
                    <span>{isExpanded ? "▲" : "▼"}</span>
                  </div>

                  {isExpanded && phase === "WORK" && !me.finished_phase && (
                    <div style={{ padding: "10px", background: "#e3f2fd", borderTop: "1px solid #bbdefb" }}>
                      <div style={{ display: "flex", gap: "5px", alignItems: "center", marginBottom: "10px" }}>
                        <span style={{ fontSize: "0.85rem" }}>I want:</span>
                        <input
                          type="number"
                          min="1"
                          style={{ width: "50px", padding: "4px" }}
                          value={wageOffer}
                          onChange={(e) => setWageOffer(Number(e.target.value))}
                        />
                        <select
                          style={{ padding: "4px" }}
                          value={wageType}
                          onChange={(e) => setWageType(e.target.value)}
                        >
                          <option value="food">Food</option>
                          <option value="wood">Wood</option>
                          <option value="iron">Iron</option>
                        </select>
                      </div>
                      <button
                        className="btn-sm success"
                        onClick={() => handleSendApplication(tile)}
                      >
                        Send Application
                      </button>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* BOTTOM SECTION: Mass Broadcast */}
      {phase === "WORK" && !me.finished_phase && publicJobBoard.length > 0 && (
        <div style={{ marginTop: "15px", paddingTop: "15px", borderTop: "2px dashed #ccc" }}>
          <h4 style={{ marginTop: 0, marginBottom: "5px", fontSize: "0.9rem" }}>Broadcast Application</h4>
          <p style={{ fontSize: "0.75rem", color: "#666", marginBottom: "10px" }}>
            Send an application to EVERYONE who produces the resource you need.
          </p>

          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: "bold" }}>Wage:</span>
            <input
              type="number"
              min="1"
              style={{ width: "60px", padding: "4px" }}
              value={broadcastWage}
              onChange={(e) => setBroadcastWage(Number(e.target.value))}
            />
          </div>

          <div style={{ display: "flex", gap: "5px" }}>
            <button className="btn-sm" style={{ flex: 1, background: "#ffb74d", color: "#333" }} onClick={() => handleBroadcast("food")}>
              For Food
            </button>
            <button className="btn-sm" style={{ flex: 1, background: "#8d6e63", color: "white" }} onClick={() => handleBroadcast("wood")}>
              For Wood
            </button>
            <button className="btn-sm" style={{ flex: 1, background: "#90a4ae", color: "#333" }} onClick={() => handleBroadcast("iron")}>
              For Iron
            </button>
          </div>
        </div>
      )}

    </div>
  );
};

export default AvailableWorkCard;
