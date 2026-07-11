import React, { useState, useEffect } from "react";
import { TradeActionDTO, Resource, ResourceBundle } from "../../../dtos/index";
import { renderItems } from "./TradeCard";
import styles from "./ShippingWindow.module.css";
import ResourceStepper from "../ResourceStepper"; // <-- Import the stepper

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
    setActualItems({ ...(expectedToSend || {}) });
  }, [trade.id]);

  const handleShip = () => {
    onFinalizeTrade(trade.id, actualItems);
  };

  if (hasFinalized) {
    return (
      <div className={styles.panel4}>
        <strong className={styles.label2}>Goods Shipped!</strong>
        <div className={styles.panel3}>Waiting for {getPlayerName(otherPersonId || "")} to send their goods...</div>
      </div>
    );
  }

  return (
    <div className={styles.panel2}>
      <div className={styles.row3}>
        <strong className={styles.label}>Ship to {getPlayerName(otherPersonId || "")}</strong>
        <span className={styles.text}>
          Expected from them: {renderItems(expectedToReceive)}
        </span>
      </div>

      <div className={styles.panel}>
        Agreed to send: {renderItems(expectedToSend)}
      </div>

      <div className={styles.row2}>
        <div className={styles.row}>
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
          className={`btn success ${styles.button}`}
          
          onClick={handleShip}
        >
          Ship Goods
        </button>
      </div>
    </div>
  );
};

export default ShippingWindow;
