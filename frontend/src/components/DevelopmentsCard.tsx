import React from "react";
import { GameStateDTO, EmploymentActionDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onSend: (payload: Record<string, any>) => void;
}

const DevelopmentsCard: React.FC<Props> = ({ state, onSend }) => {
  const { me } = state;
  const getPlayerName = usePlayerName();

  // Filter actions to find employment applications sent TO me
  const employmentActions = (me.actions || []).filter(
    (a): a is EmploymentActionDTO => a.type === "EMPLOYMENT"
  );

  return (
    <div className="card" style={{ flex: 1 }}>
      <h3>My Properties</h3>
      {me.developments.length === 0 ? (
        <p style={{ color: "#888", fontStyle: "italic" }}>You own no land.</p>
      ) : (
        me.developments.map((dev) => {
          // Find pending applications specific to this development
          const pendingApplications = employmentActions.filter(
            (a) => a.dev_id === dev.id && a.is_application && a.status === "PENDING"
          );

          return (
            <div
              key={dev.id}
              style={{
                border: "1px solid #ccc",
                borderRadius: "6px",
                padding: "10px",
                marginBottom: "10px",
                background: "#fafafa",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong style={{ fontSize: "1.1rem" }}>{dev.type} (Lvl {dev.level})</strong>
                <span
                  style={{
                    fontSize: "0.8rem",
                    color: dev.maintenence_days < 2 ? "red" : "#666",
                    fontWeight: "bold",
                  }}
                >
                  Degrades in {dev.maintenence_days} days
                </span>
              </div>

              {/* System Actions: Maintenance & Upgrade */}
              <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                <button
                  className="btn-sm"
                  style={{ background: "#795548", color: "white" }}
                  onClick={() =>
                    onSend({
                      actionCommand: "MAINTENANCE",
                      type: "MAINTENANCE",
                      dev_id: dev.id,
                      cost: 1,
                      cost_type: "wood",
                    })
                  }
                >
                  Maintain (1 Wood)
                </button>
                <button
                  className="btn-sm"
                  style={{ background: "#f57c00", color: "white" }}
                  onClick={() =>
                    onSend({
                      actionCommand: "UPGRADE",
                      type: "UPGRADE",
                      dev_id: dev.id,
                    })
                  }
                >
                  Upgrade (Cost varies)
                </button>
              </div>

              {/* Owner's Inbox: Applications from other players */}
              {pendingApplications.length > 0 && (
                <div style={{ marginTop: "10px", borderTop: "1px dashed #ccc", paddingTop: "10px" }}>
                  <strong style={{ fontSize: "0.85rem", color: "#2196F3" }}>Job Applications:</strong>
                  {pendingApplications.map((app) => (
                    <div key={app.id} style={{ display: "flex", justifyContent: "space-between", marginTop: "5px", fontSize: "0.85rem" }}>
                      <span>{getPlayerName(app.initiator_id)} wants to work for {app.wage} {app.wage_type}.</span>
                      <div style={{ display: "flex", gap: "5px" }}>
                        <button className="btn-sm success" onClick={() => onSend({ actionCommand: "ACCEPT", actionId: app.id })}>Hire</button>
                        <button className="btn-sm danger" onClick={() => onSend({ actionCommand: "DENY", actionId: app.id })}>Reject</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
};

export default DevelopmentsCard;
