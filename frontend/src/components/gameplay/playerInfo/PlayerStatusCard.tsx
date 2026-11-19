import type { GameStateDTO } from "../../../dtos";
import { useGameState } from "../../hooks/useGameState";
import InfoTooltip from "../../InfoTooltip";
import styles from "./PlayerStatusCard.module.css";

const RESOURCE_TOOLTIPS = {
  overview:
    "Used for trade and health, make sure you have a food and a wood for fire at the end of the day!",
  wood: "Wood is used for lighting fires to keep warm and building/maintaining/upgrading developments",
  food: "1 food is eaten every day and used for building/maintaining/upgrading developments",
  iron: "Iron is used for building/maintaining/upgrading developments, very valuable to development owners!",
};

const HEALTH_TOOLTIPS = {
  overview: "You can't work or contest developments when sick or recovering!",
  healthy: "You are good! Keep eating and staying warm to have a low sickness chance.",
  recovering: "You are recovering! Keep eating and staying warm to get healthy tomorrow.",
  sick: "You are sick! If you don't eat and stay warm and get sick again, you will die. Eating and staying warm guarantees recovery with time",
  unknown: "Your current health status is unknown.",
};

const getHealthTooltipText = (health: string | undefined): string => {
  switch (health) {
    case "healthy":
      return HEALTH_TOOLTIPS.healthy;
    case "sick":
      return HEALTH_TOOLTIPS.sick;
    case "recovering":
      return HEALTH_TOOLTIPS.recovering;
    default:
      return HEALTH_TOOLTIPS.unknown;
  }
};

const getSicknessChanceTooltipText = (gameState: GameStateDTO): string => {
  const hungerRatePercent = ((gameState?.hunger_sickness_rate ?? 0) * 100).toFixed(0);
  const coldRatePercent = ((gameState?.cold_sickness_rate ?? 0) * 100).toFixed(0);
  const recoveryRatePercent = ((gameState?.recovery_rate ?? 0) * 100).toFixed(0);

  return `Chance you get sick during the night (Hunger: +${hungerRatePercent}%, Cold: +${coldRatePercent}%). Your chance drops ${recoveryRatePercent}% upon both eating and being warm at night. Being sick/recovering means you can't work.`;
};

const PlayerStatusCard = () => {
  const gameState = useGameState();
  const { me } = gameState;

  const woodCount = me.resources?.wood || 0;
  const foodCount = me.resources?.food || 0;
  const ironCount = me.resources?.iron || 0;

  const healthDisplay = me.health ? me.health.toUpperCase() : "UNKNOWN";
  const healthStyle = me.health === "healthy" ? styles.healthGood : styles.healthBad;
  const sicknessChancePercent = ((me.sickness_chance || 0) * 100).toFixed(0);

  return (
    <div className={`card ${styles.statusBar}`}>
      {/* Resources Section */}
      <div className={styles.resourcesSection}>
        <div className={styles.sectionHeader}>
          <h3 className={styles.sectionTitle}>My Resources</h3>
          <span className={styles.tooltipWrapper}>
            <InfoTooltip displayText="ⓘ" infoText={RESOURCE_TOOLTIPS.overview} />
          </span>
        </div>
        <ul className={styles.resourceList}>
          <li>
            🪵 <InfoTooltip displayText="Wood: " infoText={RESOURCE_TOOLTIPS.wood} />{" "}
            <strong>{woodCount}</strong>
          </li>
          <li>
            🍎 <InfoTooltip displayText="Food: " infoText={RESOURCE_TOOLTIPS.food} />{" "}
            <strong>{foodCount}</strong>
          </li>
          <li>
            ⛏️ <InfoTooltip displayText="Iron: " infoText={RESOURCE_TOOLTIPS.iron} />{" "}
            <strong>{ironCount}</strong>
          </li>
        </ul>
      </div>

      {/* Vertical Divider */}
      <div className={styles.verticalDivider} />

      {/* Health Section */}
      <div className={styles.healthSection}>
        <div className={styles.sectionHeader}>
          <h3 className={styles.sectionTitle}>Health</h3>
          <span className={styles.tooltipWrapper}>
            <InfoTooltip displayText="ⓘ" infoText={HEALTH_TOOLTIPS.overview} />
          </span>
        </div>

        <div className={styles.healthMetrics}>
          <div className={styles.metricItem}>
            <p className={styles.metricCopy}>
              <InfoTooltip
                displayText="State: "
                infoText={getHealthTooltipText(me.health)}
              />
              <strong className={`${styles.statusLabel} ${healthStyle}`}>
                {healthDisplay}
              </strong>
            </p>
          </div>

          <div className={styles.metricItem}>
            <p className={styles.metricCopy}>
              <InfoTooltip
                displayText={`Sickness Chance: ${sicknessChancePercent}%`}
                infoText={getSicknessChanceTooltipText(gameState)}
              />
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlayerStatusCard;
