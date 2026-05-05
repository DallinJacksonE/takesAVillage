import React, { useState } from "react";
import { GameStateDTO, TradeMessageDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onSend: (payload: Record<string, any>) => void;
}

const TradeDesk: React.FC<Props> = ({ state, onSend }) => {
  const { me, messages, player_list } = state;
  const getPlayerName = usePlayerName();

  // State for drafting a new trade
  const [draftingWith, setDraftingWith] = useState<string | null>(null);
  const [offerAmount, setOfferAmount] = useState(1);
  const [offerType, setOfferType] = useState("food");
  const [requestAmount, setRequestAmount] = useState(1);
  const [requestType, setRequestType] = useState("wood");

  // State for drafting a counter-offer
  const [counteringMsgId, setCounteringMsgId] = useState<string | null>(null);
  const [counterOfferAmount, setCounterOfferAmount] = useState(1);
  const [counterOfferType, setCounterOfferType] = useState("food");
  const [counterRequestAmount, setCounterRequestAmount] = useState(1);
  const [counterRequestType, setCounterRequestType] = useState("wood");

  // Filter out trades from the message list
  const tradeMessages = (messages || []).filter((m) => m.type === "TRADE") as TradeMessageDTO[];

  const needsAttention = tradeMessages.filter(
    (m) => (m.status === "PENDING" || m.status === "BARTERING") && m.pending_action_from === me.id
  );

  const waitingOnThem = tradeMessages.filter(
    (m) => (m.status === "PENDING" || m.status === "BARTERING") && m.pending_action_from !== me.id
  );

  const handleSendDraft = () => {
    if (!draftingWith) return;
    onSend({
      to_id: draftingWith,
      from_id: me.id,
      type: "TRADE",
      offer_items: { [offerType]: offerAmount },
      request_items: { [requestType]: requestAmount },
    });
    setDraftingWith(null); // Close draft box after sending
  };

  const handleStartCounter = (msg: TradeMessageDTO) => {
    const isSender = msg.from_id === me.id;
    // Pre-fill the counter offer with what the other player originally requested/offered
    const theirOffer = isSender ? msg.request_items : msg.offer_items;
    const theirRequest = isSender ? msg.offer_items : msg.request_items;

    const oType = Object.keys(theirRequest || {})[0] || "food";
    const oAmt = (theirRequest || {})[oType] || 1;
    const rType = Object.keys(theirOffer || {})[0] || "wood";
    const rAmt = (theirOffer || {})[rType] || 1;

    setCounterOfferType(oType);
    setCounterOfferAmount(oAmt);
    setCounterRequestType(rType);
    setCounterRequestAmount(rAmt);

    setCounteringMsgId(msg.id);
  };

  const handleSendCounter = (msgId: string) => {
    onSend({
      id: msgId,
      action: "BARTER",
      offer_items: { [counterOfferType]: counterOfferAmount },
      request_items: { [counterRequestType]: counterRequestAmount }
    });
    setCounteringMsgId(null);
  };

  // Helper to visually render the trade: [ 2 Food ] ➔ [ 1 Wood ]
  const renderTradeVisual = (offer: Record<string, number>, request: Record<string, number>) => {
    const oType = Object.keys(offer)[0] || "food";
    const oAmt = offer[oType] || 0;
    const rType = Object.keys(request)[0] || "wood";
    const rAmt = request[rType] || 0;

    return (
      <div style={{ display: "flex", alignItems: "center", gap: "10px", fontWeight: "bold" }}>
        <span style={{ background: "#e8f5e9", padding: "4px 8px", borderRadius: "4px", border: "1px solid #c8e6c9" }}>
          {oAmt} {oType}
        </span>
        <span style={{ color: "#888" }}>➔</span>
        <span style={{ background: "#e3f2fd", padding: "4px 8px", borderRadius: "4px", border: "1px solid #bbdefb" }}>
          {rAmt} {rType}
        </span>
      </div>
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", height: "100%" }}>

      {/* TOP ROW: Initiate New Trades */}
      <div className="card" style={{ margin: 0 }}>
        <h3 style={{ marginTop: 0 }}>The Trading Post</h3>
        <p style={{ fontSize: "0.8rem", color: "#666" }}>Select a villager to propose a trade</p>

        <div style={{ display: "flex", gap: "10px", overflowX: "auto", paddingBottom: "10px" }}>
          {player_list?.filter(p => p.id !== me.id).map((player) => (
            <button
              key={player.id}
              className="btn-sm"
              style={{ background: draftingWith === player.id ? "#2196F3" : "#f0f0f0", color: draftingWith === player.id ? "white" : "#333" }}
              onClick={() => setDraftingWith(draftingWith === player.id ? null : player.id)}
            >
              {player.name}
            </button>
          ))}
        </div>

        {/* DRAFTING BOX */}
        {draftingWith && (
          <div style={{ marginTop: "15px", padding: "15px", background: "#f9f9f9", borderRadius: "6px", border: "2px solid #2196F3" }}>
            <h4 style={{ margin: "0 0 10px 0" }}>Drafting Trade with {getPlayerName(draftingWith)}</h4>
            <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
              <span>I will give:</span>
              <input type="number" min="1" style={{ width: "50px" }} value={offerAmount} onChange={(e) => setOfferAmount(Number(e.target.value))} />
              <select value={offerType} onChange={(e) => setOfferType(e.target.value)}>
                <option value="food">Food</option>
                <option value="wood">Wood</option>
                <option value="iron">Iron</option>
              </select>

              <span>for their:</span>
              <input type="number" min="1" style={{ width: "50px" }} value={requestAmount} onChange={(e) => setRequestAmount(Number(e.target.value))} />
              <select value={requestType} onChange={(e) => setRequestType(e.target.value)}>
                <option value="food">Food</option>
                <option value="wood">Wood</option>
                <option value="iron">Iron</option>
              </select>

              <button className="btn success" onClick={handleSendDraft}>Send Offer</button>
            </div>
          </div>
        )}
      </div>

      {/* DASHBOARD COLUMNS */}
      <div style={{ display: "flex", gap: "20px", flex: 1 }}>

        {/* LEFT COLUMN: Needs Attention */}
        <div className="card" style={{ flex: 1, margin: 0, overflowY: "auto", borderTop: "4px solid #FF9800" }}>
          <h3 style={{ marginTop: 0 }}>Needs Your Attention</h3>
          {needsAttention.length === 0 ? (
            <p style={{ color: "#888", fontStyle: "italic", fontSize: "0.85rem" }}>All caught up!</p>
          ) : (
            needsAttention.map(msg => {
              const isSender = msg.from_id === me.id;
              const give = isSender ? msg.offer_items : msg.request_items;
              const receive = isSender ? msg.request_items : msg.offer_items;
              const otherPersonId = isSender ? msg.to_id : msg.from_id;

              return (
                <div key={msg.id} style={{ background: "#fff", padding: "10px", marginBottom: "10px", borderRadius: "6px", border: "1px solid #ddd", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
                  <div style={{ fontSize: "0.8rem", color: "#666", marginBottom: "5px" }}>
                    From <strong>{getPlayerName(otherPersonId)}</strong>
                  </div>
                  {renderTradeVisual(give || {}, receive || {})}

                  {/* Action Buttons OR Counter Input */}
                  {counteringMsgId === msg.id ? (
                    <div style={{ marginTop: "10px", padding: "10px", background: "#fff3e0", borderRadius: "4px", border: "1px solid #ffcc80" }}>
                      <div style={{ display: "flex", gap: "5px", alignItems: "center", flexWrap: "wrap", fontSize: "0.85rem" }}>
                        <span>Give:</span>
                        <input type="number" min="1" style={{ width: "40px", padding: "2px" }} value={counterOfferAmount} onChange={(e) => setCounterOfferAmount(Number(e.target.value))} />
                        <select style={{ padding: "2px" }} value={counterOfferType} onChange={(e) => setCounterOfferType(e.target.value)}>
                          <option value="food">Food</option>
                          <option value="wood">Wood</option>
                          <option value="iron">Iron</option>
                        </select>
                        <span>for:</span>
                        <input type="number" min="1" style={{ width: "40px", padding: "2px" }} value={counterRequestAmount} onChange={(e) => setCounterRequestAmount(Number(e.target.value))} />
                        <select style={{ padding: "2px" }} value={counterRequestType} onChange={(e) => setCounterRequestType(e.target.value)}>
                          <option value="food">Food</option>
                          <option value="wood">Wood</option>
                          <option value="iron">Iron</option>
                        </select>
                      </div>
                      <div style={{ display: "flex", gap: "5px", marginTop: "10px" }}>
                        <button className="btn-sm warning" onClick={() => handleSendCounter(msg.id)}>Send Counter</button>
                        <button className="btn-sm" onClick={() => setCounteringMsgId(null)}>Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: "flex", gap: "5px", marginTop: "10px" }}>
                      <button className="btn-sm success" onClick={() => onSend({ id: msg.id, action: "ACCEPT" })}>Accept</button>
                      <button className="btn-sm warning" onClick={() => handleStartCounter(msg)}>Counter</button>
                      <button className="btn-sm danger" onClick={() => onSend({ id: msg.id, action: "DENY" })}>Deny</button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* RIGHT COLUMN: Waiting on Them */}
        <div className="card" style={{ flex: 1, margin: 0, overflowY: "auto", borderTop: "4px solid #2196F3" }}>
          <h3 style={{ marginTop: 0 }}>Pending (Waiting on Them)</h3>
          {waitingOnThem.length === 0 ? (
            <p style={{ color: "#888", fontStyle: "italic", fontSize: "0.85rem" }}>No outgoing trades.</p>
          ) : (
            waitingOnThem.map(msg => {
              const isSender = msg.from_id === me.id;
              const give = isSender ? msg.offer_items : msg.request_items;
              const receive = isSender ? msg.request_items : msg.offer_items;
              const otherPersonId = isSender ? msg.to_id : msg.from_id;

              return (
                <div key={msg.id} style={{ background: "#fafafa", padding: "10px", marginBottom: "10px", borderRadius: "6px", border: "1px dashed #ccc" }}>
                  <div style={{ fontSize: "0.8rem", color: "#666", marginBottom: "5px" }}>
                    Sent to <strong>{getPlayerName(otherPersonId)}</strong>
                  </div>
                  {renderTradeVisual(give || {}, receive || {})}
                  <div style={{ fontSize: "0.75rem", color: "#888", marginTop: "8px", fontStyle: "italic" }}>
                    Awaiting response...
                  </div>
                </div>
              );
            })
          )}
        </div>

      </div>
    </div>
  );
};

export default TradeDesk;
