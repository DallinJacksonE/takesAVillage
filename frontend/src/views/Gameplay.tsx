import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import VillageMap from "../components/VillageMap";
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
      setPlayerCount(MOCK_STATE.player_list.length);
      setTimeLeft(MOCK_STATE.time_remaining);
      setUserId(MOCK_ME.id);

      const dummyPresenter = {
        submitAction: (action: string, payload: any) =>
          console.log("Mock Action Submitted:", action, payload),
        sendChat: (content: string, toId: string) =>
          console.log("Mock Chat Sent:", content, "to", toId),
        destroy: () => { },
      } as unknown as GameplayPresenter;

      setPresenter(dummyPresenter);
      return;
    }

    const view: GameplayView = {
      setGameState,
      setPlayerCount,
      setTimeLeft,
      setUserId,
      showAlert: (msg: string) => alert(msg),
    };

    const newPresenter = new GameplayPresenter(view, gameId || "");
    setPresenter(newPresenter);

    return () => newPresenter.destroy();
  }, [gameId]);

  if (!gameState || !presenter) return <div>Loading...</div>;

  const { phase } = gameState;

  if (gameState.status === "WAITING") {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <h2>Waiting Room: Village {gameId}</h2>
        <p>Players Joined: {playerCount} / 10</p>

        {/* Render Host Controls */}
        {gameState.is_host ? (
          <div>
            <button
              onClick={() => presenter.handleStartGame()}
              disabled={playerCount < 1}
              style={{ padding: "10px 20px", fontSize: "16px", cursor: playerCount >= 2 ? "pointer" : "not-allowed" }}
            >
              Start Game
            </button>
            {playerCount < 2 && <p style={{ color: "red" }}>Need at least 2 players to start.</p>}
          </div>
        ) : (
          /* Render Guest View */
          <div>
            <p>Waiting for the host to start the game...</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ padding: "20px" }}>
      <PlayerProvider players={gameState.player_list}>
        {/* --- HEADER --- */}
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px" }}>
          <h2>Village: {gameId} (Players: {playerCount})</h2>
          <div>
            <strong>Day {gameState.day}</strong> | Phase: {phase} | Time:{" "}
            {timeLeft}s
          </div>
        </div>

        {/* --- MAIN DASHBOARD GRID --- */}
        <div style={{ display: "flex", gap: "20px", marginBottom: "20px" }}>

          {/* LEFT COLUMN: Player Stats & Phase Mechanics */}
          <div style={{ flex: 2, display: "flex", flexDirection: "column", gap: "20px" }}>
            <PlayerStatusCard state={gameState} />

            {/* Phase Routing */}
            {phase === "WORK" && (
              <div style={{ display: "flex", gap: "20px" }}>
                <DevelopmentsCard
                  state={gameState}
                  onSend={(payload) => presenter.submitAction(payload.actionCommand || payload.action, payload)}
                />
                <AvailableWorkCard
                  state={gameState}
                  onSend={(payload) => presenter.submitAction(payload.actionCommand || payload.action, payload)}
                />
              </div>
            )}

            {phase === "TRADE" && (
              <TradeDesk
                state={gameState}
                onSend={(payload) => presenter.submitAction(payload.actionCommand || payload.action, payload)}
              />
            )}

            {phase === "NIGHT" && (
              <CampfireRing
                state={gameState}
                onSend={(payload) => presenter.submitAction(payload.actionCommand || payload.action, payload)}
                onAction={(actionCommand, payload) => presenter.submitAction(actionCommand, payload)}
              />
            )}

            {/* End Phase Lock-In */}
            {!gameState.me.finished_phase ? (
              <div className="card" style={{ background: "#333", color: "white", textAlign: "center" }}>
                <button
                  className="btn"
                  onClick={() => presenter.submitAction("FINISH_PHASE")}
                >
                  {phase === "NIGHT" ? "End Day" : "End Phase"}
                </button>
              </div>
            ) : (
              <div className="card" style={{ background: "#e59f71", textAlign: "center" }}>
                Waiting For Others To Finish
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: Roster & Social Chat */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "20px" }}>
            <PlayerRoster />
            <TabbedCommunicator
              messages={gameState.chat_messages as any} // Cast if needed depending on how your interface is strictly set
              playerId={userId}
              players={gameState.player_list}
              onSend={(content: string, toId: string) => presenter.sendChat(content, toId)}
            />
          </div>
        </div>

        {/* --- MAP --- */}
        {gameState.map && (
          <div className="card">
            <h3>Village Map</h3>
            <VillageMap
              mapData={gameState.map}
              playerId={userId}
              development_costs={gameState.development_costs}
              onAction={(actionCommand, payload) =>
                presenter.submitAction(actionCommand, payload)
              }
            />

          </div>
        )}
      </PlayerProvider>
    </div>
  );
};

export default Gameplay;
