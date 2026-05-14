import React from "react";
import { GameStateDTO, CampfireActionDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onStartFire: () => void;
  onRequestSeat: (targetId: string) => void;
  onOfferSeat: (targetId: string) => void;
  onAccept: (actionId: string) => void;
  onDeny: (actionId: string) => void;
}

const CampfireRing: React.FC<Props> = ({
  state,
  onStartFire,
  onRequestSeat,
  onOfferSeat,
  onAccept,
  onDeny
}) => {
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

  const acceptedFireActions = fireActions.filter(a => a.status === "ACCEPTED");
  const fireSessions = acceptedFireActions.reduce<Record<string, { hostId: string; guestIds: string[] }>>((sessions, action) => {
    const hostId = action.is_request ? action.target_id : action.initiator_id;
    const guestId = action.is_request ? action.initiator_id : action.target_id;

    if (!hostId || !guestId) {
      return sessions;
    }

    const session = sessions[hostId] || { hostId, guestIds: [] };
    if (!session.guestIds.includes(guestId)) {
      session.guestIds = [...session.guestIds, guestId];
    }
    sessions[hostId] = session;
    return sessions;
  }, {});

  const myFireSession = me.fire_status === "HOST"
    ? fireSessions[me.id]
    : Object.values(fireSessions).find(session => session.guestIds.includes(me.id));

  const fireParticipantIds = myFireSession
    ? [myFireSession.hostId, ...myFireSession.guestIds].filter((id, index, arr) => id && arr.indexOf(id) === index)
    : [];

  const isAtCapacity = myGuests.length >= 2;

  return (
    <div className="card" style={{ minHeight: "297px", flex: 1, display: "flex", flexDirection: "column", gap: "20px" }}>
      <h3>Campfire</h3>

      <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>

      {/* --- LEFT COLUMN --- */}
      <div style={{ flex: 1, borderRight: "1px solid #eee", paddingRight: "15px", minWidth: "220px" }}>

        {/* MY STATUS (moved to top) */}
        <div style={{ marginBottom: "15px", paddingBottom: "10px", borderBottom: "1px solid #eee" }}>
          <strong>My Status:</strong>{" "}
          <span style={{ color: me.fire_status === "COLD" ? "#1976d2" : "#d32f2f", fontWeight: "bold" }}>
            {me.fire_status} {me.fire_status === "HOST" && "🔥"}
          </span>

          {me.fire_status === "GUEST" && (() => {
            const hostAction = fireActions.find(a =>
              a.status === "ACCEPTED" && (
                (a.is_request && a.initiator_id === me.id) ||
                (!a.is_request && a.target_id === me.id)
              )
            );

            const hostId = hostAction
              ? (hostAction.is_request ? hostAction.target_id : hostAction.initiator_id)
              : "";

            return (
              <div style={{ marginTop: "5px", fontSize: "0.85rem", color: "#666" }}>
                Warming by <strong>{getPlayerName(hostId)}</strong>'s fire
              </div>
            );
          })()}
        </div>

        {/* VILLAGE */}
        <h4 style={{ marginTop: 0 }}>Village</h4>

        {player_list.filter(p => p.id !== me.id).map(p => (
          <div
            key={p.id}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "8px",
              fontSize: "0.85rem"
            }}
          >
            <span>
              {p.name}{" "}
              {p.fire_status === "HOST"
                ? "🔥"
                : p.fire_status === "GUEST"
                ? "🥳"
                : p.fire_status === "COLD"
                ? "🥶"
                : ""}
            </span>

            {me.fire_status === "GUEST" && (() => {
              const hostAction = fireActions.find(a =>
                a.status === "ACCEPTED" && (
                  (a.is_request && a.initiator_id === me.id) ||
                  (!a.is_request && a.target_id === me.id)
                )
              );

              const hostId = hostAction
                ? (hostAction.is_request ? hostAction.target_id : hostAction.initiator_id)
                : "";

              return (
                <div style={{ marginTop: "5px", fontSize: "0.85rem", color: "#666" }}>
                  Warming by <strong>{getPlayerName(hostId)}</strong>'s fire
                </div>
              );
            })()}
          </div>

          {/* VILLAGE */}
          <h4 style={{ marginTop: 0 }}>Village</h4>

          {player_list.filter(p => p.id !== me.id).map(p => (
            <div
              key={p.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "8px",
                fontSize: "1rem",
                fontWeight: "bold"
              }}
            >
              <span>
                {p.name} {p.fire_status === "HOST" || p.fire_status === "GUEST" ? "🔥" : ""}
              </span>

              <div style={{ display: "flex", gap: "5px" }}>
                {p.fire_status === "HOST" && me.fire_status === "COLD" && (
                  <button className="btn-tooltip info" onClick={() => onRequestSeat(p.id)}>
                    Request Seat
                  </button>
                )}

                {me.fire_status === "HOST" &&
                  p.fire_status !== "HOST" &&
                  p.fire_status !== "GUEST" && (
                    <button
                      className="btn-tooltip info"
                      disabled={isAtCapacity}
                      onClick={() => onOfferSeat(p.id)}
                    >
                      Offer Seat
                    </button>
                  )}
              </div>
            </div>
          ))}
        </div>

        {/* --- RIGHT COLUMN --- */}
        <div style={{ flex: 1, minWidth: "280px", display: "flex", flexDirection: "column", gap: "15px" }}>

          {/* TOP RIGHT: FIRE CONTROLS */}
          <div>

            <div style={{ marginBottom: "10px" }}>
              {me.fire_status === "COLD" && (
                <button
                  className="btn-tooltip danger"
                  style={{
                    padding: "8px 14px",
                    fontSize: "0.85rem",
                  }}
                  disabled={me.resources.wood < 1}
                  onClick={onStartFire}
                >
                  Start Fire (1 Wood)
                </button>
              )}
            </div>

            {/* AT FIRE */}
            {fireParticipantIds.length > 0 && (
              <div style={{ marginTop: "15px", padding: "10px", background: "#fafafa", borderRadius: "8px", border: "1px solid #ddd" }}>
                <h4 style={{ margin: "0 0 8px 0", fontSize: "0.9rem", color: "#444" }}>
                  At the fire
                </h4>

                <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "0.85rem", color: "#666" }}>
                  {fireParticipantIds.map(id => (
                    <li key={id}>
                      <strong>{getPlayerName(id)}</strong>
                      {id === me.id ? " (You)" : ""}
                      {id === myFireSession?.hostId ? " — Host" : ""}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* BOTTOM RIGHT: STATUS FEED */}
          <div style={{ marginTop: "auto" }}>

            {/* INVITES */}
            {incomingOffers.length > 0 && (
              <div style={{ background: "#e3f2fd", padding: "10px", borderRadius: "6px", marginBottom: "10px" }}>
                <h4 style={{ margin: "0 0 5px 0", color: "#1976d2", fontSize: "0.9rem" }}>
                  Campfire Invites
                </h4>

                {incomingOffers.map(offer => (
                  <div key={offer.id} style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>From <strong>{getPlayerName(offer.initiator_id)}</strong></span>
                    <div style={{ display: "flex", gap: "5px" }}>
                      <button className="btn-tooltip success" onClick={() => onAccept(offer.id)}>Accept</button>
                      <button className="btn-tooltip danger" onClick={() => onDeny(offer.id)}>Decline</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* REQUESTS */}
            {incomingRequests.length > 0 && (
              <div style={{ background: "#ffebee", padding: "10px", borderRadius: "6px", marginBottom: "10px" }}>
                <h4 style={{ margin: "0 0 5px 0", color: "#c62828", fontSize: "0.9rem" }}>
                  Requests for warmth
                </h4>

                {incomingRequests.map(req => (
                  <div key={req.id} style={{ display: "flex", justifyContent: "space-between" }}>
                    <span><strong>{getPlayerName(req.initiator_id)}</strong></span>
                    <div style={{ display: "flex", gap: "5px" }}>
                      <button className="btn-tooltip success" disabled={isAtCapacity} onClick={() => onAccept(req.id)}>Let In</button>
                      <button className="btn-tooltip danger" onClick={() => onDeny(req.id)}>Turn Away</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* OUTGOING */}
            {(outgoingOffers.length > 0 || outgoingRequests.length > 0) && (
              <div style={{ background: "#fafafa", padding: "10px", borderRadius: "6px", border: "1px dashed #ccc" }}>
                <h4 style={{ margin: "0 0 5px 0", color: "#888", fontSize: "0.9rem" }}>
                  Awaiting Reply
                </h4>

                {outgoingOffers.map(o => (
                  <div key={o.id}>
                    Offered seat to {getPlayerName(o.target_id || "")}
                  </div>
                ))}

                {outgoingRequests.map(r => (
                  <div key={r.id}>
                    Requested seat from {getPlayerName(r.target_id || "")}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CampfireRing;
