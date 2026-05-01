import React, { useState } from "react";
import {
  MessageDTO,
  DevelopmentDTO,
  PlayerDTO,
  TradeMessageDTO,
  EmploymentMessageDTO,
} from "../../../dtos/index";
import MessageItem from "./MessageItem";
import MessageComposer from "./MessageComposer";

export interface BarterDraft {
  to_id?: string;
  from_id?: string;
  wage_offer?: number;
  wage_type?: string;
  offer_items?: Record<string, number>;
  request_items?: Record<string, number>;
  [key: string]: any;
}

export interface MessageBoardProps {
  phase: "WORK" | "TRADE" | "NIGHT";
  messages: MessageDTO[];
  playerId: string;
  myDevelopments: DevelopmentDTO[];
  myResources: { wood: number; food: number; iron: number };
  players: PlayerDTO[];
  onSend: (payload: Record<string, any>) => void;
}

const MessageBoard: React.FC<MessageBoardProps> = ({
  phase,
  messages,
  playerId,
  myDevelopments,
  myResources,
  players,
  onSend,
}) => {
  const [editingMsgId, setEditingMsgId] = useState<string | null>(null);
  const [barterValues, setBarterValues] = useState<BarterDraft>({});

  const handleBarterStart = (msg: MessageDTO) => {
    setEditingMsgId(msg.id);
    if (msg.type === "EMPLOYMENT") {
      const empMsg = msg as EmploymentMessageDTO;
      setBarterValues({
        wage_offer: empMsg.wage_offer,
        wage_type: empMsg.wage_type,
      });
    } else if (msg.type === "TRADE") {
      const tradeMsg = msg as TradeMessageDTO;
      setBarterValues({
        offer_items: tradeMsg.offer_items,
        request_items: tradeMsg.request_items,
      });
    }
  };

  const handleSendUpdate = () => {
    if (!editingMsgId) return;

    const payload: Record<string, any> = {
      id: editingMsgId,
      action: "BARTER",
      ...barterValues,
    };

    onSend(payload);
    setEditingMsgId(null);
  };

  return (
    <div
      className="card"
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
              myResources={myResources}
              isEditing={editingMsgId === msg.id}
              barterValues={barterValues}
              setBarterValues={setBarterValues}
              onSend={onSend}
              onBarterStart={handleBarterStart}
              onSendUpdate={handleSendUpdate}
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
        myResources={myResources}
        players={players}
        onSend={onSend}
      />
    </div>
  );
};

export default MessageBoard;
