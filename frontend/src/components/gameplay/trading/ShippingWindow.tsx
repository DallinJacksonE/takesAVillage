import { useEffect, useState } from "react";
import type { Resource, ResourceBundle, TradeActionDTO } from "../../../dtos";
import ResourceStepper from "../ResourceStepper";
import styles from "./ShippingWindow.module.css";
import { renderItems } from "./TradeCard";

export interface ShippingWindowProps {
  trade: TradeActionDTO;
  meId: string;
  onFinalizeTrade: (actionId: string, actualItems: Partial<ResourceBundle>) => void;
  getPlayerName: (id: string) => string;
}

const TRADE_RESOURCES: Resource[] = ["food", "wood", "iron"];

export const ShippingWindow = ({
  trade,
  meId,
  onFinalizeTrade,
  getPlayerName,
}: ShippingWindowProps) => {
  const isInitiator = meId === trade.initiator_id;
  const partnerPlayerId = isInitiator ? trade.target_id : trade.initiator_id;
  const isAlreadyShipped = isInitiator
    ? trade.initiator_finalized
    : trade.target_finalized;

  // Strict initiator ownership mapping
  const expectedToSend = isInitiator ? trade.offer_items : trade.request_items;
  const expectedToReceive = isInitiator ? trade.request_items : trade.offer_items;

  const [actualItems, setActualItems] = useState<Partial<ResourceBundle>>(
    expectedToSend || {},
  );

  // Only re-initialize if the active trade changes, so local adjustments aren't wiped on parent re-renders
  useEffect(() => {
    setActualItems({ ...(expectedToSend || {}) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trade.id]);

  const handleShipGoods = () => {
    onFinalizeTrade(trade.id, actualItems);
  };

  const partnerName = getPlayerName(partnerPlayerId || "");

  if (isAlreadyShipped) {
    return (
      <div className={styles.shippedSuccessPanel}>
        <strong className={styles.shippedSuccessTitle}>Goods Shipped!</strong>
        <div className={styles.waitingNotice}>
          Waiting for {partnerName} to send their goods...
        </div>
      </div>
    );
  }

  return (
    <div className={styles.shippingContainer}>
      <div className={styles.headerRow}>
        <strong className={styles.headerTitle}>Ship to {partnerName}</strong>
        <span className={styles.expectedBadge}>
          Expected from them: {renderItems(expectedToReceive)}
        </span>
      </div>

      <div className={styles.agreedNotice}>
        Agreed to send: {renderItems(expectedToSend)}
      </div>

      <div className={styles.stepperContainer}>
        <div className={styles.stepperList}>
          {TRADE_RESOURCES.map((resource) => (
            <ResourceStepper
              key={`ship-${resource}`}
              onChange={(value) =>
                setActualItems((prev) => ({ ...prev, [resource]: value }))
              }
              resource={resource}
              value={actualItems[resource] || 0}
            />
          ))}
        </div>

        <button
          className={`btn success ${styles.shipButton}`}
          onClick={handleShipGoods}
          type="button"
        >
          Ship Goods
        </button>
      </div>
    </div>
  );
};

export default ShippingWindow;
