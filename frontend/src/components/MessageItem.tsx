import React from "react";
import { MessageDTO } from "../../../dtos/index";
import ChatMessage from "./MessageTypes/ChatMessage";
import JobOfferMessage from "./MessageTypes/JobOfferMessage";
import TradeMessage from "./MessageTypes/TradeMessage";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
	msg: MessageDTO;
	playerId: string;
	isEditing: boolean;
	barterValues: Partial<MessageDTO>;
	setBarterValues: (values: Partial<MessageDTO>) => void;
	onSend: (payload: Partial<MessageDTO> & { action?: string }) => void;
	onBarterStart: (msg: MessageDTO) => void;
	onSendUpdate: () => void;
	onCancelEdit: () => void;
}

const MessageItem: React.FC<Props> = ({
	msg,
	playerId,
	isEditing,
	barterValues,
	setBarterValues,
	onSend,
	onBarterStart,
	onSendUpdate,
	onCancelEdit,
}) => {
	const getPlayerName = usePlayerName();
	const isMe = msg.from_id === playerId;
	const isReceivedCounterOffer = msg.bartered && msg.to_id === playerId;

	const showActions =
		msg.type !== "TEXT" &&
		!isEditing &&
		msg.to_id === playerId &&
		(msg.status === "PENDING" || msg.bartered);

	if (msg.is_system) {
		return (
			<div
				key={msg.id}
				style={{
					textAlign: "center",
					fontStyle: "italic",
					color: "#666",
					margin: "5px 0",
					fontSize: "0.8rem",
				}}
			>
				{msg.content}
			</div>
		);
	}

	return (
		<div
			key={msg.id}
			className='message-card'
			style={{
				border: isEditing
					? "2px solid #2196F3"
					: isReceivedCounterOffer
						? "2px solid #FFC107"
						: "1px solid #ddd",
				padding: "10px",
				marginBottom: "8px",
				borderRadius: "6px",
				background: "#fff",
				boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
			}}
		>
			<div
				style={{
					display: "flex",
					justifyContent: "space-between",
					fontSize: "0.75rem",
					marginBottom: "8px",
					color: "#555",
				}}
			>
				<span style={{ fontWeight: "bold" }}>
					{isMe
						? `To: ${getPlayerName(msg.to_id)}`
						: `From: ${getPlayerName(msg.from_id)}`}
				</span>
				<span
					style={{
						background:
							msg.status === "ACCEPTED"
								? "#e8f5e9"
								: msg.status === "DENIED"
									? "#ffebee"
									: msg.bartered
										? "#fff3e0"
										: "#e3f2fd",
						padding: "2px 6px",
						borderRadius: "4px",
						textTransform: "uppercase",
						fontSize: "0.7rem",
					}}
				>
					{msg.status}
				</span>
			</div>

			<div style={{ padding: "5px 0", fontSize: "0.9rem" }}>
				{isEditing ? (
					<div
						style={{
							background: "#f5f5f5",
							padding: "10px",
							borderRadius: "4px",
						}}
					>
						{msg.type === "EMPLOYMENT" && (
							<JobOfferMessage
								msg={msg}
								isEditing={isEditing}
								barterValues={barterValues}
								setBarterValues={setBarterValues}
							/>
						)}
						{msg.type === "TRADE" && (
							<TradeMessage
								msg={msg}
								isEditing={isEditing}
								barterValues={barterValues}
								setBarterValues={setBarterValues}
							/>
						)}
					</div>
				) : (
					<div>
						{msg.type === "TEXT" && <ChatMessage msg={msg} />}
						{msg.type === "EMPLOYMENT" && (
							<JobOfferMessage
								msg={msg}
								isEditing={isEditing}
								barterValues={barterValues}
								setBarterValues={setBarterValues}
							/>
						)}
						{msg.type === "TRADE" && (
							<TradeMessage
								msg={msg}
								isEditing={isEditing}
								barterValues={barterValues}
								setBarterValues={setBarterValues}
							/>
						)}
					</div>
				)}
			</div>

			<div
				style={{
					display: "flex",
					justifyContent: "flex-end",
					gap: "8px",
					marginTop: "8px",
				}}
			>
				{showActions && (
					<>
						<button
							className='btn-sm success'
							onClick={() => onSend({ id: msg.id, action: "ACCEPT" })}
						>
							Accept
						</button>
						<button
							className='btn-sm warning'
							onClick={() => onBarterStart(msg)}
						>
							Counter Offer
						</button>
						<button
							className='btn-sm danger'
							onClick={() => onSend({ id: msg.id, action: "DENY" })}
						>
							Deny
						</button>
					</>
				)}
				{isEditing && (
					<>
						<button className='btn-sm success' onClick={onSendUpdate}>
							Send Offer
						</button>
						<button className='btn-sm' onClick={onCancelEdit}>
							Cancel
						</button>
					</>
				)}
			</div>
		</div>
	);
};

export default MessageItem;
