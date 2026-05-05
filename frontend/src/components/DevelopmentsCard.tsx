import React from "react";
import { GameStateDTO } from "../../../dtos/index";

interface Props {
  state: GameStateDTO;
}

const DevelopmentsCard: React.FC<Props> = ({ state }) => {
  const { me } = state;

  return (
    <div className='card' style={{ margin: 0, flex: 1 }}>
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
  );
};

export default DevelopmentsCard;
