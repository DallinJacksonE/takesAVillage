import React, { useState } from "react";
import { MessageDTO, DevelopmentDTO, PlayerDTO } from "../../../dtos/index";

type MessageType = "TEXT" | "TRADE" | "EMPLOYMENT";

interface Props {
  phase: "WORK" | "TRADE" | "NIGHT";
  playerId: string;
  myDevelopments: DevelopmentDTO[];
  myResources: { wood: number; food: number; iron: number };
  players: PlayerDTO[];
  onSend: (payload: Partial<MessageDTO>) => void;
}

const MessageComposer: React.FC<Props> = ({
  phase,
  playerId,
  myDevelopments,
  myResources,
  players,
  onSend,
}) => {
  // Compose State
  const [toId, setToId] = useState("");
  const [type, setType] = useState<MessageType>("TEXT");
  const [content, setContent] = useState("");

  // Compose: Trade/Job Defaults
  const [offerAmount, setOfferAmount] = useState(1);
  const [offerType, setOfferType] = useState("food");
  const [gainAmount, setGainAmount] = useState(1);
  const [gainType, setGainType] = useState("wood");
  const [wageOffer, setWageOffer] = useState(1);
  const [wageType, setWageType] = useState("wood");
  const [devId, setDevId] = useState("");

  const isWageExceeding =
    type === "EMPLOYMENT" &&
    wageOffer > (myResources[wageType as keyof typeof myResources] || 0);

  const handleComposeSend = () => {
    if (!toId) return alert("Select a recipient");

    const payload: Partial<MessageDTO> = {
      to_id: toId,
      from_id: playerId,
      type: type,
    };

    if (type === "TEXT") {
      payload.content = content;
    } else if (type === "EMPLOYMENT") {
      payload.wage_offer = parseInt(String(wageOffer));
      payload.wage_type = wageType;
      payload.dev_id = devId;
    } else if (type === "TRADE") {
      payload.offer_items = { [offerType]: parseInt(String(offerAmount)) };
      payload.request_items = { [gainType]: parseInt(String(gainAmount)) };
    }

    onSend(payload);
    setContent("");
    setOfferAmount(1);
    setOfferType("food");
    setGainAmount(1);
    setGainType("wood");
    setWageOffer(1);
    setWageType("wood");
    setDevId("");
  };

  return (
    <div
      style={{
        borderTop: "2px solid #eee",
        padding: "10px 0 0 0",
        marginTop: "10px",
      }}
    >
      <div style={{ display: "flex", gap: "5px", marginBottom: "8px" }}>
        <select
          style={{ flex: 1 }}
          value={toId}
          onChange={(e) => setToId(e.target.value)}
        >
          <option value="">To Player...</option>
          {players.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <select
          value={type}
          onChange={(e) => setType(e.target.value as MessageType)}
        >
          <option value="TEXT">Chat</option>
          {phase === "WORK" && <option value="EMPLOYMENT">Job Offer</option>}
          {phase === "TRADE" && <option value="TRADE">Trade</option>}
        </select>
      </div>

      <div style={{ display: "flex", gap: "5px", alignItems: "center" }}>
        {type === "TEXT" && (
          <input
            style={{ flex: 1 }}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Message..."
          />
        )}

        {type === "EMPLOYMENT" && (
          <>
            <input
              type="number"
              style={{ width: "70px" }}
              value={wageOffer}
              onChange={(e) => setWageOffer(Number(e.target.value))}
            />
            <select
              value={wageType}
              onChange={(e) => setWageType(e.target.value)}
            >
              <option value="food">Food</option>
              <option value="wood">Wood</option>
              <option value="iron">Iron</option>
            </select>
            <select
              style={{ flex: 1 }}
              value={devId}
              onChange={(e) => setDevId(e.target.value)}
            >
              <option value="">Site...</option>
              {myDevelopments.map((d, i) => (
                <option key={i} value={d.id}>
                  {d.type} ({d.level})
                </option>
              ))}
            </select>
          </>
        )}

        {type === "TRADE" && (
          <>
            <input
              type="number"
              style={{ width: "70px" }}
              value={offerAmount}
              onChange={(e) => setOfferAmount(Number(e.target.value))}
            />
            <select
              value={offerType}
              onChange={(e) => setOfferType(e.target.value)}
            >
              <option value="food">Food</option>
              <option value="wood">Wood</option>
              <option value="iron">Iron</option>
            </select>
            <span>for</span>
            <input
              type="number"
              style={{ width: "70px" }}
              value={gainAmount}
              onChange={(e) => setGainAmount(Number(e.target.value))}
            />
            <select
              value={gainType}
              onChange={(e) => setGainType(e.target.value)}
            >
              <option value="food">Food</option>
              <option value="wood">Wood</option>
              <option value="iron">Iron</option>
            </select>
          </>
        )}

        <button
          className="btn"
          onClick={handleComposeSend}
          disabled={isWageExceeding}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default MessageComposer;
