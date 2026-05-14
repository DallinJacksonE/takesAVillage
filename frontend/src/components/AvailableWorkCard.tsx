import React from "react";
import { GameStateDTO, EmploymentActionDTO, CommitWorkPayload } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onCommitWork: (payload: CommitWorkPayload) => void;
  onAcceptOffer: (actionId: string) => void;
  onDenyOffer: (actionId: string) => void;
}

const AvailableWorkCard: React.FC<Props> = ({
  state,
  onCommitWork,
  onAcceptOffer,
  onDenyOffer
}) => {
  const { me } = state;
  const getPlayerName = usePlayerName();

  const employmentActions = (me.actions || []).filter(
    (a): a is EmploymentActionDTO => a.type === "EMPLOYMENT"
  );

  const contestActions = (me.actions || []).filter(
    (a) => a.type === "CONTEST" || a.type === "JOIN_CONTEST"
  );

  const pendingOffers = employmentActions.filter(
    (a) => a.target_id === me.id && !a.is_application && a.status === "PENDING"
  );

  const pendingApplications = employmentActions.filter(
    (a) => a.initiator_id === me.id && a.is_application && a.status === "PENDING"
  );

  const sentOffers = employmentActions.filter(
    (a) => a.initiator_id === me.id && !a.is_application && a.status === "PENDING"
  );
  const sentOfferDevIds = sentOffers.map(a => a.dev_id);

  const displayableInherentWork = me.available_work.filter(
    (work) => !sentOfferDevIds.includes(work.development.id)
  );
  console.log(displayableInherentWork)
  // FIX 2: Only show the "Contracted Job" UI if the backend hasn't already provided it
  const acceptedContracts = employmentActions.filter(
    (a) =>
      a.status === "ACCEPTED" &&
      (a.is_application ? me.id === a.initiator_id : me.id === a.target_id) &&
      !me.available_work.some((aw) => aw.development.id === a.dev_id)
  );

  return (
    <div className="card" style={{ minHeight: "297px", flex: 1, display: "flex", flexDirection: "column" }}>
      <h3 style={{ marginTop: 0 }}>Work Phase Dashboard</h3>

      {/* --- Section 1: Ready to Commit (Inherent + Accepted) --- */}
      <div style={{ marginBottom: "15px" }}>
        <strong style={{ color: "#388e3c" }}>Available Jobs</strong>
        {displayableInherentWork.length === 0 && acceptedContracts.length === 0 ? (
          <p style={{ fontSize: "0.85rem", color: "#888", fontStyle: "italic" }}>No jobs available.</p>
        ) : (
          <>
            {/* 1. Render Inherent / Backend Generated Work */}
            {displayableInherentWork.map((work, idx) => (
              <div key={`inherent-${idx}`} style={{ background: "#e8f5e9", padding: "8px", borderRadius: "4px", marginTop: "5px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ fontSize: "0.85rem" }}>
                  <strong>{work.development.type}</strong>
                  <div style={{ color: "#555" }}>
                    Wage: {work.wage} {work.wage_type} {work.employer_id !== me.id && `(from ${getPlayerName(work.employer_id)})`}
                  </div>
                </div>
                <button
                  className="btn-tooltip success"
                  disabled={me.finished_phase}
                  onClick={() => onCommitWork({ work_action: work })}
                >
                  Lock In
                </button>
              </div>
            ))}

            {/* 2. Render Dynamically Accepted Contracts */}
            {acceptedContracts.map((work) => {
              const employerId = work.is_application ? work.target_id : work.initiator_id;
              return (
                <div key={work.id} style={{ background: "#e8f5e9", padding: "8px", borderRadius: "4px", marginTop: "5px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontSize: "0.85rem" }}>
                    <strong>Contracted Job</strong>
                    <div style={{ color: "#555" }}>
                      Wage: {work.wage} {work.wage_type} {employerId && employerId !== me.id && `(from ${getPlayerName(employerId)})`}
                    </div>
                  </div>
                  <button
                    className="btn-tooltip success"
                    disabled={me.finished_phase}
                    onClick={() => onCommitWork({ action_id: work.id })}
                  >
                    Lock In
                  </button>
                </div>
              );
            })}
          </>
        )}
      </div>

      {/* --- Section 2: Active Contests (Lock-In) --- */}
      {contestActions.length > 0 && (
        <div style={{ marginBottom: "15px", borderTop: "1px solid #eee", paddingTop: "10px" }}>
          <strong style={{ color: "#c62828" }}>Active Conflicts</strong>
          {contestActions.map((contest) => (
            <div key={contest.id} style={{ background: "#ffebee", padding: "8px", borderRadius: "4px", marginTop: "5px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: "0.85rem", color: "#c62828" }}>
                <strong>Contesting Property</strong>
              </div>
              <button
                className="btn-tooltip danger"
                style={{ padding: "4px 10px", fontSize: "0.85rem" }}
                disabled={me.finished_phase}
                onClick={() => onCommitWork({ action_id: contest.id })}
              >
                Commit to Fight
              </button>
            </div>
          ))}
        </div>
      )}

      {/* --- Section 3: Incoming Job Offers --- */}
      {pendingOffers.length > 0 && (
        <div style={{ marginBottom: "15px", borderTop: "1px solid #eee", paddingTop: "10px" }}>
          <strong style={{ color: "#1976d2" }}>Job Offers</strong>
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

      {/* --- Section 4: Pending Applications --- */}
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
