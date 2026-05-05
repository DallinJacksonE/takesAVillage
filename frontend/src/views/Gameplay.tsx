import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import StatusCards from "../components/StatusCards";
import VillageMap from "../components/VillageMap";
import MessageBoard from "../components/MessageBoard";
import { GameStateDTO } from "../../../dtos";
import { PlayerProvider } from "../components/hooks/usePlayerName";
import {
  GameplayPresenter,
  GameplayView,
} from "../presenters/GameplayPresenter";
import PlayerStatusCard from "../components/PlayerStatusCard";
import DevelopmentsCard from "../components/DevelopmentsCard";
import AvailableWorkCard from "../components/AvailableWorkCard";
import { MOCK_STATE, MOCK_ME } from "./mockData";
import PlayerRoster from "../components/PlayerRoster";
import TradeDesk from "../components/TradeDesk";
import TabbedCommunicator from "../components/TabbedCommunicator";
import CampfireRing from "../components/CampfireRing";

const Gameplay: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const [presenter, setPresenter] = useState<GameplayPresenter | null>(null);
  const [gameState, setGameState] = useState<GameStateDTO | null>(null);
  const [playerCount, setPlayerCount] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [userId, setUserId] = useState("");

  useEffect(() => {

    if (gameId === "test-render") {
      setGameState(MOCK_STATE);
      setPlayerCount(MOCK_STATE.player_list.length); // Dynamically set to 8 based on the mock array
      setTimeLeft(MOCK_STATE.time_remaining);
      setUserId(MOCK_ME.id);

      const dummyPresenter = {
        handleStartGame: () => console.log("[MOCK] Start Game triggered"),
        handleUserAction: (action: string, payload: any) => console.log(`[MOCK] Action: ${action}`, payload),
        handleSendMessage: (payload: any) => console.log("[MOCK] Send Message:", payload),
        destroy: () => console.log("[MOCK] Cleanup"),
      } as unknown as GameplayPresenter;

      setPresenter(dummyPresenter);
      return;
    }


    if (gameId) {
      const view: GameplayView = {
        setGameState,
        setPlayerCount,
        setTimeLeft,
        setUserId,
        showAlert: (message: string) => alert(message),
      };
      const gameplayPresenter = new GameplayPresenter(view, gameId);
      setPresenter(gameplayPresenter);

      return () => {
        gameplayPresenter.destroy();
      };
    }
  }, [gameId]);

  if (!presenter || !gameState) return <div>Connecting...</div>;

  if (gameState.status === "WAITING") {
    return (
      <div
        className="container"
        style={{ textAlign: "center", marginTop: "50px" }}
      >
        <h1>Waiting for Players...</h1>
        <h2>Game ID: {gameId}</h2>
        <p>Players: {playerCount}</p>
        {gameState.is_host && (
          <button className="btn" onClick={() => presenter.handleStartGame()}>
            Start Game
          </button>
        )}
      </div>
    );
  }

  const { day, phase } = gameState;

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          borderBottom: "2px solid #333",
          paddingBottom: "10px",
          marginBottom: "20px",
        }}
      >
        <h2>{gameState.me.name}</h2>
        <h2 style={{ color: "#2e7d32" }}>
          Day {day}: {phase}
        </h2>
        <h3>
          {Math.floor(timeLeft / 60)}:
          {(timeLeft % 60).toString().padStart(2, "0")}
        </h3>
      </div>

      <PlayerProvider players={gameState.player_list || []}>
        <PlayerStatusCard state={gameState} />
        {/* NEW LAYOUT: Flex container for the side-by-side split */}
        <div style={{ display: "flex", gap: "20px", height: "650px", marginBottom: "20px", minWidth: 0 }}>

          {/* MAIN COLUMN (flex: 2) - Dynamic Phase Cards */}
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", flex: 3, minWidth: 0 }}>

            {phase === "WORK" && (
              <div style={{ display: "flex", gap: "20px", height: "100%" }}>
                {/* We pass onSend down so these cards can interact directly with the Message API */}
                <DevelopmentsCard
                  state={gameState}
                  onSend={(payload) => presenter.handleSendMessage(payload)}
                />
                <AvailableWorkCard
                  state={gameState}
                  map={gameState.map || []}
                  onAction={(action, payload) => presenter.handleUserAction(action, payload)}
                  onSend={(payload) => presenter.handleSendMessage(payload)}
                />
              </div>
            )}

            {phase === "TRADE" && (
              <TradeDesk
                state={gameState}
                onSend={(payload) => presenter.handleSendMessage(payload)}
              />
            )}

            {phase === "NIGHT" && (
              <CampfireRing
                state={gameState}
                onSend={(payload) => presenter.handleSendMessage(payload)}
                onAction={(action, payload) => presenter.handleUserAction(action, payload)}
              />
            )}

          </div>

          {/* RIGHT COLUMN (flex: 2) - Roster and Tabbed Chat */}
          <div style={{ flex: 2, display: "flex", flexDirection: "column", gap: "10px", minWidth: 0 }}>
            <PlayerRoster />
            <TabbedCommunicator
              messages={gameState.messages || []}
              playerId={userId}
              players={gameState.player_list || []}
              onSend={(payload) => presenter.handleSendMessage(payload)}
            />
          </div>
        </div>
        {phase === "TRADE" && (
          <>
            {!gameState.me.finished_phase ? (
              <div
                className="card"
                style={{
                  background: "#D4ECD6",
                  textAlign: "center",
                  margin: "20px 0",
                }}
              >
                <button
                  className="btn"
                  onClick={() => presenter.handleUserAction("FINISH_PHASE", {})}
                >
                  Finish Trading
                </button>
              </div>
            ) : (
              <div
                className="card"
                style={{
                  background: "#e59f71",
                  textAlign: "center",
                  margin: "20px 0",
                }}
              >
                Waiting For Others To Finish
              </div>
            )}
          </>
        )}

        {phase === "NIGHT" && (
          <>
            {!gameState.me.finished_phase ? (
              <div
                className="card"
                style={{
                  background: "#333",
                  color: "white",
                  textAlign: "center",
                  margin: "20px 0",
                }}
              >
                <button
                  className="btn"
                  onClick={() => presenter.handleUserAction("FINISH_PHASE", {})}
                >
                  End Day
                </button>
              </div>
            ) : (
              <div
                className="card"
                style={{
                  background: "#e59f71",
                  textAlign: "center",
                  margin: "20px 0",
                }}
              >
                Waiting For Others To Finish
              </div>
            )}
          </>
        )}

        {gameState.map && (
          <VillageMap
            mapData={gameState.map}
            playerId={userId}
            onAction={(action, payload) =>
              presenter.handleUserAction(action, payload)
            }
          />
        )}
      </PlayerProvider>
    </div>
  );
};

export default Gameplay;
