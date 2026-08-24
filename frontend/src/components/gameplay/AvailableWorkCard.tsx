import React from "react";
import { EmploymentActionDTO, WorkActionDTO, CommitWorkPayload } from "../../dtos/index";
import { usePlayerName } from "../hooks/usePlayerName";
import { useGameState } from "../hooks/useGameState";

import styles from "./AvailableWorkCard.module.css";
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
    <div className={`card ${styles.column}`} >
      <h3 className={styles.header2}>Work Phase Dashboard</h3>      {/* --- Section 1: Ready to Commit (Inherent + Accepted Contracts) --- */}
      <div className={styles.panel10}>
        <h3 className={styles.header}>Available Work</h3>

        {(!me.available_work || me.available_work.length === 0) ? (
          <div className={styles.panel9}>
            No work available right now. Check back tomorrow or negotiate a contract!
          </div>
        ) : (
          me.available_work.map((work: WorkActionDTO, index: number) => {
            const itemKey = work.action_id || `inherent-work-${index}`;
            const developmentLabel = `${work.development?.type || "Property"} ${work.development?.id || ""}`.trim();
            const wageLabel = `${work.wage} ${work.wage_type}`;

            return (
              <div
                key={itemKey}
                className={styles.row5}
              >
                <span className={styles.workDetails}>
                  <strong>{developmentLabel}</strong>
                  <span>Agreed wage: {wageLabel}</span>
                </span>

                <button
                  aria-label={`Commit work at ${developmentLabel} for agreed wage ${wageLabel}`}
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
        <div className={styles.panel8}>
          <strong className={styles.label5}>Hired Workers</strong>
          {myEmployees.map((contract) => {
            // Find the worker's ID based on whether it was an application or an offer
            const workerId = contract.is_application ? contract.initiator_id : contract.target_id;
            return (
              <div key={contract.id} className={styles.panel7}>
                <span>{getPlayerName(workerId || "")} hired for {contract.wage} {contract.wage_type}.</span>
              </div>
            );
          })}
        </div>
      )}

      {/* --- Section 3: Job Offers Received --- */}
      {pendingOffers.length > 0 && (
        <div className={styles.panel6}>
          <strong className={styles.label4}>Job Offers Received</strong>
          {pendingOffers.map((offer) => (
            <div key={offer.id} className={styles.row4}>
              <span>{getPlayerName(offer.initiator_id)} offering {offer.wage} {offer.wage_type}.</span>
              <div className={styles.row3}>
                <button className="btn-tooltip info" onClick={() => onAcceptOffer(offer.id)}>Accept</button>
                <button className="btn-tooltip danger" onClick={() => onDenyOffer(offer.id)}>Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- Section 4: Applications Received --- */}
      {receivedApplications.length > 0 && (
        <div className={styles.panel5}>
          <strong className={styles.label3}>Applications Received</strong>
          {receivedApplications.map((app) => (
            <div key={app.id} className={styles.row2}>
              <span>{getPlayerName(app.initiator_id)} applying for {app.wage} {app.wage_type}.</span>
              <div className={styles.row}>
                <button className="btn-tooltip info" onClick={() => onAcceptOffer(app.id)}>Hire</button>
                <button className="btn-tooltip danger" onClick={() => onDenyOffer(app.id)}>Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* --- Section 5: Sent Offers --- */}
      {sentOffers.length > 0 && (
        <div className={styles.panel4}>
          <strong className={styles.label2}>Offers Sent</strong>
          {sentOffers.map((offer) => (
            <div key={offer.id} className={styles.panel3}>
              Offered to {getPlayerName(offer.target_id || "")}
            </div>
          ))}
        </div>
      )}

      {/* --- Section 6: Pending Applications --- */}
      {pendingApplications.length > 0 && (
        <div className={styles.panel2}>
          <strong className={styles.label}>Awaiting Reply</strong>
          {pendingApplications.map((app) => (
            <div key={app.id} className={styles.panel}>
              Applied to {getPlayerName(app.target_id || "")}
            </div>
          ))}
        </div>
      )}

    </div>
  );
};

export default AvailableWorkCard;
