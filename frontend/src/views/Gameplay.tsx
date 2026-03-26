import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import StatusCards from "../components/StatusCards";
import VillageMap from "../components/VillageMap";
import MessageBoard from "../components/MessageBoard";
import { GameStateDTO, MessageDTO } from "../../../dtos";
import { PlayerProvider } from "../components/hooks/usePlayerName";
import {
	GameplayPresenter,
	GameplayView,
} from "../presenters/GameplayPresenter";

const Gameplay: React.FC = () => {
	const { gameId } = useParams<{ gameId: string }>();
	const [presenter, setPresenter] = useState<GameplayPresenter | null>(null);
	const [gameState, setGameState] = useState<GameStateDTO | null>(null);
	const [playerCount, setPlayerCount] = useState(0);
	const [timeLeft, setTimeLeft] = useState(0);
	const [userId, setUserId] = useState("");
	const [editingMsgId, setEditingMsgId] = useState<string | null>(null);
	const [barterValues, setBarterValues] = useState<Partial<MessageDTO>>({});

	useEffect(() => {
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

	const handleBarterStart = (msg: MessageDTO) => {
		setEditingMsgId(msg.id);
		if (msg.type === "EMPLOYMENT") {
			setBarterValues({
				wage_offer: msg.wage_offer,
				wage_type: msg.wage_type,
			});
		} else if (msg.type === "TRADE") {
			setBarterValues({
				offer_items: msg.offer_items,
				request_items: msg.request_items,
			});
		}
	};

	const handleSendUpdate = () => {
		if (!editingMsgId || !presenter) return;

		const payload: Partial<MessageDTO> & { action: string } = {
			id: editingMsgId,
			action: "BARTER",
			...barterValues,
		};

		presenter.handleSendMessage(payload);
		setEditingMsgId(null);
	};

	if (!presenter || !gameState) return <div>Connecting...</div>;

	if (gameState.status === "WAITING") {
		return (
			<div
				className='container'
				style={{ textAlign: "center", marginTop: "50px" }}
			>
				<h1>Waiting for Players...</h1>
				<h2>Game ID: {gameId}</h2>
				<p>Players: {playerCount}</p>
				{gameState.is_host && (
					<button className='btn' onClick={() => presenter.handleStartGame()}>
						Start Game
					</button>
				)}
			</div>
		);
	}

	const { day, phase } = gameState;

	return (
		<div className='container'>
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

			<div style={{ display: "flex", gap: "20px", marginBottom: "20px" }}>
				<StatusCards
					state={gameState}
					map={gameState.map}
					onAction={(action, payload) =>
						presenter.handleUserAction(action, payload)
					}
				/>
			</div>

			<PlayerProvider players={gameState.player_list || []}>
				<MessageBoard
					phase={phase}
					messages={gameState.messages || []}
					playerId={userId}
					myDevelopments={gameState.me.developments || []}
					onSend={(payload) => presenter.handleSendMessage(payload)}
					editingMsgId={editingMsgId}
					setEditingMsgId={setEditingMsgId}
					barterValues={barterValues}
					setBarterValues={setBarterValues}
					onBarterStart={handleBarterStart}
					onSendUpdate={handleSendUpdate}
				/>
			</PlayerProvider>

			{phase === "TRADE" && (
				<>
					{!gameState.me.finished_phase ? (
						<div
							className='card'
							style={{
								background: "#D4ECD6",
								textAlign: "center",
								margin: "20px 0",
							}}
						>
							<button
								className='btn'
								onClick={() => presenter.handleUserAction("FINISH_PHASE", {})}
							>
								Finish Trading
							</button>
						</div>
					) : (
						<div
							className='card'
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
							className='card'
							style={{
								background: "#333",
								color: "white",
								textAlign: "center",
								margin: "20px 0",
							}}
						>
							<button
								className='btn'
								onClick={() => presenter.handleUserAction("FINISH_PHASE", {})}
							>
								End Day
							</button>
						</div>
					) : (
						<div
							className='card'
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
		</div>
	);
};

export default Gameplay;
