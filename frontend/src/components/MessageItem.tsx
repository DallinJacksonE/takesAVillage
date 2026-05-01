import React, { useState } from "react";
import { MessageDTO } from "../../../dtos/index";
import ChatMessage from "./MessageTypes/ChatMessage";
import JobOfferMessage from "./MessageTypes/JobOfferMessage";
import TradeMessage from "./MessageTypes/TradeMessage";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  msg: MessageDTO;
  playerId: string;
  myResources: { wood: number; food: number; iron: number };
  isEditing: boolean;
  barterValues: Partial<MessageDTO>;
  setBarterValues: (values: Partial<MessageDTO>) => void;
  onSend: (payload: Partial<MessageDTO> & { action?: string }) => void;
  onBarterStart: (msg: MessageDTO) => void;
  onSendUpdate: () => void;
  onCancelEdit: () => void;
}

const MessageItem: React.FC<Props> = ({
  msg,
  playerId,
  myResources,
  isEditing,
  barterValues,
  setBarterValues,
  onSend,
  onBarterStart,
  onSendUpdate,
  onCancelEdit,
}) => {
  const getPlayerName = usePlayerName();
  const isMe = msg.from_id === playerId;
  const isReceivedCounterOffer = msg.bartered && msg.to_id === playerId;

  const showActions =
    msg.type !== "TEXT" &&
    !isEditing &&
    msg.to_id === playerId &&
    (msg.status === "PENDING" || msg.bartered);

  const isSender = playerId === msg.from_id;
  const hasFinalized = isSender
    ? msg.sender_finalized
    : msg.recipient_finalized;
  const expectedItems = isSender ? msg.offer_items : msg.request_items;
  const [actualItems, setActualItems] = useState<Record<string, number>>(
    expectedItems || {},
  );

  const isExceedingInventory = Object.entries(actualItems).some(
    ([res, amt]) => amt > (myResources[res as keyof typeof myResources] || 0),
  );

  let isBarterExceedingInventory = false;
  if (
    isEditing &&
    msg.type === "EMPLOYMENT" &&
    msg.employer_id === playerId && // Fixed: Check against the explicit employer_id
    barterValues.wage_offer !== undefined &&
    barterValues.wage_type
  ) {
    isBarterExceedingInventory =
      barterValues.wage_offer >
      (myResources[barterValues.wage_type as keyof typeof myResources] || 0);
  }

  if (msg.is_system) {
    return (
      <div
        key={msg.id}
        style={{
          textAlign: "center",
          fontStyle: "italic",
          color: "#666",
          margin: "5px 0",
          fontSize: "0.8rem",
        }}
      >
        {msg.content}
      </div>
    );
  }

  return (
    <div
      key={msg.id}
      className="message-card"
      style={{
        border: isEditing
          ? "2px solid #2196F3"
          : isReceivedCounterOffer
            ? "2px solid #FFC107"
            : "1px solid #ddd",
        padding: "10px",
        marginBottom: "8px",
        borderRadius: "6px",
        background: "#fff",
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: "0.75rem",
          marginBottom: "8px",
          color: "#555",
        }}
      >
        <span style={{ fontWeight: "bold" }}>
          {isMe
            ? `To: ${getPlayerName(msg.to_id)}`
            : `From: ${getPlayerName(msg.from_id)}`}
        </span>
        <span
          style={{
            background:
              msg.status === "ACCEPTED"
                ? "#e8f5e9"
                : msg.status === "COMPLETED"
                  ? "#d1c4e9"
                  : msg.status === "DENIED"
                    ? "#ffebee"
                    : msg.bartered
                      ? "#fff3e0"
                      : "#e3f2fd",
            padding: "2px 6px",
            borderRadius: "4px",
            textTransform: "uppercase",
            fontSize: "0.7rem",
          }}
        >
          {msg.status}
        </span>
      </div>

      <div style={{ padding: "5px 0", fontSize: "0.9rem" }}>
        {msg.status === "ACCEPTED" && msg.type === "TRADE" ? (
          <div>
            <TradeMessage
              msg={msg}
              isEditing={false}
              barterValues={barterValues}
              setBarterValues={setBarterValues}
            />
            {hasFinalized ? (
              <div
                style={{
                  padding: "10px",
                  background: "#fdfd96",
                  borderRadius: "4px",
                  marginTop: "10px",
                }}
              >
                <em>Waiting for other player to finalize...</em>
              </div>
            ) : (
              <div
                style={{
                  padding: "10px",
                  background: "#e2e2e2",
                  borderRadius: "5px",
                  marginTop: "10px",
                }}
              >
                <strong>Trade Agreed!</strong> Prepare your actual delivery:
                {expectedItems &&
                  Object.keys(expectedItems).map((res) => (
                    <div
                      key={res}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        marginTop: "5px",
                      }}
                    >
                      <span
                        style={{ textTransform: "capitalize", width: "50px" }}
                      >
                        {res}:
                      </span>
                      <input
                        type="number"
                        min="0"
                        style={{ width: "60px", padding: "4px" }}
                        value={actualItems[res] || 0}
                        onChange={(e) =>
                          setActualItems({
                            ...actualItems,
                            [res]: Number(e.target.value),
                          })
                        }
                      />
                    </div>
                  ))}
                <button
                  className="btn-sm success"
                  style={{ marginTop: "10px" }}
                  disabled={isExceedingInventory}
                  onClick={() =>
                    onSend({
                      id: msg.id,
                      action: "FINALIZE",
                      actual_items: actualItems,
                    })
                  }
                >
                  Finalize Shipment
                </button>
              </div>
            )}
          </div>
        ) : isEditing ? (
          <div
            style={{
              background: "#f5f5f5",
              padding: "10px",
              borderRadius: "4px",
            }}
          >
            {msg.type === "EMPLOYMENT" && (
              <JobOfferMessage
                msg={msg}
                isEditing={isEditing}
                barterValues={barterValues}
                setBarterValues={setBarterValues}
              />
            )}
            {msg.type === "TRADE" && (
              <TradeMessage
                msg={msg}
                isEditing={isEditing}
                barterValues={barterValues}
                setBarterValues={setBarterValues}
              />
            )}
          </div>
        ) : msg.status === "COMPLETED" && msg.type === "TRADE" ? (
          <div>
            <TradeMessage
              msg={msg}
              isEditing={false}
              barterValues={barterValues}
              setBarterValues={setBarterValues}
            />
            <div
              style={{
                marginTop: "10px",
                padding: "10px",
                background: "#f3e5f5",
                borderRadius: "5px",
                fontSize: "0.85rem",
              }}
            >
              <strong>Shipment Finalized</strong>
              <div style={{ marginTop: "4px", color: "#666" }}>
                <div>
                  <strong>You sent:</strong>{" "}
                  {Object.entries(
                    isSender
                      ? msg.actual_offer_items || {}
                      : msg.actual_request_items || {},
                  )
                    .map(([res, amt]) => `${amt} ${res}`)
                    .join(", ") || "Nothing"}
                </div>
                <div>
                  <strong>You received:</strong>{" "}
                  {Object.entries(
                    isSender
                      ? msg.actual_request_items || {}
                      : msg.actual_offer_items || {},
                  )
                    .map(([res, amt]) => `${amt} ${res}`)
                    .join(", ") || "Nothing"}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div>
            {msg.type === "TEXT" && <ChatMessage msg={msg} />}
            {msg.type === "EMPLOYMENT" && (
              <JobOfferMessage
                msg={msg}
                isEditing={isEditing}
                barterValues={barterValues}
                setBarterValues={setBarterValues}
              />
            )}
            {msg.type === "TRADE" && (
              <TradeMessage
                msg={msg}
                isEditing={isEditing}
                barterValues={barterValues}
                setBarterValues={setBarterValues}
              />
            )}
          </div>
        )}
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          gap: "8px",
          marginTop: "8px",
        }}
      >
        {showActions && (
          <>
            <button
              className="btn-sm success"
              onClick={() => onSend({ id: msg.id, action: "ACCEPT" })}
            >
              Accept
            </button>
            <button
              className="btn-sm warning"
              onClick={() => onBarterStart(msg)}
            >
              Counter Offer
            </button>
            <button
              className="btn-sm danger"
              onClick={() => onSend({ id: msg.id, action: "DENY" })}
            >
              Deny
            </button>
          </>
        )}
        {isEditing && (
          <>
            <button
              className="btn-sm success"
              onClick={onSendUpdate}
              disabled={isBarterExceedingInventory}
            >
              Send Offer
            </button>
            <button className="btn-sm" onClick={onCancelEdit}>
              Cancel
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default MessageItem;
