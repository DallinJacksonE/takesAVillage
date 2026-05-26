import React from "react";
import { useGameState } from "./hooks/useGameState"; // Import the hook
import InfoTooltip from "./InfoTooltip";

const PlayerStatusCard: React.FC = () => {
  const gameState = useGameState();
  const { me } = gameState;

  const resourcesInfoText = "Used for trade and health, make sure you have a food and a wood for fire at the end of the day!"
  const woodInfoText = "Wood is used for lighting fires to keep warm and building/maintaining/upgrading developments"
  const foodInfoText = "1 food is eaten every day and used for building/maintaining/upgrading developments"
  const ironInfoText = "Iron is used for building/maintaining/upgrading developments, very valuable to development owners!"
  const healthInfoText = "Chance you get sick during the night, goes up if you don't eat or stay warm. Being sick means you can't work."
  const healthStateTextHealthy = "You are good! Keep eating and staying warm to have a low sickness chance."
  const healthStateTextRecovering = "You are recovering! Keep eating and staying warm to get healthy tomorrow."
  const healthStateTextSick = "You are sick! If you don't eat and stay warm and get sick again, you will die."

  const getHealthTooltipText = (health: string) => {
    switch (health) {
      case "healthy":
        return healthStateTextHealthy;
      case "sick":
        return healthStateTextSick;
      case "recovering":
        return healthStateTextRecovering;
      default:
        return "Your current health status is unknown.";
    }
  };
  return (
    <div
      className='card bar'
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "1rem",
        marginBottom: "20px",
      }}
    >
      {/* Resources Section */}
      <div style={{ flex: 2 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "left", gap: "8px", marginBottom: "1em" }}>
          <h3 style={{ margin: 0 }}>My Resources</h3>
          <span style={{ color: "var(--light_grey)" }}>
            <InfoTooltip displayText={"ⓘ"} infoText={resourcesInfoText} />
          </span>
        </div>
        <ul style={{
          listStyle: "none",
          padding: 0,
          display: "flex",
          gap: "1.5rem",
          margin: 0
        }}>
          <li>
            🪵 <InfoTooltip
              displayText={"Wood: "}
              infoText={woodInfoText}
            /> <strong>{me.resources?.wood || 0}</strong>
          </li>
          <li>
            🍎 <InfoTooltip
              displayText={"Food: "}
              infoText={foodInfoText}
            />
            <strong>{me.resources?.food || 0}</strong>
          </li>
          <li>
            ⛏️ <InfoTooltip
              displayText={"Iron: "}
              infoText={ironInfoText}
            />
            <strong>{me.resources?.iron || 0}</strong>
          </li>
        </ul>
      </div>

      {/* Vertical Divider */}
      <div style={{ width: "1px", height: "60px", background: "#eee" }}></div>

      {/* Health Section */}
      <div style={{ flex: 1, minWidth: "200px", paddingLeft: "20px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "left", gap: "8px", marginBottom: "1em" }}>
          <h3 style={{ margin: 0 }}>Health</h3>
          <span style={{ color: "var(--light_grey)" }}>
            <InfoTooltip displayText={"ⓘ"} infoText={healthInfoText} />
          </span>
        </div>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <p style={{ margin: 0 }}>
              <InfoTooltip
                displayText={`State: `}
                infoText={getHealthTooltipText(me.health)}
              />

              <strong style={{ color: me.health === "healthy" ? "#2e7d32" : "#c62828" }}>
                {me.health ? me.health.toUpperCase() : "UNKNOWN"}
              </strong>
            </p>


          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <p style={{ margin: 0 }}>
              <InfoTooltip
                displayText={`Sickness: ${((me.sickness_chance || 0) * 100).toFixed(0)}%`}
                infoText={healthInfoText}
              />

            </p>


          </div>

          <p style={{ margin: 0 }}>
          </p>
        </div>
      </div>
    </div>
  );
};

export default PlayerStatusCard;
