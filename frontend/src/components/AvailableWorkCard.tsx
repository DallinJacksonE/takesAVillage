import React from "react";
import { GameStateDTO, EmploymentActionDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onSend: (payload: Record<string, any>) => void;
}

const AvailableWorkCard: React.FC<Props> = ({ state, onSend }) => {
  const { me } = state;
  const getPlayerName = usePlayerName();

  // Filter actions for employment interactions
  const employmentActions = (me.actions || []).filter(
    (a): a is EmploymentActionDTO => a.type === "EMPLOYMENT"
  );

  // Offers sent TO me by an owner
  const pendingOffers = employmentActions.filter(
    (a) => a.target_id === me.id && !a.is_application && a.status === "PENDING"
  );

  // Applications I sent out waiting for an owner's reply
  const pendingApplications = employmentActions.filter(
    (a) => a.initiator_id === me.id && a.is_application && a.status === "PENDING"
  );

  return (
    <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      <h3>Work Phase</h3>

      {/* --- Section 1: Ready to Commit (Inherent + Accepted) --- */}
      <div style={{ marginBottom: "15px" }}>
        <strong style={{ color: "#388e3c" }}>Available Jobs</strong>
        {me.available_work.length === 0 ? (
          <p style={{ fontSize: "0.85rem", color: "#888", fontStyle: "italic" }}>No jobs available.</p>
        ) : (
          me.available_work.map((work, idx) => (
            <div key={idx} style={{ background: "#e8f5e9", padding: "8px", borderRadius: "4px", marginTop: "5px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: "0.85rem" }}>
                <strong>{work.development.type}</strong>
                <div style={{ color: "#555" }}>
                  Wage: {work.wage} {work.wage_type} {work.employer_id !== me.id && `(from ${getPlayerName(work.employer_id)})`}
                </div>
              </div>
              <button
                style={{ background: "grey", color: "white" }}
                className="btn-secondary"
                disabled={me.finished_phase}
                onClick={() => onSend({ actionCommand: "COMMIT_WORK", work_action: work })}
              >
                Lock In
              </button>
            </div>
          ))
        )}
      </div>

      {/* --- Section 2: Incoming Job Offers --- */}
      {pendingOffers.length > 0 && (
        <div style={{ marginBottom: "15px", borderTop: "1px solid #eee", paddingTop: "10px" }}>
          <strong style={{ color: "#1976d2" }}>Job Offers</strong>
          {pendingOffers.map((offer) => (
            <div key={offer.id} style={{ background: "#e3f2fd", padding: "8px", borderRadius: "4px", marginTop: "5px", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem" }}>
              <span>{getPlayerName(offer.initiator_id)} is offering {offer.wage} {offer.wage_type}.</span>
              <div style={{ display: "flex", gap: "5px" }}>
                <button className="btn-secondary" style={{ background: "#2196F3", color: "white" }} onClick={() => onSend({ actionCommand: "ACCEPT", actionId: offer.id })}>Accept</button>
                <button className="btn-secondary danger" onClick={() => onSend({ actionCommand: "DENY", actionId: offer.id })}>Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- Section 3: Pending Applications --- */}
      {pendingApplications.length > 0 && (
        <div style={{ borderTop: "1px solid #eee", paddingTop: "10px" }}>
          <strong style={{ color: "#f57c00" }}>Awaiting Reply</strong>
          {pendingApplications.map((app) => (
            <div key={app.id} style={{ background: "#fff3e0", padding: "8px", borderRadius: "4px", marginTop: "5px", fontSize: "0.85rem", color: "#666" }}>
              Applied to {getPlayerName(app.target_id || "")} for {app.wage} {app.wage_type}.
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AvailableWorkCard;
