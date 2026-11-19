import React, { useState } from "react";
import { TradeActionDTO, Resource, ResourceBundle } from "../../../dtos/index";
import ResourceStepper from "../ResourceStepper";
import styles from "./TradeCard.module.css";

const TRADE_RESOURCES: Resource[] = ["food", "wood", "iron"];

export const renderItems = (items?: Partial<Record<Resource, number>>): string => {
  if (!items || Object.keys(items).length === 0) return "Nothing";
  return (
    Object.entries(items)
      .filter(([_, val]) => (val as number) > 0)
      .map(([res, val]) => `${val} ${res}`)
      .join(", ") || "Nothing"
  );
};

export interface TradeCardProps {
  trade: TradeActionDTO;
  meId: string;
  getPlayerName: (id: string) => string;
  onAccept: (actionId: string) => void;
  onDeny: (actionId: string) => void;
  onCounterTrade: (
    actionId: string,
    offerItems: Partial<ResourceBundle>,
    requestItems: Partial<ResourceBundle>,
  ) => void;
}

export const TradeCard: React.FC<TradeCardProps> = ({
  trade,
  meId,
  getPlayerName,
  onAccept,
  onDeny,
  onCounterTrade,
}) => {
  const isInitiator = meId === trade.initiator_id;
  const otherPersonId = isInitiator ? trade.target_id : trade.initiator_id;

  const theyGive = isInitiator ? trade.request_items : trade.offer_items;
  const theyWant = isInitiator ? trade.offer_items : trade.request_items;

  const [isCountering, setIsCountering] = useState(false);
  const [counterGiveItems, setCounterGiveItems] = useState<Partial<ResourceBundle>>({});
  const [counterReqItems, setCounterReqItems] = useState<Partial<ResourceBundle>>({});

  const handleOpenCounter = () => {
    setIsCountering(true);
    const myExpectedGive = isInitiator ? trade.offer_items : trade.request_items;
    const myExpectedReq = isInitiator ? trade.request_items : trade.offer_items;
    setCounterGiveItems(myExpectedGive || {});
    setCounterReqItems(myExpectedReq || {});
  };

  const handleSubmitCounter = () => {
    const payloadOffer = isInitiator ? counterGiveItems : counterReqItems;
    const payloadRequest = isInitiator ? counterReqItems : counterGiveItems;
    onCounterTrade(trade.id, payloadOffer, payloadRequest);
    setIsCountering(false);
  };

  return (
    <div className={styles.tradeCard}>
      <div className={styles.cardHeader}>
        <strong>{getPlayerName(otherPersonId || "")}</strong>
      </div>
      <div className={styles.tradeSummary}>
        <div>
          They Give: <strong>{renderItems(theyGive)}</strong>
        </div>
        <div>
          They Want: <strong>{renderItems(theyWant)}</strong>
        </div>
      </div>

      {isCountering ? (
        <div className={styles.counterSection}>
          <div className={styles.counterTitle}>Counter Offer</div>

          <div className={styles.counterColumns}>
            {/* I GIVE */}
            <div className={styles.resourceColumn}>
              <strong className={styles.giveLabel}>I Give:</strong>
              {TRADE_RESOURCES.map((res) => (
                <ResourceStepper
                  key={`give-${res}`}
                  resource={res}
                  value={counterGiveItems[res] || 0}
                  onChange={(val) => setCounterGiveItems({ ...counterGiveItems, [res]: val })}
                />
              ))}
            </div>

            {/* I WANT */}
            <div className={styles.resourceColumn}>
              <strong className={styles.wantLabel}>I Want:</strong>
              {TRADE_RESOURCES.map((res) => (
                <ResourceStepper
                  key={`req-${res}`}
                  resource={res}
                  value={counterReqItems[res] || 0}
                  onChange={(val) => setCounterReqItems({ ...counterReqItems, [res]: val })}
                />
              ))}
            </div>
          </div>

          <button className={`btn ${styles.counterSubmitButton}`} onClick={handleSubmitCounter}>
            Send Counter Offer
          </button>
        </div>
      ) : (
        <div className={styles.actionButtonsRow}>
          <button
            className={`btn success ${styles.actionButton}`}
            onClick={() => onAccept(trade.id)}
          >
            Accept
          </button>
          <button
            className={`btn info ${styles.actionButton}`}
            onClick={handleOpenCounter}
          >
            Counter
          </button>
          <button
            className={`btn danger ${styles.actionButton}`}
            onClick={() => onDeny(trade.id)}
          >
            Reject
          </button>
        </div>
      )}
    </div>
  );
};

export default TradeCard;
