import { usePlayers } from "./hooks/usePlayerName";
import PlayerInfo from "./PlayerInfo"

const PlayerRoster = () => {
  const { players } = usePlayers();

  if (!players || players.length === 0) {
    return <div>No Players Found.</div>;
  }

  return (
    <div className="card">
      <h3>Villagers</h3>
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
