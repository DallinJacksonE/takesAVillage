import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import VillageMap from "../components/VillageMap";
import { GameStateDTO, ChatMessageDTO } from "../../../dtos";
import { PlayerProvider } from "../components/hooks/usePlayerName";
import {
  GameplayPresenter,
  GameplayView,
} from "../presenters/GameplayPresenter";
import InfoTooltip from "../components/InfoTooltip"
import PlayerStatusCard from "../components/PlayerStatusCard";
import DevelopmentsCard from "../components/DevelopmentsCard";
import AvailableWorkCard from "../components/AvailableWorkCard";
import PlayerRoster from "../components/PlayerRoster";
import TradeDesk from "../components/TradeDesk";
import TabbedCommunicator from "../components/TabbedCommunicator";
import CampfireRing from "../components/CampfireRing";
import { PlayerColorProvider } from "../components/hooks/usePlayerColor";
import PlayerInfo from "../components/PlayerInfo";
import { GameStateProvider } from "../components/hooks/useGameState";


const Gameplay: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const presenterRef =
    React.useRef<GameplayPresenter | null>(null);
  const [gameState, setGameState] = useState<GameStateDTO | null>(null);
  const [playerCount, setPlayerCount] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [userId, setUserId] = useState("");
  const [messages, setMessages] = useState<ChatMessageDTO[]>([]);
  const getPhaseTooltip = (phase: string) => {
    switch (phase) {
      case "WORK":
        return "Work phase: build developments, work them, hire others, and prepare to feed yourself and stay warm. Working for others gives them the resources and they promise to give back the desired wage during the trade phase";
      case "TRADE":
        return "Trade phase: negotiate deals, exchange resources, and finalize contracts. Will you be honest to build your reputation or lie for profit?";
      case "NIGHT":
        return "Night phase: Get fire by either starting your own or sitting at someone else's. Fire seats can be traded too during the trade phase! Eat and stay warm to minimize sickness chance.";
      default:
        return "";
    }
  };

  useEffect(() => {

    if (!gameId) return;

    const view: GameplayView = {
      setGameState,
      setPlayerCount,
      setTimeLeft,
      setUserId,
      showAlert: (msg: string) => alert(msg),

      setChatHistory: setMessages,
      addChatMessage: (msg: ChatMessageDTO) =>
        setMessages(prev => [...prev, msg]),
    };

    const presenter =
      new GameplayPresenter(view, gameId);

    presenterRef.current = presenter;

    return () => {

      presenter.destroy();

      presenterRef.current = null;
    };

  }, [gameId]);

  const presenter = presenterRef.current;

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
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
                marginBottom: "20px",
                gap: "8px"
              }}
            >
              <h2 style={{ margin: 0, fontSize: '1.8rem' }}>
                Village: {gameId}{" "}
                <PlayerInfo playerId={gameState.me.id} />

                <span
                  style={{
                    marginLeft: 8,
                    padding: "2px 8px",
                    borderRadius: 12,
                    fontSize: "0.75rem",
                    color: "white",
                    minWidth: 140,
                    display: "inline-flex",
                    justifyContent: "center",
                    alignItems: "center",
                    background:
                      gameState.phase === "WORK"
                        ? gameState.me.finished_phase
                          ? "#2e7d32"
                          : "#6c757d"
                        : "#444",
                    opacity: gameState.phase === "WORK" ? 1 : 0,
                    transition: "opacity 0.2s ease, background 0.2s ease",
                    pointerEvents: "none"
                  }}
                >
                  {gameState.phase === "WORK"
                    ? gameState.me.health === "healthy"
                      ? gameState.me.finished_phase
                        ? "Action Locked In ✓"
                        : "! Action Available !"
                      : "No Action Available"
                    : ""}
                </span>
              </h2>

              <div style={{ fontSize: "1.3rem" }}>
                <strong>Day {gameState.day}</strong>
                {" | "}
                <InfoTooltip infoText={getPhaseTooltip(gameState.phase)}>
                  <span style={{ textDecoration: "underline", fontWeight: 600, cursor: "help", color: "white" }}>
                    Phase: {gameState.phase}
                  </span>
                </InfoTooltip>
                {" | "}
                Time:{" "}

                <span
                  style={{
                    color: timeLeft <= 20 ? "#8d1216" : "inherit",
                    fontWeight: timeLeft <= 20 ? "bold" : "normal",
                    transition: "color 0.3s ease"
                  }}
                >
                  {timeLeft}s
                </span>
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

                {/* LEFT: Small End Phase Sidebar */}
                <div
                  style={{
                    display: "flex",
                    gap: "12px",
                    position: "sticky",
                    top: "20px",
                    width: "100%",
                    alignItems: "flex-start"
                  }}
                >
                  <div
                    className="card"
                    style={{
                      backgroundColor: "var(--medium_honey)",
                      flex: 1,
                      minWidth: 0,
                      boxSizing: "border-box",
                      overflow: "hidden"
                    }}
                  >
                    <h3 style={{ marginTop: 0 }}>Village Map</h3>

                    <VillageMap
                      mapData={gameState.map}
                      playerId={userId}
                      development_costs={gameState.development_costs}
                      onBuild={(tileId) =>
                        presenter.buildDevelopment(tileId)
                      }
                    />
                  </div>
                </div>

              </div>

              {/* RIGHT COLUMN: Roster & Social Chat */}
              {/* minWidth: 0 prevents the chat from blowing out the grid horizontally */}
              <div style={{ display: "flex", flexDirection: "column", gap: "20px", minWidth: 0 }}>
                <PlayerRoster />
                <TabbedCommunicator
                  messages={messages}
                  playerId={userId}
                  players={gameState.player_list}
                  onSend={(content: string, toId: string) => presenter.sendChat(content, toId)}
                />

                {!gameState.me.finished_phase ? (
                  <div
                    className="card card-finish_phase"
                    style={{
                      color: "white",
                      textAlign: "center",
                      padding: "12px",
                      boxSizing: "border-box"
                    }}
                  >
                    <button
                      className="btn"
                      style={{
                        width: "100%",
                        fontSize: "0.9rem",
                        padding: "10px",
                        boxSizing: "border-box"
                      }}
                      onClick={() => presenter.finishPhase()}
                    >
                      {gameState.phase === "NIGHT"
                        ? "End Day"
                        : "End Phase"}
                    </button>
                  </div>
                ) : (
                  <div
                    className="card card-waiting"
                    style={{
                      textAlign: "center",
                      fontSize: "0.9rem",
                      padding: "12px",
                      flex: "0 0 220px",
                      boxSizing: "border-box",
                    }}
                  >
                    Waiting For Others
                  </div>
                )}

              </div>
            </div>

          </PlayerProvider>
        </PlayerColorProvider>
      </GameStateProvider>
    </div >
  );
};

export default Gameplay;
