import React, { useState } from "react";
import { TradeActionDTO, Resource, ResourceBundle } from "../../../dtos/index";
import ResourceStepper from "./ResourceStepper"; // <-- Import the stepper

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
    <div style={{ background: "#fafafa", padding: "12px", borderRadius: "6px", border: "1px solid #ccc", marginBottom: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
        <strong>{getPlayerName(otherPersonId || "")}</strong>
      </div>
      <div style={{ fontSize: "0.85rem", marginBottom: "10px" }}>
        <div>They Give: <strong>{renderItems(theyGive)}</strong></div>
        <div>They Want: <strong>{renderItems(theyWant)}</strong></div>
      </div>

      {isCountering ? (
        <div style={{ background: "#fff", padding: "12px", borderRadius: "6px", border: "1px dashed #2196F3", marginTop: "10px" }}>
          <div style={{ fontSize: "0.85rem", color: "#2196F3", marginBottom: "10px", fontWeight: "bold" }}>Counter Offer</div>

          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            {/* I GIVE */}
            <div style={{ flex: 1, minWidth: "140px" }}>
              <strong style={{ display: "block", marginBottom: "8px", fontSize: "0.8rem", color: "#1976d2" }}>I Give:</strong>
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
            <div style={{ flex: 1, minWidth: "140px" }}>
              <strong style={{ display: "block", marginBottom: "8px", fontSize: "0.8rem", color: "#f57c00" }}>I Want:</strong>
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

          <button className="btn" style={{ background: "#2196F3", color: "white", padding: "6px 12px", borderRadius: "4px", width: "100%", marginTop: "12px", fontWeight: "bold" }} onClick={handleSubmitCounter}>
            Send Counter Offer
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", gap: "8px" }}>
          <button className="btn success" style={{ padding: "4px 10px", fontSize: "0.8rem" }} onClick={() => onAccept(trade.id)}>Accept</button>
          <button className="btn info" style={{ padding: "4px 10px", fontSize: "0.8rem" }} onClick={handleOpenCounter}>Counter</button>
          <button className="btn danger" style={{ padding: "4px 10px", fontSize: "0.8rem" }} onClick={() => onDeny(trade.id)}>Reject</button>
        </div>
      )}
    </div>
  );
};

export default TradeCard;
