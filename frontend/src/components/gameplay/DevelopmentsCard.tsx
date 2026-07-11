import React, { useState } from "react";
import { EmploymentActionDTO, Resource } from "../../dtos/index";
import { usePlayerName } from "../hooks/usePlayerName";
import { usePlayerColors } from "../hooks/usePlayerColor";
import { useGameState } from "../hooks/useGameState";
import InfoTooltip from "../InfoTooltip";
import { useEffect } from "react";

import styles from "./DevelopmentsCard.module.css";
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
  const { me, player_list } = gameState;
  const getPlayerName = usePlayerName();
  const { getPlayerColor } = usePlayerColors();

  // --- HYDRATION LOGIC ---
  const hydratedMe = {
    ...me,
    developments: gameState.developments.filter(
      (dev) => dev.owner_id === me.id
    )
  };

  const hydratedPlayerList = player_list.map((p) => ({
    ...p,
    developments: gameState.developments.filter(
      (dev) => dev.owner_id === p.id
    )
  }));  // -----------------------

  // Accordion State
  const [expandedIds, setExpandedIds] = useState<Set<string>>(() => {
    return new Set(); // start empty, then populate via effect
  });
  const didInitRef = React.useRef(false);

  useEffect(() => {
    if (didInitRef.current) return;

    didInitRef.current = true;

    setExpandedIds(
      new Set(hydratedMe.developments.map(d => d.id))
    );
  }, [hydratedMe.developments]);

  // Draft Job Application State
  const [appWage, setAppWage] = useState<number>(1);
  const [appWageType, setAppWageType] = useState<Resource>("food");

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
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

  const propertiesInfoText = "These are your developments, you can choose to spend your work phase at one of them or spend it upgrading or maintaining it. To build a development, click a hex on the map!"
  const maintenanceInfoText = "Level will decrease if maintenance is at 0, level is amount of resources generated per employed person."
  const upgradeInfoText = "Increase the level and resource output by 1."
  const villageDevelopmentsInfoText = "Other village developments, send an application to work there and request a wage, or contest ownsership to takes the development for yourself."
  const contestInfoText = "Start a contest for this dev. Spends your work action. Will need to break a tie with the owner so get people on your side to join the contest next work phase."
  return (
    <div className={`card ${styles.column}`} >

      {/* --- SECTION 1: MY DEVELOPMENTS --- */}
      <div>
        <div className={styles.row}>
          <h3 className={styles.header}>My Developments</h3>
          <span className={styles.text}>
            <InfoTooltip displayText={"ⓘ"} infoText={propertiesInfoText} />
          </span>
        </div>
        {hydratedMe.developments.length === 0 ? (
          <p className={styles.copy}>You own no land, click a hex on the map to build!</p>
        ) : (
          hydratedMe.developments.map((dev) => {
            const pendingApplications = employmentActions.filter(
              (a) => a.dev_id === dev.id && a.is_application && a.status === "PENDING"
            );

            // Determine border color based on urgency flags
            let borderColor = "#ccc";
            if (dev.is_contested) borderColor = "#c62828"; // Red for contested
            else if (pendingApplications.length > 0) borderColor = "#2e7d32"; // Green for applicants

            const isExpanded = expandedIds.has(dev.id);
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
                  <strong className={styles.field}>{dev.type} (Lvl {dev.level})</strong>
                  <span style={{ fontSize: "0.8rem", color: dev.maintenance_days < 2 ? "red" : "#666", fontWeight: "bold" }}>
                    {dev.is_contested ? "🔥 CONTESTED" : `Degrades in ${dev.maintenance_days}d`}
                  </span>
                </div>

                {/* Accordion Body */}
                {isExpanded && (
                  <div className={styles.field2}>

                    {/* Contextual Action Buttons */}
                    <div className={styles.field3}>
                      {dev.is_contested ? (
                        <button
                          className={`btn danger ${styles.field4}`}
                          
                          onClick={() => onContest(dev.id, "OWNER")}
                        >
                          Defend Property
                        </button>
                      ) : (
                        <>
                          {/* Wrapped Maintenance Button */}
                          <InfoTooltip infoText={maintenanceInfoText}>
                            <button
                              className={`btn-tooltip ${styles.field5}`}
                              
                              onClick={() => onMaintain(dev.id)}
                            >
                              Maintenance: {
                                dev.maintenance_cost
                                  ? Object.entries(dev.maintenance_cost)
                                    .map(([resource, amount]) => `${amount} ${resource}`)
                                    .join(", ")
                                  : "Unknown Cost"
                              }
                            </button>
                          </InfoTooltip>

                          {/* Wrapped Upgrade Button */}
                          <InfoTooltip infoText={upgradeInfoText}>
                            <button
                              className="btn-tooltip"
                              style={{
                                background: dev.can_upgrade ? "#f57c00" : "#777",
                                color: "white",
                                width: "100%",
                                cursor: dev.can_upgrade ? "pointer" : "not-allowed",
                                opacity: dev.can_upgrade ? 1 : 0.7
                              }}
                              onClick={() => onUpgrade(dev.id)}
                              disabled={!dev.can_upgrade}
                            >
                              {dev.can_upgrade
                                ? `Upgrade: ${dev.upgrade_cost
                                  ? Object.entries(dev.upgrade_cost)
                                    .map(([resource, amount]) => `${amount} ${resource}`)
                                    .join(", ")
                                  : "Unknown Cost"
                                }`
                                : "Max Level"}
                            </button>
                          </InfoTooltip>
                        </>
                      )}
                    </div>
                    {dev.is_contested && dev.owner_id === me.id && (
                      <div
                        className={styles.field6}
                      >
                        <strong className={styles.field7}>⚔️ Your Property is Under Contest</strong>

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
                      <div className={styles.field8}>
                        <strong className={styles.field9}>Job Applications:</strong>
                        {pendingApplications.map((app) => (
                          <div key={app.id} className={styles.field10}>
                            <span>{getPlayerName(app.initiator_id)} asking {app.wage} {app.wage_type}</span>
                            <div className={styles.field11}>
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
        <div className={styles.field12}>
          <h3 className={styles.field13}>Village Developments</h3>
          <span className={styles.field14}>
            <InfoTooltip displayText={"ⓘ"} infoText={villageDevelopmentsInfoText} />
          </span>
        </div>
        {villageDevelopments.length === 0 ? (
          <p className={styles.field15}>Nobody else has developed land yet.</p>
        ) : (
          villageDevelopments.map((dev) => {
            const isExpanded = expandedIds.has(dev.id);

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
                  <strong className={styles.field16}>{dev.type} (Lvl {dev.level})</strong>
                  <span style={{ fontSize: "0.8rem", color: getPlayerColor(dev.owner_id) }}>Owner: {getPlayerName(dev.owner_id)}</span>
                </div>

                {/* Accordion Body */}
                {isExpanded && (
                  <div className={styles.field17}>

                    {/* Apply for Job Form */}
                    {!dev.is_contested && (
                      <div
                        className={styles.field18}
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
                          className={`btn-tooltip success ${styles.field19}`}
                          
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
                      className={styles.field20}
                    >

                      {/* NOT contested yet */}
                      {!dev.is_contested && dev.owner_id !== me.id && (
                        <InfoTooltip infoText={contestInfoText} >
                          <button
                            className={`btn-tooltip danger ${styles.field21}`}
                            
                            onClick={() => onContest(dev.id, "INITIATOR")}
                          >
                            Contest Ownership
                          </button>
                        </InfoTooltip>

                      )}

                      {/* Already contested */}
                      {dev.is_contested && (
                        <>
                          {/* Support attackers */}
                          <InfoTooltip infoText={"Spend work phase supporting attackers"}>
                            <button
                              className={`btn-tooltip warning ${styles.field22}`}
                              
                              onClick={() => onContest(dev.id, "CONTESTER")}
                            >
                              Support Contesters
                            </button>
                          </InfoTooltip>

                          {/* Support owner */}
                          <InfoTooltip infoText={"Spend work phase supporting the owner"}>
                            <button
                              className={`btn-tooltip success ${styles.field23}`}
                              
                              onClick={() => onContest(dev.id, "OWNER")}
                            >
                              Support Owner
                            </button>

                          </InfoTooltip>
                        </>
                      )}
                      {dev.is_contested && (
                        <div
                          className={styles.field24}
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
                )
                }
              </div>
            );
          })
        )}
      </div>
    </div >
  );
};

export default DevelopmentsCard;
