import { usePlayers } from "./hooks/usePlayerName";
import { DevelopmentDTO } from "../../../dtos/index"

interface Props {
  playerId: string;
}

const PlayerDevelopmentsInfo: React.FC<Props> = ({ playerId }) => {
  const { players } = usePlayers();

  const player = players?.find((p) => p.id === playerId);

  if (!player) {
    return (<></>)
  }
  return (
    <span>
      {player.developments && player.developments.map((dev: DevelopmentDTO, index) => (
        <span key={index} style={{ marginLeft: "5px", overflowY: "auto" }}>
          {dev.type} (L.{dev.level})
        </span>
      ))}
    </span>

  )
}
export default PlayerDevelopmentsInfo;
