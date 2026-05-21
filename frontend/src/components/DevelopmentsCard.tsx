import React, { useState } from "react";
import { EmploymentActionDTO, Resource, DevelopmentDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";
import { usePlayerColors } from "./hooks/usePlayerColor";
import { useGameState } from "./hooks/useGameState";
import InfoTooltip from "./InfoTooltip";

interface Props {
  onMaintain: (devId: string) => void;
  onUpgrade: (devId: string) => void;
  onContest: (devId: string, side: "INITIATOR" | "CONTESTER" | "OWNER") => void;
  onApplyForJob: (targetId: string, devId: string, wage: number, wageType: Resource) => void;
  onAcceptApplicant: (actionId: string) => void;
  onDenyApplicant: (actionId: string) => void;
}

const DevelopmentsCard: React.FC<Props> = ({
  onMaintain,
  onUpgrade,
  onContest,
  onApplyForJob,
  onAcceptApplicant,
  onDenyApplicant
}) => {
  const gameState = useGameState();
  const { me, player_list, developments } = gameState;
  const getPlayerName = usePlayerName();
  const { getPlayerColor } = usePlayerColors();

  // --- HYDRATION LOGIC ---
  const hydratedMe = {
    ...me,
    developments: gameState.developments.filter(
      (dev) => dev.owner_id === me.id
    )
  };

  // Hydrate the 'player_list' using the exact same filtering logic
  const hydratedPlayerList = player_list.map((p) => ({
    ...p,
    developments: gameState.developments.filter(
      (dev) => dev.owner_id === p.id // Note: Use p.id here if your PlayerDTO uses 'id' instead of 'session_id' on the frontend
    )
  }));  // -----------------------

  // Accordion State
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Draft Job Application State
  const [appWage, setAppWage] = useState<number>(1);
  const [appWageType, setAppWageType] = useState<Resource>("food");

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  // Note: Use hydratedMe here instead of the raw me!
  const employmentActions = (hydratedMe.actions || []).filter(
    (a): a is EmploymentActionDTO => a.type === "EMPLOYMENT"
  );

  // Aggregate foreign developments
  // Note: Use hydratedPlayerList here instead of the raw player_list!
  const villageDevelopments = hydratedPlayerList
    .filter((p) => p.id !== hydratedMe.id)
    .flatMap((p) =>
      p.developments.map((dev) => ({ ...dev, owner_id: p.id }))
    );

  const propertiesInfoText = "These are your developments, you can choose to spend your work phase at one of them or spend it upgrading or maintaining it."
  const maintenanceInfoText = "Level will decrease if maintenance is at 0, level is amount of resources generated per employed person."
  const upgradeInfoText = "Increase the level and resource output by 1."
  const villageDevelopmentsInfoText = "Other village developments, send an application to work there and request a wage, or contest ownsership to takes the development for yourself."

  return (
    <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column", gap: "20px" }}>

      {/* --- SECTION 1: MY DEVELOPMENTS --- */}
      <div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "left", gap: "8px", marginBottom: "1em" }}>
          <h3 style={{ margin: 0 }}>My Developments</h3>
          <span style={{ color: "var(--light_grey)" }}>
            <InfoTooltip displayText={"ⓘ"} infoText={propertiesInfoText} />
          </span>
        </div>
        {hydratedMe.developments.length === 0 ? (
          <p style={{ color: "#888", fontStyle: "italic", fontSize: "0.85rem" }}>You own no land.</p>
        ) : (
          hydratedMe.developments.map((dev) => {
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
                          onClick={() => onContest(dev.id, "OWNER")}
                        >
                          Defend Property
                        </button>
                      ) : (
                        <>
                          <button
                            className="btn-tooltip"
                            style={{ background: "#795548", color: "white", flex: 1 }}
                            onClick={() => onMaintain(dev.id)}
                          >
                            Maintenance: {
                              gameState.development_costs[dev.type]?.maintain
                                ? Object.entries(gameState.development_costs[dev.type].maintain)
                                  .map(([resource, amount]) => `${amount} ${resource}`)
                                  .join(", ")
                                : "Unknown Cost"
                            }
                          </button>
                          <button
                            className="btn-tooltip"
                            style={{ background: "#f57c00", color: "white", flex: 1 }}
                            onClick={() => onUpgrade(dev.id)}
                          >
                            Upgrade: {
                              gameState.development_costs[dev.type]?.upgrade
                                ? Object.entries(gameState.development_costs[dev.type].upgrade)
                                  .map(([resource, amount]) => `${amount} ${resource}`)
                                  .join(", ")
                                : "Unknown Cost"
                            }
                          </button>
                        </>
                      )}
                    </div>
                    {dev.is_contested && dev.owner_id === me.id && (
                      <div
                        style={{
                          marginTop: "10px",
                          fontSize: "0.85rem",
                          display: "flex",
                          flexDirection: "column",
                          gap: "4px",
                          padding: "8px",
                          background: "#fff3f3",
                          border: "1px solid #f0b4b4",
                          borderRadius: "6px",
                        }}
                      >
                        <strong style={{ color: "#c62828" }}>⚔️ Your Property is Under Contest</strong>

                        <span>
                          Initiator: {getPlayerName(dev.contest_initiator_id)}
                        </span>

                        <span>
                          Attackers: {dev.contester_supporters?.length || 0}
                        </span>

                        <span>
                          Defenders: {dev.owner_supporters?.length || 0}
                        </span>
                      </div>
                    )}

                    {/* Pending Applications */}
                    {pendingApplications.length > 0 && (
                      <div style={{ marginTop: "15px", borderTop: "1px dashed #ccc", paddingTop: "10px" }}>
                        <strong style={{ fontSize: "0.85rem", color: "#2e7d32" }}>Job Applications:</strong>
                        {pendingApplications.map((app) => (
                          <div key={app.id} style={{ display: "flex", justifyContent: "space-between", marginTop: "5px", fontSize: "0.85rem", alignItems: "center" }}>
                            <span>{getPlayerName(app.initiator_id)} asking {app.wage} {app.wage_type}</span>
                            <div style={{ display: "flex", gap: "5px" }}>
                              <button className="btn-tooltip info" onClick={() => onAcceptApplicant(app.id)}>Hire</button>
                              <button className="btn-tooltip danger" onClick={() => onDenyApplicant(app.id)}>Reject</button>
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
        <div style={{ display: "flex", alignItems: "center", justifyContent: "left", gap: "8px", marginBottom: "1em" }}>
          <h3 style={{ margin: 0 }}>Village Developments</h3>
          <span style={{ color: "var(--light_grey)" }}>
            <InfoTooltip displayText={"ⓘ"} infoText={villageDevelopmentsInfoText} />
          </span>
        </div>
        {villageDevelopments.length === 0 ? (
          <p style={{ color: "#888", fontStyle: "italic", fontSize: "0.85rem" }}>No other properties exist.</p>
        ) : (
          villageDevelopments.map((dev) => {
            const isExpanded = expandedId === dev.id;

            const borderColor = dev.is_contested
              ? "#c62828"
              : "#ccc";

            return (
              <div
                key={dev.id}
                style={{
                  border: `2px solid ${borderColor}`,
                  borderRadius: "6px",
                  marginBottom: "8px",
                  background: dev.is_contested ? "#fff5f5" : "#fff",
                  overflow: "hidden",
                  boxShadow: dev.is_contested
                    ? "0 0 8px rgba(198,40,40,0.35)"
                    : "none",
                  transition: "all 0.2s ease"
                }}
              >

                {/* Accordion Header */}
                <div
                  style={{ padding: "8px 10px", display: "flex", justifyContent: "space-between", cursor: "pointer", background: isExpanded ? "#eee" : "transparent" }}
                  onClick={() => toggleExpand(dev.id)}
                >
                  <strong style={{ fontSize: "0.9rem" }}>{dev.type} (Lvl {dev.level})</strong>
                  <span style={{ fontSize: "0.8rem", color: getPlayerColor(dev.owner_id) }}>Owner: {getPlayerName(dev.owner_id)}</span>
                </div>

                {/* Accordion Body */}
                {isExpanded && (
                  <div style={{ padding: "10px", borderTop: "1px solid #ddd", display: "flex", flexDirection: "column", gap: "10px" }}>

                    {/* Apply for Job Form */}
                    {!dev.is_contested && (
                      <div
                        style={{
                          display: "flex",
                          gap: "5px",
                          alignItems: "center",
                          fontSize: "0.85rem"
                        }}
                      >
                        <span>Ask for:</span>

                        <input
                          type="number"
                          min="1"
                          value={appWage}
                          onChange={e => setAppWage(parseInt(e.target.value) || 1)}
                          style={{ width: "40px", padding: "2px" }}
                        />

                        <select
                          value={appWageType}
                          onChange={e => setAppWageType(e.target.value as Resource)}
                          style={{ padding: "2px" }}
                        >
                          <option value="food">Food</option>
                          <option value="wood">Wood</option>
                          <option value="iron">Iron</option>
                        </select>

                        <button
                          className="btn-tooltip success"
                          style={{ marginLeft: "auto" }}
                          onClick={() =>
                            onApplyForJob(
                              dev.owner_id,
                              dev.id,
                              appWage,
                              appWageType
                            )
                          }
                        >
                          Apply
                        </button>
                      </div>
                    )}

                    <div
                      style={{
                        marginTop: "15px",
                        borderTop: "1px dashed #ccc",
                        paddingTop: "10px",
                        width: "90%",
                        display: "flex",
                        gap: "8px",
                      }}
                    >

                      {/* NOT contested yet */}
                      {!dev.is_contested && dev.owner_id !== me.id && (
                        <button
                          className="btn-tooltip danger"
                          style={{ width: "100%", padding: "6px" }}
                          onClick={() => onContest(dev.id, "INITIATOR")}
                        >
                          Contest Ownership
                        </button>
                      )}

                      {/* Already contested */}
                      {dev.is_contested && (
                        <>
                          {/* Support attackers */}
                          <button
                            className="btn-tooltip warning"
                            style={{ flex: 1, padding: "6px" }}
                            onClick={() => onContest(dev.id, "CONTESTER")}
                          >
                            Support Contesters
                          </button>

                          {/* Support owner */}
                          <button
                            className="btn-tooltip success"
                            style={{ flex: 1, padding: "6px" }}
                            onClick={() => onContest(dev.id, "OWNER")}
                          >
                            Support Owner
                          </button>
                        </>
                      )}
                      {dev.is_contested && (
                        <div
                          style={{
                            marginTop: "10px",
                            fontSize: "0.8rem",
                            display: "flex",
                            flexDirection: "column",
                            gap: "4px",
                          }}
                        >
                          <span>
                            ⚔️ Initiator: {getPlayerName(dev.contest_initiator_id)}
                          </span>

                          <span>
                            Attackers: {dev.contester_supporters?.length || 0}
                          </span>

                          <span>
                            Defenders: {dev.owner_supporters?.length || 0}
                          </span>
                        </div>
                      )}
                    </div>
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
