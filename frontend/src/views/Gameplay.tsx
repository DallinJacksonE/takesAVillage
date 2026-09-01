import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import VillageMap from "../components/gameplay/VillageMap";
import { GameStateDTO, ChatMessageDTO, Resource } from "../dtos";
import { PlayerProvider } from "../components/hooks/usePlayerName";
import {
  GameplayPresenter,
  GameplayView,
} from "../presenters/GameplayPresenter";
import { ConnectionState, GameNotification } from "../service/GameplayService";
import InfoTooltip from "../components/InfoTooltip"
import PlayerStatusCard from "../components/gameplay/playerInfo/PlayerStatusCard";
import DevelopmentsCard from "../components/gameplay/DevelopmentsCard";
import AvailableWorkCard from "../components/gameplay/AvailableWorkCard";
import PlayerRoster from "../components/gameplay/playerInfo/PlayerRoster";
import TradeDesk from "../components/gameplay/trading/TradeDesk";
import TabbedCommunicator from "../components/gameplay/communication/TabbedCommunicator";
import CampfireRing from "../components/gameplay/CampfireRing";
import { PlayerColorProvider } from "../components/hooks/usePlayerColor";
import PlayerInfo from "../components/gameplay/playerInfo/PlayerInfo";
import { GameStateProvider } from "../components/hooks/useGameState";
import styles from "./Gameplay.module.css";
import PlayerSprite from "../components/gameplay/player/PlayerSprite";
import { getGoblinSpriteForAnimation } from "../components/gameplay/player/playerSpriteCatalog";
import GameplayShell from "../components/gameplay/layout/GameplayShell";
import PlayerStatusBar from "../components/gameplay/layout/PlayerStatusBar";
import ConnectionBanner from "../components/gameplay/layout/ConnectionBanner";
import ToastStack from "../components/gameplay/layout/ToastStack";
import NightTransitionAcknowledger from "../components/gameplay/NightTransitionAcknowledger";
import { buildPhaseAttentionKey } from "../components/gameplay/layout/phaseAttention";


const Gameplay: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const presenterRef =
    React.useRef<GameplayPresenter | null>(null);
  const [gameState, setGameState] = useState<GameStateDTO | null>(null);
  const [playerCount, setPlayerCount] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [userId, setUserId] = useState("");
  const [messages, setMessages] = useState<ChatMessageDTO[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>("CONNECTING");
  const [toasts, setToasts] = useState<Array<GameNotification & { id: number }>>([]);

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
      showToast: (notification: GameNotification) => {
        const id = Date.now();
        setToasts(prev => [...prev, { ...notification, id }]);
        window.setTimeout(() => {
          setToasts(prev => prev.filter(toast => toast.id !== id));
        }, 5000);
      },
      setChatHistory: setMessages,
      addChatMessage: (msg: ChatMessageDTO) =>
        setMessages(prev => [...prev, msg]),

      // NEW: Wire the connection state to the UI
      setConnectionState,
    };

    const presenter = new GameplayPresenter(view, gameId);
    presenterRef.current = presenter;

    return () => {
      presenter.destroy();
      presenterRef.current = null;
    };
  }, [gameId]);

  const presenter = presenterRef.current;

  if (!gameState || !presenter) {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <ConnectionBanner state={connectionState} />
        <ToastStack toasts={toasts} />
        <h2>Loading Village...</h2>
      </div>
    );
  }

  if (gameState.status === "WAITING") {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <ConnectionBanner state={connectionState} />
        <ToastStack toasts={toasts} />
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
        <ToastStack toasts={toasts} />
        <h2>Game Over: Village {gameId}</h2>
        <p>Thank you for playing</p>
      </div>
    );
  }

  const isDead = gameState.me.health === "dead";

  if (isDead) {
    return (
      <div className="observation-screen">
        <ToastStack toasts={toasts} />
        <NightTransitionAcknowledger
          state={gameState}
          onComplete={presenter.acknowledgeNightAnimation}
        />
        <GameStateProvider gameState={gameState}>
          <PlayerProvider players={gameState.player_list}>
            <h2>You have perished.</h2>
            <p>You are now observing the village.</p>
            <PlayerRoster />
            <VillageMap
              mapData={gameState.map}
              phase={gameState.phase}
              playerId={userId}
              players={gameState.player_list}
              development_costs={gameState.development_costs}
              maxFireSeats={gameState.max_fire_seats}
              onBuild={(tileId) => presenter.buildDevelopment(tileId)}
            />

          </PlayerProvider>
        </GameStateProvider>
      </div>
    );
  }

  const myVisualState = gameState.player_list.find(
    (player) => player.id === gameState.me.id,
  )?.visual_state ?? { animation: "IDLE" as const, location: { kind: "HOME" as const } };
  const statusSprite = getGoblinSpriteForAnimation(myVisualState.animation);

  const acceptedActionIds = gameState.me.actions
    .filter(a => a.status === "ACCEPTED" && (a.type === "EMPLOYMENT" || a.type === "TRADE" || a.type === "BARTER"))
    .map(a => a.id)
    .join(",");

  return (
    <div className={styles.gameplayPage}>
      <ConnectionBanner state={connectionState} />
      <ToastStack toasts={toasts} />
      <NightTransitionAcknowledger
        state={gameState}
        onComplete={presenter.acknowledgeNightAnimation}
      />
      <GameStateProvider gameState={gameState}>
        <PlayerColorProvider gameState={gameState}>
          <PlayerProvider players={gameState.player_list}>
            <GameplayShell
              actionAttentionKey={buildPhaseAttentionKey(gameState)}
              autoOpenActionsKey={acceptedActionIds}
              statusBar={(
                <PlayerStatusBar
                  day={gameState.day}
                  phase={gameState.phase}
                  playerName={gameState.me.name}
                  timeLeft={timeLeft}
                  sprite={(
                    <PlayerSprite
                      {...statusSprite}
                      animation={myVisualState.animation}
                      alt={`${gameState.me.name} goblin`}
                      scale={1}
                    />
                  )}
                />
              )}
              map={(
                <VillageMap
                  mapData={gameState.map}
                  phase={gameState.phase}
                  playerId={userId}
                  players={gameState.player_list}
                  development_costs={gameState.development_costs}
                  maxFireSeats={gameState.max_fire_seats}
                  onBuild={(tileId) => presenter.buildDevelopment(tileId)}
                  onReact={presenter.setEmoji}
                  onMaintain={(devId) => presenter.maintainDevelopment(devId)}
                  onUpgrade={(devId) => presenter.upgradeDevelopment(devId)}
                  onContest={(devId, side) => presenter.contestDevelopment(devId, side as "INITIATOR" | "CONTESTER" | "OWNER")}
                  onApplyForJob={(targetId, devId, wage, wageType) => presenter.draftEmployment(targetId, devId, wage, wageType as Resource, true)}
                  onDraftTrade={(targetId, offer, req) => presenter.draftTrade(targetId, offer, req)}
                  onRequestSeat={(targetId) => presenter.draftCampfire(targetId, true)}
                  onOfferSeat={(targetId) => presenter.draftCampfire(targetId, false)}
                  myActions={gameState.me.actions}
                  onAcceptApplicant={(actionId) => presenter.acceptContract(actionId, "EMPLOYMENT")}
                  onDenyApplicant={(actionId) => presenter.denyContract(actionId, "EMPLOYMENT")}
                />
              )}
              actionPanel={(
                <div className={styles.panelStack}>
                  <div className={styles.phaseHeading}>
                    <h2>{gameState.phase} phase</h2>
                    <InfoTooltip infoText={getPhaseTooltip(gameState.phase)} />
                  </div>
                  <PlayerStatusCard />
                  {gameState.phase === "WORK" && (
                    <>
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
                    </>
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
                  {!gameState.me.finished_phase ? (
                    <div className={`card ${styles.finishPhaseCard}`}>
                      <button className={`btn ${styles.finishPhaseButton}`} onClick={() => presenter.finishPhase()}>
                        {gameState.phase === "NIGHT" ? "End Day" : "End Phase"}
                      </button>
                    </div>
                  ) : (
                    <div className={`card ${styles.waitingCard}`}>Waiting...</div>
                  )}
                </div>
              )}
              chatPanel={(
                <div className={`${styles.panelStack} ${styles.chatStack}`}>
                  <TabbedCommunicator
                    messages={messages}
                    playerId={gameState.me.id}
                    players={gameState.player_list}
                    chats={gameState.chats ?? []}
                    onSend={presenter.sendChat}
                    onCreateChat={(name, memberIds) => presenter.createChat(name, memberIds)}
                  />
                </div>
              )}
            />
          </PlayerProvider>
        </PlayerColorProvider>
      </GameStateProvider>
    </div >
  );
};

export default Gameplay;
