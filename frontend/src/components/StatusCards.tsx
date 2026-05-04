import React from "react";
import { GameStateDTO, MapTileDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  map: MapTileDTO[];
  onAction: (action: string, payload: any) => void;
}

const StatusCards: React.FC<Props> = ({ state, map, onAction }) => {
  const { me, phase, session_id } = state;
  const getPlayerName = usePlayerName();

  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", height: "100%", width: "100%" }}>
        {/* Top Row Wrapper: Forces cards side-by-side */}
        <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", width: "100%" }}>

          {/* Left Col: Developments */}
          <div className='card' style={{ flex: 1, margin: 0 }}>
            <h3>Developments</h3>
            {!me.developments || me.developments.length === 0 ? (
              <p style={{ color: "#888", fontStyle: "italic" }}>
                No developments yet.
              </p>
            ) : (
              me.developments.map((dev, idx) => (
                <div
                  key={idx}
                  style={{
                    background: "#f9f9f9",
                    padding: "10px",
                    marginBottom: "10px",
                    borderRadius: "4px",
                    border: "1px solid #eee",
                  }}
                >
                  <strong>
                    {dev.type} (Lvl {dev.level})
                  </strong>
                  <div style={{ fontSize: "0.85rem", color: "#555", marginTop: "5px" }}>
                    Maint: {dev.maintenence_days} days remaining
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Right Col: Available Work */}
          <div className='card' style={{ flex: 1, margin: 0 }}>
            <h3>Available Work</h3>
            <p style={{ fontSize: "0.8rem", color: "#666" }}>
              Sites you can work today
            </p>

            {!me.available_work || me.available_work.length === 0 ? (
              <p style={{ color: "#888", fontStyle: "italic" }}>
                No work available.
              </p>
            ) : (
              <ul style={{ paddingLeft: "20px" }}>
                {me.available_work.map((devId) => {
                  const tile = map.find((t) => t.id === devId);

                  if (!tile) return null;

                  return (
                    <li
                      key={devId}
                      style={{
                        marginBottom: "5px",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <span>
                        <strong>{tile.type}</strong>{" "}
                        <span style={{ fontSize: "0.8em", color: "#666" }}>
                          (
                          {tile.owner_id === session_id
                            ? me.name
                            : getPlayerName(tile.owner_id!)}
                          )
                        </span>
                      </span>

                      {phase === "WORK" && !me.finished_phase && (
                        <button
                          className='btn-sm success'
                          style={{
                            marginLeft: "10px",
                            padding: "2px 8px",
                            fontSize: "0.7rem",
                          }}
                          onClick={() => onAction("WORK_DEV", { dev_id: devId })}
                        >
                          Work
                        </button>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>

        {/* Bottom Bar: Resources & Health */}
        <div
          className='bar'
          style={{
            marginTop: "auto",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap", /* Ensures it wraps nicely on smaller screens */
            gap: "1rem"
          }}
        >
          {/* Resources Section */}
          <div style={{ flex: 2 }}>
            <h3 style={{ marginTop: 0 }}>My Resources</h3>
            <ul style={{
              listStyle: "none",
              padding: 0,
              display: "flex",
              gap: "1.5rem", /* Spaces out the resources horizontally */
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

          {/* Vertical Divider (Hidden on small screens if it wraps) */}
          <div style={{ width: "1px", height: "60px", background: "#eee" }}></div>

          {/* Health Section */}
          <div style={{ flex: 1, minWidth: "200px" }}>
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
      </div >
    </>
  );
};

export default StatusCards;
