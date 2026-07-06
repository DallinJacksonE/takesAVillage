import React from "react";
import { useGameState } from "../../hooks/useGameState"; // Import the hook
import InfoTooltip from "../../InfoTooltip";

import styles from "./PlayerStatusCard.module.css";
const PlayerStatusCard: React.FC = () => {
  const gameState = useGameState();
  const { me } = gameState;

  const resourcesInfoText = "Used for trade and health, make sure you have a food and a wood for fire at the end of the day!"
  const woodInfoText = "Wood is used for lighting fires to keep warm and building/maintaining/upgrading developments"
  const foodInfoText = "1 food is eaten every day and used for building/maintaining/upgrading developments"
  const ironInfoText = "Iron is used for building/maintaining/upgrading developments, very valuable to development owners!"
  const sicknesschanceInfoText =
    `Chance you get sick during the night (Hunger: +${((gameState?.hunger_sickness_rate ?? 0) * 100).toFixed(0)}%, Cold: +${((gameState?.cold_sickness_rate ?? 0) * 100).toFixed(0)}%). Your chance drops ${((gameState?.recovery_rate ?? 0) * 100).toFixed(0)}% upon both eating and being warm at night. Being sick/recovering means you can't work.`;
  const healthStateTextHealthy = "You are good! Keep eating and staying warm to have a low sickness chance."
  const healthStateTextRecovering = "You are recovering! Keep eating and staying warm to get healthy tomorrow."
  const healthStateTextSick = "You are sick! If you don't eat and stay warm and get sick again, you will die. Eating and staying warm gurantees recovery with time"
  const healthInfoText = "You can't work or contest developments when sick or recovering!"

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
      className={`card ${styles.statusBar} ${styles.row7}`}
      
    >
      {/* Resources Section */}
      <div className={styles.panel3}>
        <div className={styles.row6}>
          <h3 className={styles.header2}>My Resources</h3>
          <span className={styles.text2}>
            <InfoTooltip displayText={"ⓘ"} infoText={resourcesInfoText} />
          </span>
        </div>
        <ul className={styles.row5}>
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
      <div className={styles.panel2}></div>

      {/* Health Section */}
      <div className={styles.panel}>
        <div className={styles.row4}>
          <h3 className={styles.header}>Health</h3>
          <span className={styles.text}>
            <InfoTooltip displayText={"ⓘ"} infoText={healthInfoText} />
          </span>
        </div>
        <div className={styles.row3}>
          <div className={styles.row2}>
            <p className={styles.copy3}>
              <InfoTooltip
                displayText={`State: `}
                infoText={getHealthTooltipText(me.health)}
              />

              <strong className={[styles.label, me.health === "healthy" ? styles.healthGood : styles.healthBad].join(" ")}>
                {me.health ? me.health.toUpperCase() : "UNKNOWN"}
              </strong>
            </p>


          </div>
          <div className={styles.row}>
            <p className={styles.copy2}>
              <InfoTooltip
                displayText={`Sickness Chance: ${((me.sickness_chance || 0) * 100).toFixed(0)}%`}
                infoText={sicknesschanceInfoText}
              />

            </p>


          </div>

          <p className={styles.copy}>
          </p>
        </div>
      </div>
    </div>
  );
};

export default PlayerStatusCard;
