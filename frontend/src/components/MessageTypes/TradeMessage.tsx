import React from "react";
import { TradeMessageDTO } from "../../../../dtos";
import { BarterDraft } from "../MessageBoard";

const getFirstItem = (items: Record<string, number> | undefined) => {
  if (!items) {
    return { type: "food", amount: 0 };
  }
  const keys = Object.keys(items);
  if (keys.length === 0) {
    return { type: "food", amount: 0 };
  }
  const type = keys[0];
  return { type, amount: items[type] };
};

interface Props {
  msg: TradeMessageDTO;
  isEditing: boolean;
  barterValues: BarterDraft;
  setBarterValues: (values: BarterDraft) => void;
  isSender: boolean;
}

const TradeMessage: React.FC<Props> = ({
  msg,
  isEditing,
  barterValues,
  setBarterValues,
  isSender,
}) => {
  const inputStyle = { width: "70px", padding: "4px", marginRight: "4px" };
  const selectStyle = { padding: "4px", marginRight: "4px" };

  if (isEditing) {
    // Dynamically map the UI perspective to the global payload contract
    const giveKey = isSender ? "offer_items" : "request_items";
    const forKey = isSender ? "request_items" : "offer_items";

    const giveData = getFirstItem(barterValues[giveKey] || {});
    const forData = getFirstItem(barterValues[forKey] || {});

    return (
      <div
        style={{
          display: "flex",
          gap: "5px",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <span>Give</span>
        <input
          type="number"
          style={inputStyle}
          value={giveData.amount}
          onChange={(e) =>
            setBarterValues({
              ...barterValues,
              [giveKey]: { [giveData.type]: Number(e.target.value) },
            })
          }
        />
        <select
          style={selectStyle}
          value={giveData.type}
          onChange={(e) =>
            setBarterValues({
              ...barterValues,
              [giveKey]: { [e.target.value]: giveData.amount },
            })
          }
        >
          <option value="food">Food</option>
          <option value="wood">Wood</option>
          <option value="iron">Iron</option>
        </select>
        <span>for</span>
        <input
          type="number"
          style={inputStyle}
          value={forData.amount}
          onChange={(e) =>
            setBarterValues({
              ...barterValues,
              [forKey]: { [forData.type]: Number(e.target.value) },
            })
          }
        />
        <select
          style={selectStyle}
          value={forData.type}
          onChange={(e) =>
            setBarterValues({
              ...barterValues,
              [forKey]: { [e.target.value]: forData.amount },
            })
          }
        >
          <option value="food">Food</option>
          <option value="wood">Wood</option>
          <option value="iron">Iron</option>
        </select>
      </div>
    );
  }

  const o = getFirstItem(msg.offer_items);
  const r = getFirstItem(msg.request_items);
  const displayOffer = `${o.amount} ${o.type}`;
  const displayRequest = `${r.amount} ${r.type}`;

  return (
    <span>
      <strong>Trade:</strong> {displayOffer} ↔ {displayRequest}
      {msg.bartered && (
        <span style={{ fontStyle: "italic", color: "#888", marginLeft: "5px" }}>
          (Counter Offer)
        </span>
      )}
    </span>
  );
};

export default TradeMessage;
