import React, { useState } from "react";
import { GameStateDTO, TradeActionDTO, Resource } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onSend: (payload: Record<string, any>) => void;
}

// Helper to neatly format resource bundles
const renderItems = (items?: Partial<Record<Resource, number>>) => {
  if (!items || Object.keys(items).length === 0) return "Nothing";
  return Object.entries(items)
    .filter(([_, val]) => (val as number) > 0)
    .map(([res, val]) => `${val} ${res}`)
    .join(", ") || "Nothing";
};

// --- SUB-COMPONENT: The Shipping Window ---
const ShippingWindow: React.FC<{ trade: TradeActionDTO; meId: string; onSend: Props["onSend"]; getPlayerName: (id: string) => string }> = ({ trade, meId, onSend, getPlayerName }) => {
  const isInitiator = meId === trade.initiator_id;
  const expectedToSend = isInitiator ? trade.offer_items : trade.request_items;
  const expectedToReceive = isInitiator ? trade.request_items : trade.offer_items;
  const otherPersonId = isInitiator ? trade.target_id : trade.initiator_id;
  const hasFinalized = isInitiator ? trade.initiator_finalized : trade.target_finalized;

  // Local state for what the player *actually* decides to send
  const [actualItems, setActualItems] = useState<Record<string, number>>(expectedToSend || {});

  const handleShip = () => {
    onSend({
      actionCommand: "FINALIZE",
      actionId: trade.id,
      actual_items: actualItems,
    });
  };

  if (hasFinalized) {
    return (
      <div style={{ background: "#e8f5e9", padding: "10px", borderRadius: "6px", marginBottom: "10px", border: "1px solid #a5d6a7" }}>
        <strong style={{ color: "#2e7d32" }}>Goods Shipped!</strong>
        <div style={{ fontSize: "0.85rem", marginTop: "5px" }}>Waiting for {getPlayerName(otherPersonId || "")} to send their goods...</div>
      </div>
    );
  }

  return (
    <div style={{ background: "#fff3e0", padding: "10px", borderRadius: "6px", marginBottom: "10px", border: "1px solid #ffcc80" }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <strong>Ship to {getPlayerName(otherPersonId || "")}</strong>
        <span style={{ fontSize: "0.8rem", color: "#666" }}>Expected from them: {renderItems(expectedToReceive)}</span>
      </div>

      <div style={{ fontSize: "0.85rem", color: "#555", marginTop: "5px" }}>Agreed to send: {renderItems(expectedToSend)}</div>

      <div style={{ display: "flex", gap: "10px", marginTop: "10px", alignItems: "center" }}>
        {["food", "wood", "iron"].map((res) => (
          <div key={res} style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <span style={{ fontSize: "0.8rem", textTransform: "capitalize" }}>{res}:</span>
            <input
              type="number"
              min="0"
              style={{ width: "40px", padding: "2px" }}
              value={actualItems[res] || 0}
              onChange={(e) => setActualItems({ ...actualItems, [res]: parseInt(e.target.value) || 0 })}
            />
          </div>
        ))}
        <button className="btn success" style={{ marginLeft: "auto", padding: "4px 10px" }} onClick={handleShip}>Ship Goods</button>
      </div>
    </div>
  );
};

// --- MAIN COMPONENT ---
const TradeDesk: React.FC<Props> = ({ state, onSend }) => {
  const { me, player_list } = state;
  const getPlayerName = usePlayerName();

  // Drafting State
  const [targetId, setTargetId] = useState<string>(player_list.find(p => p.id !== me.id)?.id || "");
  const [giveAmt, setGiveAmt] = useState(1);
  const [giveRes, setGiveRes] = useState<Resource>("food");
  const [reqAmt, setReqAmt] = useState(1);
  const [reqRes, setReqRes] = useState<Resource>("wood");

  // Filtering Actions
  const tradeActions = (me.actions || []).filter((a): a is TradeActionDTO => a.type === "TRADE");
  const pendingTrades = tradeActions.filter(t => t.status === "PENDING");
  const acceptedTrades = tradeActions.filter(t => t.status === "ACCEPTED");

  const handleDraftTrade = () => {
    if (!targetId) return;
    onSend({
      actionCommand: "TRADE",
      type: "TRADE",
      target_id: targetId,
      offer_items: { [giveRes]: giveAmt },
      request_items: { [reqRes]: reqAmt }
    });
  };

  return (
    <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column", gap: "20px" }}>
      <h3>Trade Desk</h3>

      {/* --- SECTION 1: DRAFT NEW TRADE --- */}
      <div style={{ background: "#f1f3f4", padding: "15px", borderRadius: "8px" }}>
        <strong>Propose a Trade</strong>
        <div style={{ display: "flex", gap: "10px", marginTop: "10px", alignItems: "center", flexWrap: "wrap" }}>
          <select value={targetId} onChange={e => setTargetId(e.target.value)} style={{ padding: "5px" }}>
            {player_list.filter(p => p.id !== me.id).map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <span>I give:</span>
          <input type="number" min="0" value={giveAmt} onChange={e => setGiveAmt(parseInt(e.target.value) || 0)} style={{ width: "40px" }} />
          <select value={giveRes} onChange={e => setGiveRes(e.target.value as Resource)}>
            <option value="food">Food</option>
            <option value="wood">Wood</option>
            <option value="iron">Iron</option>
          </select>
          <span>for:</span>
          <input type="number" min="0" value={reqAmt} onChange={e => setReqAmt(parseInt(e.target.value) || 0)} style={{ width: "40px" }} />
          <select value={reqRes} onChange={e => setReqRes(e.target.value as Resource)}>
            <option value="food">Food</option>
            <option value="wood">Wood</option>
            <option value="iron">Iron</option>
          </select>
          <button className="btn" style={{ background: "#2196F3", color: "white" }} onClick={handleDraftTrade}>Propose</button>
        </div>
      </div>

      {/* --- SECTION 2: BARTERING (PENDING) --- */}
      {pendingTrades.length > 0 && (
        <div>
          <strong style={{ color: "#1976d2", borderBottom: "2px solid #1976d2", paddingBottom: "4px", display: "block" }}>Active Negotiations</strong>
          {pendingTrades.map(trade => {
            const isInitiator = me.id === trade.initiator_id;
            const otherPersonId = isInitiator ? trade.target_id : trade.initiator_id;

            return (
              <div key={trade.id} style={{ padding: "10px", borderBottom: "1px solid #eee", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ fontSize: "0.85rem" }}>
                  <strong>{getPlayerName(otherPersonId)}</strong>
                  <div>They Give: {renderItems(isInitiator ? trade.request_items : trade.offer_items)}</div>
                  <div>You Give: {renderItems(isInitiator ? trade.offer_items : trade.request_items)}</div>
                </div>

                <div style={{ display: "flex", gap: "5px" }}>
                  {isInitiator ? (
                    <span style={{ fontSize: "0.8rem", color: "#888", fontStyle: "italic", alignSelf: "center", marginRight: "10px" }}>Awaiting their response...</span>
                  ) : (
                    <>
                      {/* Notice we pass the 'BARTER' command here. It allows the target to flip the terms and become the initiator! */}
                      <button className="btn-sm warning" onClick={() => onSend({ actionCommand: "BARTER", actionId: trade.id, offer_items: trade.request_items, request_items: trade.offer_items })}>Counter</button>
                      <button className="btn-sm success" onClick={() => onSend({ actionCommand: "ACCEPT", actionId: trade.id })}>Accept</button>
                    </>
                  )}
                  <button className="btn-sm danger" onClick={() => onSend({ actionCommand: isInitiator ? "CANCEL" : "DENY", actionId: trade.id })}>
                    {isInitiator ? "Revoke" : "Reject"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* --- SECTION 3: THE SHIPPING WINDOW (ACCEPTED) --- */}
      {acceptedTrades.length > 0 && (
        <div>
          <strong style={{ color: "#f57c00", borderBottom: "2px solid #f57c00", paddingBottom: "4px", display: "block", marginBottom: "10px" }}>Shipping Bay</strong>
          {acceptedTrades.map(trade => (
            <ShippingWindow key={trade.id} trade={trade} meId={me.id} onSend={onSend} getPlayerName={getPlayerName} />
          ))}
        </div>
      )}

    </div>
  );
};

export default TradeDesk;
