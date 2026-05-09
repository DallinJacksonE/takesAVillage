import React from "react";
import { GameStateDTO, CampfireActionDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onSend: (payload: Record<string, any>) => void;
  onAction: (actionCommand: string, payload: any) => void;
}

const CampfireRing: React.FC<Props> = ({ state, onAction }) => {
  const { me, player_list } = state;
  const getPlayerName = usePlayerName();

  const fireActions = (me.actions || []).filter(
    (a): a is CampfireActionDTO => a.type === "CAMPFIRE"
  );

  const incomingOffers = fireActions.filter(a => a.target_id === me.id && !a.is_request && a.status === "PENDING");
  const incomingRequests = fireActions.filter(a => a.target_id === me.id && a.is_request && a.status === "PENDING");

  const outgoingOffers = fireActions.filter(a => a.initiator_id === me.id && !a.is_request && a.status === "PENDING");
  const outgoingRequests = fireActions.filter(a => a.initiator_id === me.id && a.is_request && a.status === "PENDING");

  const myGuests = fireActions.filter(a =>
    ((a.initiator_id === me.id && !a.is_request) || (a.target_id === me.id && a.is_request)) &&
    a.status === "ACCEPTED"
  );

  const isAtCapacity = myGuests.length >= 2;

  return (
    <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column", gap: "20px" }}>
      <h3>Campfire</h3>

      <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>

        {/* --- LEFT COLUMN: Village Roster --- */}
        <div style={{ flex: 1, borderRight: "1px solid #eee", paddingRight: "15px", minWidth: "200px" }}>
          <h4 style={{ marginTop: 0 }}>Village</h4>

          {player_list.filter(p => p.id !== me.id).map(p => (
            <div key={p.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", fontSize: "0.85rem" }}>
              <span>
                {p.name} {p.fire_status === "HOST" && "🔥"}
              </span>

              <div style={{ display: "flex", gap: "5px" }}>
                {p.fire_status === "HOST" && me.fire_status === "COLD" && (
                  <button
                    className="btn-sm"
                    style={{ background: "#2196F3", color: "white" }}
                    onClick={() => onAction("CAMPFIRE", { type: "CAMPFIRE", target_id: p.id, is_request: true })}
                  >
                    Request Seat
                  </button>
                )}

                {me.fire_status !== "GUEST" && p.fire_status !== "HOST" && (
                  <button
                    className="btn-sm"
                    style={{ background: "#f57c00", color: "white" }}
                    disabled={isAtCapacity || me.resources.wood < 1}
                    onClick={() => onAction("CAMPFIRE", { type: "CAMPFIRE", target_id: p.id, is_request: false })}
                  >
                    Offer Seat
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* --- RIGHT COLUMN: Inbox & Status --- */}
        <div style={{ flex: 1, minWidth: "250px" }}>

          {/* My Current Status */}
          <div style={{ marginBottom: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>My Status:</strong>{" "}
                <span style={{ color: me.fire_status === "COLD" ? "#1976d2" : "#d32f2f", fontWeight: "bold" }}>
                  {me.fire_status} {me.fire_status === "HOST" && "🔥"}
                </span>
              </div>

              {/* Start Fire Button */}
              {me.fire_status === "COLD" && (
                <button
                  className="btn success"
                  style={{ padding: "6px 12px", fontSize: "0.85rem", background: "#d32f2f" }}
                  disabled={me.resources.wood < 1}
                  onClick={() => onAction("START_FIRE", { type: "START_FIRE" })}
                >
                  Start Fire (1 Wood)
                </button>
              )}
            </div>

            {me.fire_status === "HOST" && myGuests.length > 0 && (
              <ul style={{ marginTop: "5px", paddingLeft: "20px", fontSize: "0.85rem", color: "#666" }}>
                {myGuests.map(a => {
                  const guestId = a.is_request ? a.initiator_id : a.target_id || "";
                  return <li key={a.id}><strong>{getPlayerName(guestId)}</strong></li>;
                })}
              </ul>
            )}
          </div>

          {/* Incoming Offers */}
          {incomingOffers.length > 0 && (
            <div style={{ background: "#e3f2fd", padding: "10px", borderRadius: "6px", marginBottom: "10px", border: "1px solid #bbdefb" }}>
              <h4 style={{ margin: "0 0 5px 0", color: "#1976d2", fontSize: "0.9rem" }}>Campfire Invites:</h4>
              {incomingOffers.map(offer => (
                <div key={offer.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px", fontSize: "0.85rem" }}>
                  <span>From <strong>{getPlayerName(offer.initiator_id)}</strong></span>
                  <div style={{ display: "flex", gap: "5px" }}>
                    <button className="btn-sm success" onClick={() => onAction("ACCEPT", { actionId: offer.id })}>Accept</button>
                    <button className="btn-sm danger" onClick={() => onAction("DENY", { actionId: offer.id })}>Decline</button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Incoming Requests */}
          {incomingRequests.length > 0 && (
            <div style={{ background: "#ffebee", padding: "10px", borderRadius: "6px", marginBottom: "10px", border: "1px solid #ffcdd2" }}>
              <h4 style={{ margin: "0 0 5px 0", color: "#c62828", fontSize: "0.9rem" }}>Villagers asking for warmth:</h4>
              {incomingRequests.map(req => (
                <div key={req.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px", fontSize: "0.85rem" }}>
                  <span><strong>{getPlayerName(req.initiator_id)}</strong></span>
                  <div style={{ display: "flex", gap: "5px" }}>
                    <button className="btn-sm success" disabled={isAtCapacity} onClick={() => onAction("ACCEPT", { actionId: req.id })}>Let In</button>
                    <button className="btn-sm danger" onClick={() => onAction("DENY", { actionId: req.id })}>Turn Away</button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Outgoing Waitlist */}
          {(outgoingOffers.length > 0 || outgoingRequests.length > 0) && (
            <div style={{ background: "#fafafa", padding: "10px", borderRadius: "6px", border: "1px dashed #ccc" }}>
              <h4 style={{ margin: "0 0 5px 0", color: "#888", fontSize: "0.9rem" }}>Awaiting Reply...</h4>
              {outgoingOffers.map(o => (
                <div key={o.id} style={{ fontSize: "0.8rem", color: "#666" }}>Offered seat to {getPlayerName(o.target_id || "")}</div>
              ))}
              {outgoingRequests.map(r => (
                <div key={r.id} style={{ fontSize: "0.8rem", color: "#666" }}>Requested seat from {getPlayerName(r.target_id || "")}</div>
              ))}
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default CampfireRing;
