import { usePlayers } from "../../hooks/usePlayerName";
import InfoTooltip from "../../InfoTooltip";
import PlayerInfo from "./PlayerInfo";
import styles from "./PlayerRoster.module.css";

const VILLAGE_ROSTER_INFO_TEXT =
  "Hover on a player to see their health and developments";

const PlayerRoster = () => {
  const { players } = usePlayers();

  if (!players || players.length === 0) {
    return <div>No Players Found.</div>;
  }

  return (
    <div className="card">
      <div className={styles.cardTitleRow}>
        <h3 className={styles.title}>Village Roster</h3>
        <span className={styles.tooltipWrapper}>
          <InfoTooltip displayText="ⓘ" infoText={VILLAGE_ROSTER_INFO_TEXT} />
        </span>
      </div>
      <ul className={styles.list}>
        {players.map((player) => (
          <li className={styles.item} key={player.id}>
            <PlayerInfo playerId={player.id} />
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PlayerRoster;
