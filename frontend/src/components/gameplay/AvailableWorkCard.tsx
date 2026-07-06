import React from "react";
import { EmploymentActionDTO, WorkActionDTO, CommitWorkPayload } from "../../dtos/index";
import { usePlayerName } from "../hooks/usePlayerName";
import { useGameState } from "../hooks/useGameState";

interface Props {
  onCommitWork: (payload: CommitWorkPayload) => void;
  onAcceptOffer: (actionId: string) => void;
  onDenyOffer: (actionId: string) => void;
}

const AvailableWorkCard: React.FC<Props> = ({
  onCommitWork,
  onAcceptOffer,
  onDenyOffer,
}) => {
  const gameState = useGameState();
  const { me } = gameState;
  const getPlayerName = usePlayerName();

  // Filter for ALL employment actions
  const employmentActions = (me.actions || []).filter(
    (a): a is EmploymentActionDTO => a.type === "EMPLOYMENT"
  );

  // 1. Pending Offers (Employer sent an offer to me)
  const pendingOffers = employmentActions.filter(
    (a) => a.target_id === me.id && !a.is_application && a.status === "PENDING"
  );

  // 2. Pending Applications (I applied to an employer)
  const pendingApplications = employmentActions.filter(
    (a) => a.initiator_id === me.id && a.is_application && a.status === "PENDING"
  );

  // 3. Sent Offers (I sent an offer to a worker)
  const sentOffers = employmentActions.filter(
    (a) => a.initiator_id === me.id && !a.is_application && a.status === "PENDING"
  );

  // 4. Received Applications (A worker applied to me)
  const receivedApplications = employmentActions.filter(
    (a) => a.target_id === me.id && a.is_application && a.status === "PENDING"
  );

  // NEW: Hired Workers (Employer View)
  // Shows accepted contracts where 'me' is the employer
  const myEmployees = employmentActions.filter(
    (a) => a.status === "ACCEPTED" &&
      ((a.is_application && a.target_id === me.id) || (!a.is_application && a.initiator_id === me.id))
  );

  const disabled = me.finished_phase || me.health !== "healthy";

  return (
    <div className="card" style={{ minHeight: "297px", flex: 1, display: "flex", flexDirection: "column" }}>
      <h3 style={{ marginTop: 0 }}>Work Phase Dashboard</h3>      {/* --- Section 1: Ready to Commit (Inherent + Accepted Contracts) --- */}
      <div style={{ marginBottom: "15px" }}>
        <h3 style={{ marginTop: "0", color: "#2e7d32" }}>Available Work</h3>

        {(!me.available_work || me.available_work.length === 0) ? (
          <div style={{ fontSize: "0.85rem", color: "#666", marginTop: "5px", padding: "8px", background: "#f1f8e9", borderRadius: "4px" }}>
            No work available right now. Check back tomorrow or negotiate a contract!
          </div>
        ) : (
          me.available_work.map((work: WorkActionDTO, index: number) => {
            const itemKey = work.action_id || `inherent-work-${index}`;

            return (
              <div
                key={itemKey}
                style={{ background: "#e8f5e9", padding: "8px", borderRadius: "4px", marginTop: "5px", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem" }}
              >
                <span>
                  <strong>{work.development?.type || 'Property'}</strong> - Wage: {work.wage} {work.wage_type}
                </span>

                <button
                  className="btn-tooltip success"
                  onClick={() => onCommitWork({ job: work })}
                  disabled={disabled}
                >
                  Commit
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* --- Section 2: Hired Workers (Visual Confirmation for Employer) --- */}
      {myEmployees.length > 0 && (
        <div style={{ marginBottom: "15px", borderTop: "1px solid #eee", paddingTop: "10px" }}>
          <strong style={{ color: "#4caf50" }}>Hired Workers</strong>
          {myEmployees.map((contract) => {
            // Find the worker's ID based on whether it was an application or an offer
            const workerId = contract.is_application ? contract.initiator_id : contract.target_id;
            return (
              <div key={contract.id} style={{ background: "#e8f5e9", padding: "8px", borderRadius: "4px", marginTop: "5px", fontSize: "0.85rem", color: "#333" }}>
                <span>{getPlayerName(workerId || "")} hired for {contract.wage} {contract.wage_type}.</span>
              </div>
            );
          })}
        </div>
      )}

      {/* --- Section 3: Job Offers Received --- */}
      {pendingOffers.length > 0 && (
        <div style={{ marginBottom: "15px", borderTop: "1px solid #eee", paddingTop: "10px" }}>
          <strong style={{ color: "#1976d2" }}>Job Offers Received</strong>
          {pendingOffers.map((offer) => (
            <div key={offer.id} style={{ background: "#e3f2fd", padding: "8px", borderRadius: "4px", marginTop: "5px", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem" }}>
              <span>{getPlayerName(offer.initiator_id)} offering {offer.wage} {offer.wage_type}.</span>
              <div style={{ display: "flex", gap: "5px" }}>
                <button className="btn-tooltip info" onClick={() => onAcceptOffer(offer.id)}>Accept</button>
                <button className="btn-tooltip danger" onClick={() => onDenyOffer(offer.id)}>Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- Section 4: Applications Received --- */}
      {receivedApplications.length > 0 && (
        <div style={{ marginBottom: "15px", borderTop: "1px solid #eee", paddingTop: "10px" }}>
          <strong style={{ color: "#9c27b0" }}>Applications Received</strong>
          {receivedApplications.map((app) => (
            <div key={app.id} style={{ background: "#f3e5f5", padding: "8px", borderRadius: "4px", marginTop: "5px", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem" }}>
              <span>{getPlayerName(app.initiator_id)} applying for {app.wage} {app.wage_type}.</span>
              <div style={{ display: "flex", gap: "5px" }}>
                <button className="btn-tooltip info" onClick={() => onAcceptOffer(app.id)}>Hire</button>
                <button className="btn-tooltip danger" onClick={() => onDenyOffer(app.id)}>Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- Section 5: Sent Offers --- */}
      {sentOffers.length > 0 && (
        <div style={{ borderTop: "1px solid #eee", paddingTop: "10px", marginBottom: "15px" }}>
          <strong style={{ color: "#607d8b" }}>Offers Sent</strong>
          {sentOffers.map((offer) => (
            <div key={offer.id} style={{ background: "#eceff1", padding: "8px", borderRadius: "4px", marginTop: "5px", fontSize: "0.85rem", color: "#666" }}>
              Offered to {getPlayerName(offer.target_id || "")}
            </div>
          ))}
        </div>
      )}

      {/* --- Section 6: Pending Applications --- */}
      {pendingApplications.length > 0 && (
        <div style={{ borderTop: "1px solid #eee", paddingTop: "10px" }}>
          <strong style={{ color: "#f57c00" }}>Awaiting Reply</strong>
          {pendingApplications.map((app) => (
            <div key={app.id} style={{ background: "#fff3e0", padding: "8px", borderRadius: "4px", marginTop: "5px", fontSize: "0.85rem", color: "#666" }}>
              Applied to {getPlayerName(app.target_id || "")}
            </div>
          ))}
        </div>
      )}

    </div>
  );
};

export default AvailableWorkCard;
