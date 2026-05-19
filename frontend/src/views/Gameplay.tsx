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
import { PlayerColorProvider } from "../components/hooks/usePlayerColor";
import PlayerInfo from "../components/PlayerInfo";
import { GameStateProvider } from "../components/hooks/useGameState";


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

      // Update mock to reflect new specific presenter methods
      const dummyPresenter = {
        handleStartGame: () => console.log("Mock: Start Game"),
        sendChat: (content: string, toId: string) => console.log("Mock Chat:", content, toId),
        buildDevelopment: (id: string) => console.log("Mock Build:", id),
        maintainDevelopment: (id: string) => console.log("Mock Maintain:", id),
        upgradeDevelopment: (id: string) => console.log("Mock Upgrade:", id),
        contestDevelopment: (id: string) => console.log("Mock Contest:", id),
        draftTrade: (target: string, offer: any, req: any) => console.log("Mock Draft Trade:", target),
        counterTrade: (id: string, offer: any, req: any) => console.log("Mock Counter Trade:", id),
        finalizeTrade: (id: string, items: any) => console.log("Mock Finalize Trade:", id),
        draftEmployment: (target: string, dev: string, wage: number) => console.log("Mock Job App to:", target),
        startFire: () => console.log("Mock Start Fire"),
        draftCampfire: (target: string, isReq: boolean) => console.log("Mock Campfire:", target),
        acceptContract: (id: string) => console.log("Mock Accept:", id),
        denyContract: (id: string) => console.log("Mock Deny:", id),
        cancelContract: (id: string) => console.log("Mock Cancel:", id),
        commitWork: (payload: any) => console.log("Mock Commit Work:", payload),
        finishPhase: () => console.log("Mock Finish Phase"),
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

  if (gameState.status === "WAITING") {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <h2>Waiting Room: Village {gameId}</h2>
        <p>Players: {playerCount} / 10</p>
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
          <div>
            <p>Waiting for the host to start the game...</p>
          </div>
        )}
      </div>
    );
  }

  if (gameState.status === "ENDED") {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <h2>Game Over: Village {gameId}</h2>
        <p>Thank you for playing</p>
      </div>
    );
  }

  const isDead = gameState.me.health === "dead";

  if (isDead) {
    return (
      <div className="observation-screen">
        <GameStateProvider gameState={gameState}>
          <PlayerProvider players={gameState.player_list}>
            <h2>You have perished.</h2>
            <p>You are now observing the village.</p>
            <PlayerRoster />
            <VillageMap
              mapData={gameState.map}
              playerId={userId}
              development_costs={gameState.development_costs}
              onBuild={(tileId) => presenter.buildDevelopment(tileId)}
            />

          </PlayerProvider>
        </GameStateProvider>
      </div>
    );
  }
  console.log(gameState)
  return (
    <div style={{ padding: "20px" }}>
      <GameStateProvider gameState={gameState}>
        <PlayerColorProvider gameState={gameState}>
          <PlayerProvider players={gameState.player_list}>
            {/* --- HEADER --- */}
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px" }}>
              <h2>Village: {gameId} <PlayerInfo playerId={gameState.me.id} /></h2>
              <div>
                <strong>Day {gameState.day}</strong> | Phase: {gameState.phase} | Time:{" "}
                {timeLeft}s
              </div>
            </div>

            {/* --- MAIN DASHBOARD GRID --- */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "2fr 1fr", /* Strict 2:1 ratio */
              gap: "20px",
              marginBottom: "20px",
              alignItems: "start" /* Prevents the columns from forcibly matching heights */
            }}>

              {/* LEFT COLUMN: Player Stats & Phase Mechanics */}
              <div style={{ display: "flex", flexDirection: "column", gap: "20px", minWidth: 0 }}>
                <PlayerStatusCard />

                {/* Phase Routing */}
                {gameState.phase === "WORK" && (
                  <div style={{ display: "flex", gap: "20px" }}>
                    <DevelopmentsCard
                      onMaintain={(devId) => presenter.maintainDevelopment(devId)}
                      onUpgrade={(devId) => presenter.upgradeDevelopment(devId)}
                      onContest={(devId, side) => presenter.contestDevelopment(devId, side)}
                      onApplyForJob={(targetId, devId, wage, wageType) => presenter.draftEmployment(targetId, devId, wage, wageType, true)}
                      onAcceptApplicant={(actionId) => presenter.acceptContract(actionId, "EMPLOYMENT")}
                      onDenyApplicant={(actionId) => presenter.denyContract(actionId, "EMPLOYMENT")}
                    />
                    <AvailableWorkCard
                      onCommitWork={(payload) => presenter.commitWork(payload)}
                      onAcceptOffer={(actionId) => presenter.acceptContract(actionId, "EMPLOYMENT")}
                      onDenyOffer={(actionId) => presenter.denyContract(actionId, "EMPLOYMENT")}
                    />
                  </div>
                )}

                {gameState.phase === "TRADE" && (
                  <TradeDesk
                    state={gameState}
                    onDraftTrade={(targetId, offer, req) => presenter.draftTrade(targetId, offer, req)}
                    onCounterTrade={(actionId, offer, req) => presenter.counterTrade(actionId, offer, req)}
                    onAcceptTrade={(actionId) => presenter.acceptContract(actionId)}
                    onDenyTrade={(actionId) => presenter.denyContract(actionId)}
                    onCancelTrade={(actionId) => presenter.cancelContract(actionId)}
                    onFinalizeTrade={(actionId, items) => presenter.finalizeTrade(actionId, items)}
                  />
                )}

                {gameState.phase === "NIGHT" && (
                  <CampfireRing
                    state={gameState}
                    onStartFire={() => presenter.startFire()}
                    onRequestSeat={(targetId) => presenter.draftCampfire(targetId, true)}
                    onOfferSeat={(targetId) => presenter.draftCampfire(targetId, false)}
                    onAccept={(actionId) => presenter.acceptContract(actionId)}
                    onDeny={(actionId) => presenter.denyContract(actionId)}
                  />
                )}

                {/* End Phase Lock-In */}
                {!gameState.me.finished_phase ? (
                  <div className="card card-finish_phase" style={{ color: "white", textAlign: "center" }}>
                    <button
                      className="btn"
                      onClick={() => presenter.finishPhase()}
                    >
                      {gameState.phase === "NIGHT" ? "End Day" : "End Phase"}
                    </button>
                  </div>
                ) : (
                  <div className="card card-waiting" style={{ textAlign: "center" }}>
                    Waiting For Others To Finish
                  </div>
                )}
              </div>

              {/* RIGHT COLUMN: Roster & Social Chat */}
              {/* minWidth: 0 prevents the chat from blowing out the grid horizontally */}
              <div style={{ display: "flex", flexDirection: "column", gap: "20px", minWidth: 0 }}>
                <PlayerRoster />
                <TabbedCommunicator
                  messages={gameState.chat_messages as any}
                  playerId={userId}
                  players={gameState.player_list}
                  onSend={(content: string, toId: string) => presenter.sendChat(content, toId)}
                />
              </div>
            </div>

            {/* --- MAP --- */}
            {gameState.map && (
              <div className="card" style={{ backgroundColor: "var(--medium_honey)" }}>
                <h3>Village Map</h3>
                <VillageMap
                  mapData={gameState.map}
                  playerId={userId}
                  development_costs={gameState.development_costs}
                  onBuild={(tileId) => presenter.buildDevelopment(tileId)}
                />
              </div>
            )}
          </PlayerProvider>
        </PlayerColorProvider>
      </GameStateProvider>
    </div >
  );
};

export default Gameplay;
