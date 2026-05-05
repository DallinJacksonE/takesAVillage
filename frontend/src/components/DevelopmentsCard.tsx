import React, { useState } from "react";
import { GameStateDTO, EmploymentMessageDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onSend: (payload: Record<string, any>) => void;
}

const DevelopmentsCard: React.FC<Props> = ({ state, onSend }) => {
  const { me, messages } = state;
  const getPlayerName = usePlayerName();

  const [expandedDevId, setExpandedDevId] = useState<string | null>(null);

  // State for drafting a counter-offer
  const [counteringMsgId, setCounteringMsgId] = useState<string | null>(null);
  const [counterWage, setCounterWage] = useState(1);
  const [counterType, setCounterType] = useState("food");

  const toggleExpand = (devId: string) => {
    setExpandedDevId(expandedDevId === devId ? null : devId);
    setCounteringMsgId(null);
  };

  const startCounter = (msg: EmploymentMessageDTO) => {
    setCounteringMsgId(msg.id);
    setCounterWage(msg.wage_offer || 1);
    setCounterType(msg.wage_type || "food");
  };

  const submitCounter = (msgId: string) => {
    onSend({
      id: msgId,
      action: "BARTER",
      wage_offer: counterWage,
      wage_type: counterType,
    });
    setCounteringMsgId(null);
  };

  return (
    <div className='card' style={{ margin: 0, flex: 1, overflowY: "auto" }}>
      <h3>My Developments</h3>
      <p style={{ fontSize: "0.8rem", color: "#666" }}>Manage your sites</p>

      {!me.developments || me.developments.length === 0 ? (
        <p style={{ color: "#888", fontStyle: "italic" }}>
          No developments yet.
        </p>
      ) : (
        me.developments.map((dev) => {
          // Find pending employment requests for this specific development
          const pendingApps = (messages || []).filter(
            (m) => m.type === "EMPLOYMENT" &&
              (m as EmploymentMessageDTO).dev_id === dev.id &&
              m.status === "PENDING" &&
              m.pending_action_from === me.id
          ) as EmploymentMessageDTO[];

          const isExpanded = expandedDevId === dev.id;

          return (
            <div
              key={dev.id}
              style={{
                marginBottom: "10px",
                borderRadius: "6px",
                border: isExpanded ? "2px solid #4CAF50" : "1px solid #eee",
                background: "#f9f9f9",
                overflow: "hidden"
              }}
            >
              {/* Development Header */}
              <div
                style={{ padding: "10px", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}
                onClick={() => toggleExpand(dev.id)}
              >
                <div>
                  <strong>{dev.type} (Lvl {dev.level})</strong>
                  <div style={{ fontSize: "0.75rem", color: "#555" }}>
                    Maint: {dev.maintenence_days} days
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  {pendingApps.length > 0 && (
                    <span style={{ background: "#FF5722", color: "white", padding: "2px 6px", borderRadius: "10px", fontSize: "0.7rem", fontWeight: "bold" }}>
                      {pendingApps.length} Apps
                    </span>
                  )}
                  <span>{isExpanded ? "▲" : "▼"}</span>
                </div>
              </div>

              {/* Incoming Applications Body */}
              {isExpanded && (
                <div style={{ padding: "10px", background: "#fff", borderTop: "1px solid #eee" }}>
                  {pendingApps.length === 0 ? (
                    <span style={{ fontSize: "0.85rem", color: "#888", fontStyle: "italic" }}>No pending applications.</span>
                  ) : (
                    pendingApps.map(msg => (
                      <div key={msg.id} style={{ background: "#f5f5f5", padding: "8px", borderRadius: "4px", marginBottom: "5px", fontSize: "0.85rem" }}>
                        <div style={{ marginBottom: "5px" }}>
                          <strong>{getPlayerName(msg.from_id)}</strong> wants to work for <strong>{msg.wage_offer} {msg.wage_type}</strong>.
                        </div>

                        {/* Action Buttons OR Counter Input */}
                        {counteringMsgId === msg.id ? (
                          <div style={{ display: "flex", gap: "5px", alignItems: "center", marginTop: "8px" }}>
                            <span>Offer:</span>
                            <input type="number" min="1" style={{ width: "50px", padding: "2px" }} value={counterWage} onChange={e => setCounterWage(Number(e.target.value))} />
                            <select style={{ padding: "2px" }} value={counterType} onChange={e => setCounterType(e.target.value)}>
                              <option value="food">Food</option>
                              <option value="wood">Wood</option>
                              <option value="iron">Iron</option>
                            </select>
                            <button className="btn-sm success" onClick={() => submitCounter(msg.id)}>Send</button>
                            <button className="btn-sm danger" onClick={() => setCounteringMsgId(null)}>X</button>
                          </div>
                        ) : (
                          <div style={{ display: "flex", gap: "5px", marginTop: "8px" }}>
                            <button className="btn-sm success" onClick={() => onSend({ id: msg.id, action: "ACCEPT" })}>Accept</button>
                            <button className="btn-sm warning" onClick={() => startCounter(msg)}>Counter</button>
                            <button className="btn-sm danger" onClick={() => onSend({ id: msg.id, action: "DENY" })}>Deny</button>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
};

export default DevelopmentsCard;
