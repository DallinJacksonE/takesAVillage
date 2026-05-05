import React from "react";
import { GameStateDTO, MapTileDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  map: MapTileDTO[];
  onAction: (action: string, payload: any) => void;
}

const AvailableWorkCard: React.FC<Props> = ({ state, map, onAction }) => {
  const { me, phase, session_id } = state;
  const getPlayerName = usePlayerName();

  return (
    <div className='card' style={{ margin: 0, flex: 1 }}>
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
          {me.available_work.map((work) => {
            const tile = map.find((t) => t.id === work.dev_id);

            if (!tile) return null;

            return (
              <li
                key={work.dev_id}
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
                    onClick={() => onAction("WORK_DEV", { dev_id: work.dev_id })}
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
  );
};

export default AvailableWorkCard;
