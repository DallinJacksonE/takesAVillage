import { usePlayers } from "./hooks/usePlayerName";
import PlayerInfo from "./PlayerInfo"
import InfoTooltip from "./InfoTooltip";
const PlayerRoster = () => {
  const { players } = usePlayers();

  if (!players || players.length === 0) {
    return <div>No Players Found.</div>;
  }

  const villageRosterInfoText = "Hover on a player to see their health and developments"

  return (
    <div className="card">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "left", gap: "8px", marginBottom: "1em" }}>
        <h3 style={{ margin: 0 }}>Village Roster</h3>
        <span style={{ color: '"var(--light_grey)"' }}>
          <InfoTooltip displayText={"ⓘ"} infoText={villageRosterInfoText} />
        </span>
      </div>
      <ul style={{ listStyleType: 'none' }}>
        {players.map((player) => (
          <li key={player.id} style={{ marginBottom: "8px" }}>
            <PlayerInfo playerId={player.id} />
          </li>
        ))}
      </ul>
    </div>
  );
}
export default PlayerRoster;
