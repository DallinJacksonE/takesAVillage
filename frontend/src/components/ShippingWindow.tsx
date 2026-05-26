import React, { useState, useEffect } from "react";
import { TradeActionDTO, Resource, ResourceBundle } from "../../../dtos/index";
import { renderItems } from "./TradeCard";
import ResourceStepper from "./ResourceStepper"; // <-- Import the stepper

interface ShippingWindowProps {
  trade: TradeActionDTO;
  meId: string;
  onFinalizeTrade: (actionId: string, actualItems: Partial<ResourceBundle>) => void;
  getPlayerName: (id: string) => string;
}

const ShippingWindow: React.FC<ShippingWindowProps> = ({ trade, meId, onFinalizeTrade, getPlayerName }) => {
  const isInitiator = meId === trade.initiator_id;
  const otherPersonId = isInitiator ? trade.target_id : trade.initiator_id;
  const hasFinalized = isInitiator ? trade.initiator_finalized : trade.target_finalized;

  // Strict Initiator Ownership mapping 
  const expectedToSend = isInitiator ? trade.offer_items : trade.request_items;
  const expectedToReceive = isInitiator ? trade.request_items : trade.offer_items;

  const [actualItems, setActualItems] = useState<Partial<ResourceBundle>>(expectedToSend || {});

  // Keep state synced if the trade updates
  useEffect(() => {
    setActualItems(expectedToSend || {});
  }, [trade, isInitiator]);

  const handleShip = () => {
    onFinalizeTrade(trade.id, actualItems);
  };

  if (hasFinalized) {
    return (
      <div style={{ background: "#e8f5e9", padding: "12px", borderRadius: "6px", marginBottom: "12px", border: "1px solid #a5d6a7" }}>
        <strong style={{ color: "#2e7d32" }}>Goods Shipped!</strong>
        <div style={{ fontSize: "0.85rem", marginTop: "5px" }}>Waiting for {getPlayerName(otherPersonId || "")} to send their goods...</div>
      </div>
    );
  }

  return (
    <div style={{ background: "#fff3e0", padding: "12px", borderRadius: "6px", marginBottom: "12px", border: "1px solid #ffcc80" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
        <strong style={{ fontSize: "1rem" }}>Ship to {getPlayerName(otherPersonId || "")}</strong>
        <span style={{ fontSize: "0.8rem", color: "#666", background: "#ffe0b2", padding: "2px 8px", borderRadius: "12px" }}>
          Expected from them: {renderItems(expectedToReceive)}
        </span>
      </div>

      <div style={{ fontSize: "0.85rem", color: "#d84315", marginBottom: "12px", fontWeight: "bold" }}>
        Agreed to send: {renderItems(expectedToSend)}
      </div>

      <div style={{ display: "flex", gap: "15px", alignItems: "center", flexWrap: "wrap", background: "#fff", padding: "10px", borderRadius: "6px", border: "1px dashed #ffb74d" }}>
        <div style={{ display: "flex", gap: "15px", flexWrap: "wrap", flex: 1 }}>
          {(["food", "wood", "iron"] as Resource[]).map((res) => (
            <ResourceStepper
              key={`ship-${res}`}
              resource={res}
              value={actualItems[res] || 0}
              onChange={(val) => setActualItems({ ...actualItems, [res]: val })}
            />
          ))}
        </div>

        <button
          className="btn success"
          style={{ padding: "8px 16px", fontWeight: "bold", whiteSpace: "nowrap" }}
          onClick={handleShip}
        >
          Ship Goods
        </button>
      </div>
    </div>
  );
};

export default ShippingWindow;
