import { usePlayers } from "../../hooks/usePlayerName";
import PlayerInfo from "../playerInfo/PlayerInfo"
import InfoTooltip from "../../InfoTooltip";
import styles from "./PlayerRoster.module.css";
const PlayerRoster = () => {
  const { players } = usePlayers();

  if (!players || players.length === 0) {
    return <div>No Players Found.</div>;
  }

  const villageRosterInfoText = "Hover on a player to see their health and developments"

  return (
    <div className="card">
      <div className={styles.row}>
        <h3 className={styles.header}>Village Roster</h3>
        <span className={styles.text}>
          <InfoTooltip displayText={"ⓘ"} infoText={villageRosterInfoText} />
        </span>
      </div>
      <ul className={styles.list}>
        {players.map((player) => (
          <li key={player.id} className={styles.item}>
            <PlayerInfo playerId={player.id} />
          </li>
        ))}
      </ul>
    </div>
  );
}
export default PlayerRoster;
