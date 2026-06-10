import React, { useState } from "react";
import { GameStateDTO, TradeActionDTO, Resource, ResourceBundle } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";
import TradeCard, { renderItems } from "./TradeCard";
import ShippingWindow from "./ShippingWindow";
import ResourceStepper from "./ResourceStepper"; // <-- Import the new stepper

interface Props {
  state: GameStateDTO;
  onDraftTrade: (targetId: string, offerItems: Partial<ResourceBundle>, requestItems: Partial<ResourceBundle>) => void;
  onCounterTrade: (actionId: string, offerItems: Partial<ResourceBundle>, requestItems: Partial<ResourceBundle>) => void;
  onAcceptTrade: (actionId: string) => void;
  onDenyTrade: (actionId: string) => void;
  onCancelTrade: (actionId: string) => void;
  onFinalizeTrade: (actionId: string, actualItems: Partial<ResourceBundle>) => void;
}

const TradeDesk: React.FC<Props> = ({ state, onDraftTrade, onCounterTrade, onAcceptTrade, onDenyTrade, onCancelTrade, onFinalizeTrade }) => {
  const { me, player_list } = state;
  const getPlayerName = usePlayerName();

  const [targetId, setTargetId] = useState<string | null>(null);
  const [draftGiveItems, setDraftGiveItems] = useState<Partial<ResourceBundle>>({});
  const [draftReqItems, setDraftReqItems] = useState<Partial<ResourceBundle>>({});

  const tradeActions = (me.actions || []).filter((a): a is TradeActionDTO => a.type === "TRADE" || a.type === "BARTER");
  const incomingTrades = tradeActions.filter(t => t.status === "PENDING" && t.waiting_on_id === me.id);
  const outgoingTrades = tradeActions.filter(t => t.status === "PENDING" && t.waiting_on_id !== me.id);
  const acceptedTrades = tradeActions.filter(t => t.status === "ACCEPTED");
  const otherPlayers = player_list.filter(p => p.id !== me.id);

  const handleDraftTrade = () => {
    if (!targetId) return;
    onDraftTrade(targetId, draftGiveItems, draftReqItems);
    setTargetId(null);
    setDraftGiveItems({});
    setDraftReqItems({});
  };

  return (
    <div className="card" style={{ minHeight: "297px", flex: 1, display: "flex", flexDirection: "column", gap: "20px" }}>
      <h3 style={{ marginTop: 0 }}>Trade Desk</h3>

      {/* --- TOP ROW: DRAFTING & HISTORY --- */}
      <div style={{ display: "flex", gap: "20px", flexWrap: "wrap", alignItems: "stretch" }}>

        {/* LEFT: Drafting Tray (Flex 2 takes up more room) */}
        <div style={{ flex: 2, minWidth: "300px" }}>
          <strong style={{ display: "block", marginBottom: "8px", color: "#555" }}>Draft New Trade</strong>
          <div style={{ display: "flex", overflowX: "auto", gap: "10px", paddingBottom: "10px" }}>
            {otherPlayers.map(p => (
              <button
                key={p.id}
                className="btn-user"
                style={{
                  border: targetId === p.id ? "2px solid #2196F3" : "1px solid #ccc",
                  background: targetId === p.id ? "#e3f2fd" : "#fafafa",
                  fontWeight: targetId === p.id ? "bold" : "normal"
                }}
                onClick={() => setTargetId(targetId === p.id ? null : p.id)}
              >
                {p.name}
              </button>
            ))}
          </div>

          {targetId && (
            <div style={{ background: "#fafafa", border: "1px solid #ddd", borderRadius: "8px", padding: "12px", marginTop: "10px" }}>
              <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: "140px" }}>
                  <strong style={{ display: "block", marginBottom: "8px", color: "#1976d2" }}>I Give:</strong>
                  {(["food", "wood", "iron"] as Resource[]).map(res => (
                    <ResourceStepper
                      key={res}
                      resource={res}
                      value={draftGiveItems[res] || 0}
                      onChange={(val) => setDraftGiveItems({ ...draftGiveItems, [res]: val })}
                    />
                  ))}
                </div>

                <div style={{ flex: 1, minWidth: "140px" }}>
                  <strong style={{ display: "block", marginBottom: "8px", color: "#f57c00" }}>I Want:</strong>
                  {(["food", "wood", "iron"] as Resource[]).map(res => (
                    <ResourceStepper
                      key={res}
                      resource={res}
                      value={draftReqItems[res] || 0}
                      onChange={(val) => setDraftReqItems({ ...draftReqItems, [res]: val })}
                    />
                  ))}
                </div>
              </div>

              <div style={{ marginTop: "15px" }}>
                <button className="btn" style={{ background: "#2196F3", color: "white", padding: "8px 16px", borderRadius: "4px", width: "100%", fontWeight: "bold" }} onClick={handleDraftTrade}>
                  Send Trade Offer
                </button>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Trade History (Flex 1) */}
        <div style={{ flex: 1, minWidth: "250px", background: "#fafafa", border: "1px solid #ddd", borderRadius: "8px", padding: "12px", maxHeight: "250px", overflowY: "auto" }}>
          <strong style={{ color: "#6a1b9a", borderBottom: "2px solid #ce93d8", paddingBottom: "4px", display: "block", marginBottom: "10px" }}>
            Recent Trades
          </strong>
          {(me.trade_history || []).length === 0 && <div style={{ color: "#777", fontSize: "0.9rem" }}>No recent trades</div>}
          {(me.trade_history || []).slice().reverse().map((trade) => (
            <div key={trade.id} style={{ background: "#fff", border: "1px solid #ddd", borderRadius: "6px", padding: "8px", marginBottom: "10px", fontSize: "0.82rem" }}>
              <div style={{ fontWeight: "bold", marginBottom: "6px", color: "#333" }}>With {getPlayerName(trade.target_id)}</div>
              <div style={{ marginBottom: "4px" }}><strong>Offered:</strong> <div>{renderItems(trade.offered)}</div></div>
              <div style={{ marginBottom: "4px" }}><strong>Requested:</strong> <div>{renderItems(trade.requested)}</div></div>
              <div style={{ borderTop: "1px dashed #ccc", marginTop: "6px", paddingTop: "6px" }}>
                <div style={{ marginBottom: "4px" }}><strong>Sent:</strong> <div>{renderItems(trade.actual_sent)}</div></div>
                <div><strong>Received:</strong> <div>{renderItems(trade.actual_received)}</div></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <hr style={{ border: "0", borderTop: "1px solid #ddd", margin: "0" }} />

      {/* --- MIDDLE ROW: INBOX & OUTBOX --- */}
      <div style={{ display: "flex", gap: "20px", alignItems: "stretch", flexWrap: "wrap" }}>

        {/* INBOX */}
        <div style={{ flex: 1, minWidth: "280px" }}>
          <strong style={{ color: "#1976d2", borderBottom: "2px solid #1976d2", paddingBottom: "4px", display: "block", marginBottom: "10px" }}>
            Inbox ({incomingTrades.length})
          </strong>
          {incomingTrades.map(trade => (
            <TradeCard key={trade.id} trade={trade} meId={me.id} getPlayerName={getPlayerName} onAccept={onAcceptTrade} onDeny={onDenyTrade} onCounterTrade={onCounterTrade} />
          ))}
        </div>

        {/* OUTBOX */}
        <div style={{ flex: 1, minWidth: "280px" }}>
          <strong style={{ color: "#888", borderBottom: "2px solid #ccc", paddingBottom: "4px", display: "block", marginBottom: "10px" }}>
            Awaiting Reply ({outgoingTrades.length})
          </strong>
          {outgoingTrades.map(trade => {
            const isInitiator = me.id === trade.initiator_id;
            const otherPersonId = isInitiator ? trade.target_id : trade.initiator_id;
            const iGive = isInitiator ? trade.offer_items : trade.request_items;
            const iWant = isInitiator ? trade.request_items : trade.offer_items;
            return (
              <div key={trade.id} style={{ padding: "10px", borderRadius: "6px", border: "1px dashed #ccc", marginBottom: "10px", opacity: 0.8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "5px" }}>
                  <strong>To: {getPlayerName(otherPersonId || "")}</strong>
                  <button className="btn-tooltip danger" style={{ padding: "2px 6px", fontSize: "0.7rem" }} onClick={() => onCancelTrade(trade.id)}>Revoke</button>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#555" }}>
                  <div>I Give: {renderItems(iGive)}</div>
                  <div>I Want: {renderItems(iWant)}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* --- BOTTOM ROW: SHIPPING BAY --- */}
      {acceptedTrades.length > 0 && (
        <div style={{ marginTop: "10px" }}>
          <strong style={{ color: "#f57c00", borderBottom: "2px solid #f57c00", paddingBottom: "4px", display: "block", marginBottom: "10px" }}>
            Shipping Bay (Lock-in your payload)
          </strong>
          {acceptedTrades.map(trade => (
            <ShippingWindow key={trade.id} trade={trade} meId={me.id} onFinalizeTrade={onFinalizeTrade} getPlayerName={getPlayerName} />
          ))}
        </div>
      )}
    </div>
  );
};

export default TradeDesk;
