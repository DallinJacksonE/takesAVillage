import React from "react";
import { GameStateDTO, CampfireActionDTO } from "@takes-a-village/shared";
import { usePlayerName } from "../hooks/usePlayerName";

import styles from "./CampfireRing.module.css";
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

  const isAtCapacity =
    me.fire_guests.length >= state.max_fire_seats;

  return (
    <div className={`card ${styles.column2}`} >
      <h3>Campfire</h3>

      <div className={styles.row7}>

        {/* --- LEFT COLUMN --- */}
        <div className={styles.panel9}>

          {/* MY STATUS (moved to top) */}
          <div className={styles.panel8}>
            <strong>My Status:</strong>{" "}
            <span className={me.fire_status === "COLD" ? styles.statusCold : styles.statusWarm}>
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
                <div className={styles.panel7}>
                  Warming by <strong>{getPlayerName(hostId)}</strong>'s fire
                </div>
              );
            })()}
          </div>

          {/* VILLAGE */}
          <h4 className={styles.header5}>Village</h4>

          {player_list
            .filter(p => p.id !== me.id)
            .map(p => (
              <div
                key={p.id}
                className={styles.row6}
              >
                <span>
                  {p.name}{" "}
                  {p.health === "dead"
                    ? "⚰️"
                    : p.fire_status === "HOST"
                      ? "🔥"
                      : p.fire_status === "GUEST"
                        ? "🥳"
                        : p.fire_status === "COLD"
                          ? "🥶"
                          : ""}
                </span>

                <div className={styles.row5}>

                  {/* HOST → OFFER SEAT */}
                  {me.fire_status === "HOST" &&
                    p.fire_status !== "HOST" &&
                    p.fire_status !== "GUEST" &&
                    p.health !== "dead" && (
                      <button
                        className="btn-tooltip info"
                        disabled={isAtCapacity}
                        onClick={() => onOfferSeat(p.id)}
                      >
                        Offer Seat
                      </button>
                    )}

                  {/* COLD → REQUEST SEAT FROM HOST */}
                  {me.fire_status === "COLD" && p.fire_status === "HOST" && (
                    <button
                      className="btn-tooltip success"
                      onClick={() => onRequestSeat(p.id)}
                    >
                      Request Seat
                    </button>
                  )}

                </div>
              </div>
            ))}
        </div>
        {/* --- RIGHT COLUMN --- */}
        <div className={styles.column}>

          {/* TOP RIGHT: FIRE CONTROLS */}
          <div>

            <div className={styles.panel6}>
              {me.fire_status === "COLD" && (
                <button
                  className={`btn-tooltip danger ${styles.button}`}
                  
                  disabled={me.resources.wood < 1}
                  onClick={onStartFire}
                >
                  Start Fire (1 Wood)
                </button>
              )}
            </div>

            {/* AT FIRE */}
            {fireParticipantIds.length > 0 && (
              <div className={styles.panel5}>
                <h4 className={styles.header4}>
                  At the fire
                </h4>

                <ul className={styles.list}>
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
          <div className={styles.panel4}>

            {/* INVITES */}
            {incomingOffers.length > 0 && (
              <div className={styles.panel3}>
                <h4 className={styles.header3}>
                  Campfire Invites
                </h4>

                {incomingOffers.map(offer => (
                  <div key={offer.id} className={styles.row4}>
                    <span>From <strong>{getPlayerName(offer.initiator_id)}</strong></span>
                    <div className={styles.row3}>
                      <button className="btn-tooltip success" onClick={() => onAccept(offer.id)}>Accept</button>
                      <button className="btn-tooltip danger" onClick={() => onDeny(offer.id)}>Decline</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* REQUESTS */}
            {incomingRequests.length > 0 && (
              <div className={styles.panel2}>
                <h4 className={styles.header2}>
                  Requests for warmth
                </h4>

                {incomingRequests.map(req => (
                  <div key={req.id} className={styles.row2}>
                    <span><strong>{getPlayerName(req.initiator_id)}</strong></span>
                    <div className={styles.row}>
                      <button className="btn-tooltip success" disabled={isAtCapacity} onClick={() => onAccept(req.id)}>Let In</button>
                      <button className="btn-tooltip danger" onClick={() => onDeny(req.id)}>Turn Away</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* OUTGOING */}
            {(outgoingOffers.length > 0 || outgoingRequests.length > 0) && (
              <div className={styles.panel}>
                <h4 className={styles.header}>
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
