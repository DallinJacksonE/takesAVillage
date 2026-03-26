import React, { useState } from "react";
import { MessageDTO, DevelopmentDTO, PlayerDTO } from "../../../dtos/index";
import MessageItem from "./MessageItem";
import MessageComposer from "./MessageComposer";

export interface MessageBoardProps {
	phase: "WORK" | "TRADE" | "NIGHT";
	messages: MessageDTO[];
	playerId: string;
	myDevelopments: DevelopmentDTO[];
	onSend: (payload: Partial<MessageDTO> & { action?: string }) => void;
	setEditingMsgId: (id: string | null) => void;
	editingMsgId: string | null;
	barterValues: Partial<MessageDTO>;
	setBarterValues: (values: Partial<MessageDTO>) => void;
	onBarterStart: (msg: MessageDTO) => void;
	onSendUpdate: () => void;
}

const MessageBoard: React.FC<MessageBoardProps> = ({
	phase,
	messages,
	playerId,
	myDevelopments,
	onSend,
	editingMsgId,
	setEditingMsgId,
	barterValues,
	setBarterValues,
	onBarterStart,
	onSendUpdate,
}) => {
	return (
		<div
			className='card'
			style={{
				height: "550px",
				display: "flex",
				flexDirection: "column",
			}}
		>
			<h3
				style={{
					borderBottom: "1px solid #eee",
					paddingBottom: "10px",
					margin: "0 0 10px 0",
				}}
			>
				Communications
			</h3>

			<div
				style={{
					flex: 1,
					overflowY: "auto",
					background: "#fafafa",
					padding: "10px",
					borderRadius: "4px",
					border: "1px solid #eee",
				}}
			>
				{messages?.length > 0 ? (
					messages.map((msg) => (
						<MessageItem
							key={msg.id}
							msg={msg}
							playerId={playerId}
							isEditing={editingMsgId === msg.id}
							barterValues={barterValues}
							setBarterValues={setBarterValues}
							onSend={onSend}
							onBarterStart={onBarterStart}
							onSendUpdate={onSendUpdate}
							onCancelEdit={() => setEditingMsgId(null)}
						/>
					))
				) : (
					<p style={{ textAlign: "center", color: "#999" }}>No messages.</p>
				)}
			</div>

			<MessageComposer
				phase={phase}
				playerId={playerId}
				myDevelopments={myDevelopments}
				onSend={onSend}
			/>
		</div>
	);
};

export default MessageBoard;
