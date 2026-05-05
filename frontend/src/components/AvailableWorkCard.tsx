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

  return (
    <div className='card' style={{ margin: 0, flex: 1, overflowY: "auto" }}>
      <h3>Available Work</h3>
      <p style={{ fontSize: "0.8rem", color: "#666" }}>
        Sites you can work today
      </p>

      {!me.available_work || me.available_work.length === 0 ? (
        <p style={{ color: "#888", fontStyle: "italic" }}>
          No work available.
        </p>
      ) : (
        <ul style={{ paddingLeft: "0", listStyle: "none" }}>
          {me.available_work.map((work) => {
            const tile = map.find((t) => t.id === work.dev_id);
            if (!tile) return null;

            const isExpanded = expandedId === work.dev_id;

            return (
              <li
                key={work.dev_id}
                style={{
                  marginBottom: "8px",
                  background: "#f9f9f9",
                  border: isExpanded ? "2px solid #2196F3" : "1px solid #eee",
                  borderRadius: "6px",
                  overflow: "hidden"
                }}
              >
                {/* Accordion Header */}
                <div
                  style={{ padding: "10px", cursor: "pointer", display: "flex", justifyContent: "space-between" }}
                  onClick={() => handleToggleExpand(work.dev_id)}
                >
                  <span>
                    <strong>{tile.type}</strong>{" "}
                    <span style={{ fontSize: "0.8em", color: "#666" }}>
                      ({tile.owner_id === session_id ? "You" : getPlayerName(tile.owner_id!)})
                    </span>
                  </span>
                  <span>{isExpanded ? "▲" : "▼"}</span>
                </div>

                {/* Accordion Body */}
                {isExpanded && phase === "WORK" && !me.finished_phase && (
                  <div style={{ padding: "10px", background: "#e3f2fd", borderTop: "1px solid #bbdefb" }}>
                    <div style={{ display: "flex", gap: "5px", alignItems: "center", marginBottom: "10px" }}>
                      <span style={{ fontSize: "0.85rem" }}>Request:</span>
                      <input
                        type="number"
                        min="1"
                        style={{ width: "60px", padding: "4px" }}
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
                    <div style={{ display: "flex", gap: "10px" }}>
                      <button
                        className="btn-sm success"
                        onClick={() => handleSendApplication(tile)}
                      >
                        Send Application
                      </button>
                      <button
                        className="btn-sm"
                        style={{ background: "#333", color: "white" }}
                        onClick={() => onAction("WORK_DEV", { dev_id: work.dev_id })}
                      >
                        Work Free
                      </button>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default AvailableWorkCard;
