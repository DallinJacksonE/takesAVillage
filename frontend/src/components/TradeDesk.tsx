import React, { useState } from "react";
import { GameStateDTO, TradeActionDTO, Resource, ResourceBundle } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onDraftTrade: (targetId: string, offerItems: Partial<ResourceBundle>, requestItems: Partial<ResourceBundle>) => void;
  onCounterTrade: (actionId: string, offerItems: Partial<ResourceBundle>, requestItems: Partial<ResourceBundle>) => void;
  onAcceptTrade: (actionId: string) => void;
  onDenyTrade: (actionId: string) => void;
  onCancelTrade: (actionId: string) => void;
  onFinalizeTrade: (actionId: string, actualItems: Partial<ResourceBundle>) => void;
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
const ShippingWindow: React.FC<{
  trade: TradeActionDTO;
  meId: string;
  onFinalizeTrade: Props["onFinalizeTrade"];
  getPlayerName: (id: string) => string
}> = ({ trade, meId, onFinalizeTrade, getPlayerName }) => {
  const isInitiator = meId === trade.initiator_id;
  const expectedToSend = isInitiator ? trade.offer_items : trade.request_items;
  const expectedToReceive = isInitiator ? trade.request_items : trade.offer_items;
  const otherPersonId = isInitiator ? trade.target_id : trade.initiator_id;
  const hasFinalized = isInitiator ? trade.initiator_finalized : trade.target_finalized;

  const [actualItems, setActualItems] = useState<Partial<ResourceBundle>>(expectedToSend || {});

  const handleShip = () => {
    onFinalizeTrade(trade.id, actualItems);
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

      <div style={{ fontSize: "0.85rem", color: "#555", marginTop: "5px", marginBottom: "10px" }}>
        Agreed to send: <strong>{renderItems(expectedToSend)}</strong>
      </div>

      <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
        {(["food", "wood", "iron"] as Resource[]).map((res) => (
          <div key={res} style={{ display: "flex", alignItems: "center", gap: "5px", background: "#fff", padding: "4px 8px", borderRadius: "4px", border: "1px solid #ccc" }}>
            <span style={{ fontSize: "0.8rem", textTransform: "capitalize" }}>{res}:</span>
            <input
              type="number"
              min="0"
              style={{ width: "40px", padding: "2px", border: "none", outline: "none", borderBottom: "1px solid #999" }}
              value={actualItems[res] || 0}
              onChange={(e) => setActualItems({ ...actualItems, [res]: parseInt(e.target.value) || 0 })}
            />
          </div>
        ))}
        <button className="btn success" style={{ marginLeft: "auto", padding: "6px 12px" }} onClick={handleShip}>Ship Goods</button>
      </div>
    </div>
  );
};

// --- MAIN COMPONENT ---
const TradeDesk: React.FC<Props> = ({
  state,
  onDraftTrade,
  onCounterTrade,
  onAcceptTrade,
  onDenyTrade,
  onCancelTrade,
  onFinalizeTrade
}) => {
  const { me, player_list } = state;
  const getPlayerName = usePlayerName();

  const [draftGiveItems, setDraftGiveItems] = useState<Partial<ResourceBundle>>({});
  const [draftReqItems, setDraftReqItems] = useState<Partial<ResourceBundle>>({});

  // Drafting State
  const [targetId, setTargetId] = useState<string | null>(null);
  const [counterGiveItems, setCounterGiveItems] = useState<Partial<ResourceBundle>>({});
  const [counterReqItems, setCounterReqItems] = useState<Partial<ResourceBundle>>({});

  // Counter-Offer State
  const [counteringId, setCounteringId] = useState<string | null>(null);
  const [counterGiveAmt, setCounterGiveAmt] = useState(1);
  const [counterGiveRes, setCounterGiveRes] = useState<Resource>("food");
  const [counterReqAmt, setCounterReqAmt] = useState(1);
  const [counterReqRes, setCounterReqRes] = useState<Resource>("wood");

  // Filtering Actions: Use waiting_on_id to determine Inbox vs Outbox
  const tradeActions = (me.actions || []).filter((a): a is TradeActionDTO => a.type === "TRADE" || a.type === "BARTER");
  const incomingTrades = tradeActions.filter(t => t.status === "PENDING" && t.waiting_on_id === me.id);
  const outgoingTrades = tradeActions.filter(t => t.status === "PENDING" && t.waiting_on_id !== me.id);
  const acceptedTrades = tradeActions.filter(t => t.status === "ACCEPTED");

  const otherPlayers = player_list.filter(p => p.id !== me.id);

  const handleDraftTrade = () => {
    if (!targetId) return;

    onDraftTrade(
      targetId,
      draftGiveItems,
      draftReqItems
    );

    setTargetId(null);
    setDraftGiveItems({});
    setDraftReqItems({});
  };

  const handleOpenCounter = (trade: TradeActionDTO) => {
    setCounteringId(trade.id);

    const isInitiator = me.id === trade.initiator_id;
    // Determine what *I* am currently expected to give/receive
    const myExpectedGive = isInitiator ? trade.offer_items : trade.request_items;
    const myExpectedReq = isInitiator ? trade.request_items : trade.offer_items;

    const giveKey = Object.keys(myExpectedGive || {})[0] as Resource;
    const giveVal = Object.values(myExpectedGive || {})[0] as number;
    const reqKey = Object.keys(myExpectedReq || {})[0] as Resource;
    const reqVal = Object.values(myExpectedReq || {})[0] as number;

    setCounterReqRes(reqKey || "wood");
    setCounterReqAmt(reqVal || 1);
    setCounterGiveRes(giveKey || "food");
    setCounterGiveAmt(giveVal || 1);
  };
  const handleSubmitCounter = (tradeId: string) => {
    onCounterTrade(
      tradeId,
      counterGiveItems,
      counterReqItems
    );

    setCounteringId(null);

    setCounterGiveItems({});
    setCounterReqItems({});
  };

  return (
    <div className="card" style={{ minHeight: "297px", flex: 1, display: "flex", flexDirection: "column", gap: "20px" }}>
      <h3 style={{ marginTop: 0 }}>Trade Desk</h3>

      {/* --- SECTION 1: DRAFTING TRAY --- */}
      <div>
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

        {/* Dynamic Draft Form */}
        {targetId && (
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <div>
              <strong>I Give:</strong>
              {(["food", "wood", "iron"] as Resource[]).map(res => (
                <div key={res} style={{ display: "flex", gap: "5px", alignItems: "center" }}>
                  <span>{res}</span>
                  <input
                    type="number"
                    min="0"
                    value={draftGiveItems[res] || 0}
                    onChange={(e) =>
                      setDraftGiveItems({
                        ...draftGiveItems,
                        [res]: parseInt(e.target.value) || 0,
                      })
                    }
                    style={{ width: "55px" }}
                  />
                </div>
              ))}
            </div>

            <div>
              <strong>I Want:</strong>
              {(["food", "wood", "iron"] as Resource[]).map(res => (
                <div key={res} style={{ display: "flex", gap: "5px", alignItems: "center" }}>
                  <span>{res}</span>
                  <input
                    type="number"
                    min="0"
                    value={draftReqItems[res] || 0}
                    onChange={(e) =>
                      setDraftReqItems({
                        ...draftReqItems,
                        [res]: parseInt(e.target.value) || 0,
                      })
                    }
                    style={{ width: "55px" }}
                  />
                </div>
              ))}
            </div>

            <div style={{ width: "100%", marginTop: "10px" }}>
              <button
                className="btn"
                style={{
                  background: "#2196F3",
                  color: "white",
                  padding: "6px 12px",
                  borderRadius: "4px",
                }}
                onClick={handleDraftTrade}
              >
                Send Trade Offer
              </button>
            </div>
          </div>
        )}
      </div>

      {/* --- SECTION 2: INBOX & OUTBOX (TWO COLUMNS) --- */}
      <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>

        {/* LEFT COLUMN: INBOX */}
        <div style={{ flex: 1, minWidth: "300px" }}>
          <strong style={{ color: "#1976d2", borderBottom: "2px solid #1976d2", paddingBottom: "4px", display: "block", marginBottom: "10px" }}>
            Inbox ({incomingTrades.length})
          </strong>
          {incomingTrades.map(trade => {
            const isInitiator = me.id === trade.initiator_id;
            const otherPersonId = isInitiator ? trade.target_id : trade.initiator_id;
            const theyGive = isInitiator ? trade.request_items : trade.offer_items;
            const theyWant = isInitiator ? trade.offer_items : trade.request_items;

            return (
              <div key={trade.id} style={{ background: "#fafafa", padding: "10px", borderRadius: "6px", border: "1px solid #ccc", marginBottom: "10px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <strong>{getPlayerName(otherPersonId || "")}</strong>
                </div>
                <div style={{ fontSize: "0.85rem", marginBottom: "10px" }}>
                  <div>They Give: <strong>{renderItems(theyGive)}</strong></div>
                  <div>They Want: <strong>{renderItems(theyWant)}</strong></div>
                </div>
                {/* Inline Counter Form */}
                {counteringId === trade.id ? (
                  <div style={{ background: "#fff", padding: "10px", borderRadius: "4px", border: "1px dashed #2196F3", marginBottom: "10px" }}>
                    <div style={{ fontSize: "0.8rem", color: "#2196F3", marginBottom: "5px", fontWeight: "bold" }}>Counter Offer:</div>
                    <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>

                      <div>
                        <strong>I Give:</strong>

                        {(["food", "wood", "iron"] as Resource[]).map(res => (
                          <div key={res} style={{ display: "flex", gap: "5px", alignItems: "center" }}>
                            <span>{res}</span>

                            <input
                              type="number"
                              min="0"
                              value={counterGiveItems[res] || 0}
                              onChange={(e) =>
                                setCounterGiveItems({
                                  ...counterGiveItems,
                                  [res]: parseInt(e.target.value) || 0,
                                })
                              }
                              style={{ width: "55px" }}
                            />
                          </div>
                        ))}
                      </div>

                      <div>
                        <strong>I Want:</strong>

                        {(["food", "wood", "iron"] as Resource[]).map(res => (
                          <div key={res} style={{ display: "flex", gap: "5px", alignItems: "center" }}>
                            <span>{res}</span>

                            <input
                              type="number"
                              min="0"
                              value={counterReqItems[res] || 0}
                              onChange={(e) =>
                                setCounterReqItems({
                                  ...counterReqItems,
                                  [res]: parseInt(e.target.value) || 0,
                                })
                              }
                              style={{ width: "55px" }}
                            />
                          </div>
                        ))}
                      </div>

                      <div style={{ width: "100%", marginTop: "10px" }}>
                        <button
                          className="btn-tooltip info"
                          style={{
                            background: "#2196F3",
                            color: "white",
                            padding: "6px 12px",
                            borderRadius: "4px",
                          }}
                          onClick={() => handleSubmitCounter(trade.id)}
                        >
                          Send Counter Offer
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ display: "flex", gap: "5px" }}>
                    <button className="btn-tooltip success" onClick={() => onAcceptTrade(trade.id)}>Accept</button>
                    <button className="btn-tooltip info" onClick={() => handleOpenCounter(trade)}>Counter</button>
                    <button className="btn-tooltip danger" onClick={() => onDenyTrade(trade.id)}>Reject</button>
                  </div>
                )}
              </div>

            );
          })}
        </div>

        {/* RIGHT COLUMN: PENDING / OUTBOX */}
        <div style={{ flex: 1, minWidth: "300px" }}>
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

      {/* --- SECTION 3: THE SHIPPING WINDOW (ACCEPTED) --- */}
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
