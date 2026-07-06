import React, { useState } from "react";
import { TradeActionDTO, Resource, ResourceBundle } from "../../../dtos/index";
import styles from "./TradeCard.module.css";
import ResourceStepper from "../ResourceStepper"; // <-- Import the stepper

export const renderItems = (items?: Partial<Record<Resource, number>>) => {
  if (!items || Object.keys(items).length === 0) return "Nothing";
  return Object.entries(items)
    .filter(([_, val]) => (val as number) > 0)
    .map(([res, val]) => `${val} ${res}`)
    .join(", ") || "Nothing";
};

interface TradeCardProps {
  trade: TradeActionDTO;
  meId: string;
  getPlayerName: (id: string) => string;
  onAccept: (actionId: string) => void;
  onDeny: (actionId: string) => void;
  onCounterTrade: (actionId: string, offerItems: Partial<ResourceBundle>, requestItems: Partial<ResourceBundle>) => void;
}

const TradeCard: React.FC<TradeCardProps> = ({ trade, meId, getPlayerName, onAccept, onDeny, onCounterTrade }) => {
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
    <div className={styles.panel6}>
      <div className={styles.row3}>
        <strong>{getPlayerName(otherPersonId || "")}</strong>
      </div>
      <div className={styles.panel5}>
        <div>They Give: <strong>{renderItems(theyGive)}</strong></div>
        <div>They Want: <strong>{renderItems(theyWant)}</strong></div>
      </div>

      {isCountering ? (
        <div className={styles.panel4}>
          <div className={styles.panel3}>Counter Offer</div>

          <div className={styles.row2}>
            {/* I GIVE */}
            <div className={styles.panel2}>
              <strong className={styles.label2}>I Give:</strong>
              {(["food", "wood", "iron"] as Resource[]).map((res) => (
                <ResourceStepper
                  key={`give-${res}`}
                  resource={res}
                  value={counterGiveItems[res] || 0}
                  onChange={(val) => setCounterGiveItems({ ...counterGiveItems, [res]: val })}
                />
              ))}
            </div>

            {/* I WANT */}
            <div className={styles.panel}>
              <strong className={styles.label}>I Want:</strong>
              {(["food", "wood", "iron"] as Resource[]).map((res) => (
                <ResourceStepper
                  key={`req-${res}`}
                  resource={res}
                  value={counterReqItems[res] || 0}
                  onChange={(val) => setCounterReqItems({ ...counterReqItems, [res]: val })}
                />
              ))}
            </div>
          </div>

          <button className={`btn ${styles.button4}`}  onClick={handleSubmitCounter}>
            Send Counter Offer
          </button>
        </div>
      ) : (
        <div className={styles.row}>
          <button className={`btn success ${styles.button3}`}  onClick={() => onAccept(trade.id)}>Accept</button>
          <button className={`btn info ${styles.button2}`}  onClick={handleOpenCounter}>Counter</button>
          <button className={`btn danger ${styles.button}`}  onClick={() => onDeny(trade.id)}>Reject</button>
        </div>
      )}
    </div>
  );
};

export default TradeCard;
