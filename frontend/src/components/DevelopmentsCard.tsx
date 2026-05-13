import React, { useState } from "react";
import { GameStateDTO, EmploymentActionDTO, Resource } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onMaintain: (devId: string) => void;
  onUpgrade: (devId: string) => void;
  onContest: (devId: string, targetId?: string) => void;
  onApplyForJob: (targetId: string, devId: string, wage: number, wageType: Resource) => void;
  onAcceptApplicant: (actionId: string) => void;
  onDenyApplicant: (actionId: string) => void;
}

const DevelopmentsCard: React.FC<Props> = ({
  state,
  onMaintain,
  onUpgrade,
  onContest,
  onApplyForJob,
  onAcceptApplicant,
  onDenyApplicant
}) => {
  const { me, player_list } = state;
  const getPlayerName = usePlayerName();

  // Accordion State
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Draft Job Application State
  const [appWage, setAppWage] = useState<number>(1);
  const [appWageType, setAppWageType] = useState<Resource>("food");

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const employmentActions = (me.actions || []).filter(
    (a): a is EmploymentActionDTO => a.type === "EMPLOYMENT"
  );

  // Aggregate foreign developments
  const villageDevelopments = player_list
    .filter((p) => p.id !== me.id)
    .flatMap((p) =>
      p.developments.map((dev) => ({ ...dev, owner_id: p.id }))
    );

  return (
    <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column", gap: "20px" }}>

      {/* --- SECTION 1: MY DEVELOPMENTS --- */}
      <div>
        <h3 style={{ marginTop: 0 }}>My Properties</h3>
        {me.developments.length === 0 ? (
          <p style={{ color: "#888", fontStyle: "italic", fontSize: "0.85rem" }}>You own no land.</p>
        ) : (
          me.developments.map((dev) => {
            const pendingApplications = employmentActions.filter(
              (a) => a.dev_id === dev.id && a.is_application && a.status === "PENDING"
            );

            // Determine border color based on urgency flags
            let borderColor = "#ccc";
            if (dev.is_contested) borderColor = "#c62828"; // Red for contested
            else if (pendingApplications.length > 0) borderColor = "#2e7d32"; // Green for applicants

            const isExpanded = expandedId === dev.id;
            return (
              <div
                key={dev.id}
                style={{
                  border: `2px solid ${borderColor}`,
                  borderRadius: "6px",
                  marginBottom: "10px",
                  background: "#fafafa",
                  overflow: "hidden"
                }}
              >
                {/* Accordion Header */}
                <div
                  style={{ padding: "10px", display: "flex", justifyContent: "space-between", cursor: "pointer", background: isExpanded ? "#eee" : "transparent" }}
                  onClick={() => toggleExpand(dev.id)}
                >
                  <strong style={{ fontSize: "1rem" }}>{dev.type} (Lvl {dev.level})</strong>
                  <span style={{ fontSize: "0.8rem", color: dev.maintenance_days < 2 ? "red" : "#666", fontWeight: "bold" }}>
                    {dev.is_contested ? "🔥 CONTESTED" : `Degrades in ${dev.maintenance_days}d`}
                  </span>
                </div>

                {/* Accordion Body */}
                {isExpanded && (
                  <div style={{ padding: "10px", borderTop: "1px solid #ddd" }}>

                    {/* Contextual Action Buttons */}
                    <div style={{ display: "flex", gap: "10px" }}>
                      {dev.is_contested ? (
                        <button
                          className="btn danger"
                          style={{ width: "100%" }}
                          onClick={() => onContest(dev.id)}
                        >
                          Defend Property
                        </button>
                      ) : (
                        <>
                          <button
                            className="btn-secondary"
                            style={{ background: "#795548", color: "white", flex: 1 }}
                            disabled={true}
                            onClick={() => onMaintain(dev.id)}
                          >
                            maintenance: {
                              state.development_costs[dev.type]?.maintain
                                ? Object.entries(state.development_costs[dev.type].maintain)
                                  .map(([resource, amount]) => `${amount} ${resource}`)
                                  .join(", ")
                                : "Unknown Cost"
                            }
                          </button>
                          <button
                            className="btn-secondary"
                            style={{ background: "#f57c00", color: "white", flex: 1 }}
                            onClick={() => onUpgrade(dev.id)}
                          >
                            Upgrade: {
                              state.development_costs[dev.type]?.upgrade
                                ? Object.entries(state.development_costs[dev.type].upgrade)
                                  .map(([resource, amount]) => `${amount} ${resource}`)
                                  .join(", ")
                                : "Unknown Cost"
                            }
                          </button>
                        </>
                      )}
                    </div>

                    {/* Pending Applications */}
                    {pendingApplications.length > 0 && (
                      <div style={{ marginTop: "15px", borderTop: "1px dashed #ccc", paddingTop: "10px" }}>
                        <strong style={{ fontSize: "0.85rem", color: "#2e7d32" }}>Job Applications:</strong>
                        {pendingApplications.map((app) => (
                          <div key={app.id} style={{ display: "flex", justifyContent: "space-between", marginTop: "5px", fontSize: "0.85rem", alignItems: "center" }}>
                            <span>{getPlayerName(app.initiator_id)} asking {app.wage} {app.wage_type}</span>
                            <div style={{ display: "flex", gap: "5px" }}>
                              <button className="btn-sm success" onClick={() => onAcceptApplicant(app.id)}>Hire</button>
                              <button className="btn-sm danger" onClick={() => onDenyApplicant(app.id)}>Reject</button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* --- SECTION 2: VILLAGE DEVELOPMENTS --- */}
      <div>
        <h3 style={{ marginTop: 0 }}>Village Properties</h3>
        {villageDevelopments.length === 0 ? (
          <p style={{ color: "#888", fontStyle: "italic", fontSize: "0.85rem" }}>No other properties exist.</p>
        ) : (
          villageDevelopments.map((dev) => {
            const isExpanded = expandedId === dev.id;

            return (
              <div key={dev.id} style={{ border: "1px solid #ccc", borderRadius: "6px", marginBottom: "8px", background: "#fff" }}>

                {/* Accordion Header */}
                <div
                  style={{ padding: "8px 10px", display: "flex", justifyContent: "space-between", cursor: "pointer", background: isExpanded ? "#eee" : "transparent" }}
                  onClick={() => toggleExpand(dev.id)}
                >
                  <strong style={{ fontSize: "0.9rem" }}>{dev.type} (Lvl {dev.level})</strong>
                  <span style={{ fontSize: "0.8rem", color: "#666" }}>Owner: {getPlayerName(dev.owner_id)}</span>
                </div>

                {/* Accordion Body */}
                {isExpanded && (
                  <div style={{ padding: "10px", borderTop: "1px solid #ddd", display: "flex", flexDirection: "column", gap: "10px" }}>

                    {/* Apply for Job Form */}
                    <div style={{ display: "flex", gap: "5px", alignItems: "center", fontSize: "0.85rem" }}>
                      <span>Ask for:</span>
                      <input type="number" min="1" value={appWage} onChange={e => setAppWage(parseInt(e.target.value) || 1)} style={{ width: "40px", padding: "2px" }} />
                      <select value={appWageType} onChange={e => setAppWageType(e.target.value as Resource)} style={{ padding: "2px" }}>
                        <option value="food">Food</option>
                        <option value="wood">Wood</option>
                        <option value="iron">Iron</option>
                      </select>
                      <button
                        className="btn-sm success"
                        style={{ marginLeft: "auto" }}
                        onClick={() => onApplyForJob(dev.owner_id, dev.id, appWage, appWageType)}
                      >
                        Apply
                      </button>
                    </div>

                    {/* Contest Action */}
                    <button
                      className="btn-sm danger"
                      style={{ width: "100%", padding: "6px" }}
                      disabled={true}
                      onClick={() => onContest(dev.id, dev.owner_id)}
                    >
                      Contest Ownership
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default DevelopmentsCard;
