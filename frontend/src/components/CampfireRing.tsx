// CampfireRing.tsx
import React from "react";
import { GameStateDTO, ShareFireMessageDTO } from "../../../dtos/index";
import { usePlayerName } from "./hooks/usePlayerName";

interface Props {
  state: GameStateDTO;
  onSend: (payload: Record<string, any>) => void;
  onAction: (action: string, payload: any) => void;
}

const CampfireRing: React.FC<Props> = ({ state, onSend, onAction }) => {
  const { me, messages, player_list } = state;
  const getPlayerName = usePlayerName();

  const fireMessages = (messages || []).filter(
    (m): m is ShareFireMessageDTO => m.type === "FIRE"
  );

  const incomingOffers = fireMessages.filter(m => m.to_id === me.id && m.action === "OFFER" && m.status === "PENDING");
  const outgoingOffers = fireMessages.filter(m => m.from_id === me.id && m.action === "OFFER" && m.status === "PENDING");

  const incomingRequests = fireMessages.filter(m => m.to_id === me.id && m.action === "REQUEST" && m.status === "PENDING");
  const outgoingRequests = fireMessages.filter(m => m.from_id === me.id && m.action === "REQUEST" && m.status === "PENDING");

  // Calculate my current guests to enforce the UI limit
  const myGuests = fireMessages.filter(m =>
    (m.from_id === me.id && m.action === "OFFER" && m.status === "ACCEPTED") ||
    (m.to_id === me.id && m.action === "REQUEST" && m.status === "ACCEPTED")
  );

  const isAtCapacity = myGuests.length >= 2;

  const handleStartFire = () => {
    onAction("START_FIRE", {});
  };

  const handleSendInvite = (playerId: string) => {
    onSend({ to_id: playerId, from_id: me.id, type: "FIRE", action: "OFFER" });
  };

  const handleRequestSeat = (playerId: string) => {
    onSend({ to_id: playerId, from_id: me.id, type: "FIRE", action: "REQUEST" });
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", height: "100%" }}>

      {/* HEADER & ALERTS */}
      <div className="card" style={{ margin: 0, background: "#2c3e50", color: "#ecf0f1" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ marginTop: 0, marginBottom: "5px" }}>The Campfire Ring</h2>
            <p style={{ margin: 0, color: "#bdc3c7", fontSize: "0.85rem" }}>Survive the night. Capacity is 2 guests per fire.</p>
          </div>
          {!me.finished_phase ? (
            <button className="btn success" onClick={() => onAction("FINISH_PHASE", {})}>
              Go to Sleep (End Day)
            </button>
          ) : (
            <span style={{ fontStyle: "italic", color: "#e67e22" }}>Sleeping...</span>
          )}
        </div>

        {/* Incoming Offers - Only visible if we aren't already a host or guest */}
        {me.fire_status === "COLD" && incomingOffers.length > 0 && (
          <div style={{ marginTop: "15px", background: "#34495e", padding: "10px", borderRadius: "6px", border: "1px solid #f39c12" }}>
            <h4 style={{ margin: "0 0 10px 0", color: "#f1c40f" }}>Warmth Offered:</h4>
            {incomingOffers.map(msg => (
              <div key={msg.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span><strong>{getPlayerName(msg.from_id)}</strong> is offering you a seat at their fire.</span>
                <div style={{ display: "flex", gap: "5px" }}>
                  <button className="btn-sm success" onClick={() => onSend({ id: msg.id, action: "ACCEPT" })}>Accept Seat</button>
                  <button className="btn-sm danger" onClick={() => onSend({ id: msg.id, action: "DENY" })}>Decline</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: "20px", flex: 1 }}>

        {/* LEFT: The Village Roster */}
        <div className="card" style={{ flex: 1, margin: 0, overflowY: "auto" }}>
          <h3 style={{ marginTop: 0 }}>The Village</h3>
          <p style={{ fontSize: "0.8rem", color: "#666" }}>Keep an eye on who is freezing and who is burning wood.</p>

          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {player_list?.filter(p => p.id !== me.id).map(player => {
              const alreadyInvited = outgoingOffers.some(m => m.to_id === player.id);
              const alreadyRequested = outgoingRequests.some(m => m.to_id === player.id);

              // Emojis based on status
              const statusEmoji = player.fire_status === "HOST" ? "🔥" : player.fire_status === "COLD" ? "🥶" : "";

              return (
                <li key={player.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#f9f9f9", padding: "10px", marginBottom: "8px", borderRadius: "6px", border: "1px solid #eee" }}>
                  <span>{player.name} {statusEmoji}</span>
                  <div style={{ display: "flex", gap: "5px" }}>

                    {/* ONLY HOSTS CAN SEND OFFERS TO COLD PLAYERS */}
                    {me.fire_status === "HOST" && player.fire_status === "COLD" && (
                      alreadyInvited ? (
                        <span style={{ fontSize: "0.75rem", color: "#888", fontStyle: "italic", alignSelf: "center" }}>Offer Sent</span>
                      ) : (
                        <button className="btn-sm" style={{ background: "#e67e22", color: "white" }} disabled={isAtCapacity} onClick={() => handleSendInvite(player.id)}>
                          Offer Seat
                        </button>
                      )
                    )}

                    {/* ONLY COLD PLAYERS CAN SEND REQUESTS TO HOSTS */}
                    {me.fire_status === "COLD" && player.fire_status === "HOST" && (
                      alreadyRequested ? (
                        <span style={{ fontSize: "0.75rem", color: "#888", fontStyle: "italic", alignSelf: "center" }}>Request Sent</span>
                      ) : (
                        <button className="btn-sm" style={{ background: "#3498db", color: "white" }} onClick={() => handleRequestSeat(player.id)}>
                          Request Seat
                        </button>
                      )
                    )}
                  </div>
                </li>
              );
            })}
          </ul>        </div>

        {/* RIGHT: Status Board */}
        <div className="card" style={{ flex: 1, margin: 0, background: me.fire_status === "COLD" ? "#f5f6fa" : "#fff3e0", border: me.fire_status === "COLD" ? "2px solid #dcdde1" : "2px solid #ffb74d", textAlign: "center" }}>

          {/* MODE 1: COLD */}
          {me.fire_status === "COLD" && (
            <div style={{ padding: "20px" }}>
              <h3 style={{ marginTop: 0, color: "#2f3640" }}>You are freezing. 🥶</h3>
              <p style={{ color: "#7f8fa6", fontSize: "0.9rem", marginBottom: "20px" }}>
                Wait for an invite, beg for a seat, or burn your own wood.
              </p>
              <button
                className="btn"
                style={{ background: me.resources.wood >= 1 ? "#e84118" : "#ccc", color: "white", padding: "10px 20px", fontSize: "1.1rem" }}
                disabled={me.resources.wood < 1}
                onClick={handleStartFire}
              >
                Start a Fire (Cost: 1 Wood)
              </button>
              {me.resources.wood < 1 && <p style={{ color: "#c23616", fontSize: "0.8rem", marginTop: "10px" }}>Not enough wood.</p>}
            </div>
          )}

          {/* MODE 2: GUEST */}
          {me.fire_status === "GUEST" && (
            <div style={{ padding: "20px" }}>
              <h3 style={{ marginTop: 0, color: "#e67e22" }}>You are safe. 🏕️</h3>
              <p style={{ color: "#7f8fa6", fontSize: "0.95rem" }}>
                You secured a warm seat by the fire for the night. Sleep well!
              </p>
            </div>
          )}

          {/* MODE 3: HOST */}
          {me.fire_status === "HOST" && (
            <>
              <h3 style={{ marginTop: 0, color: "#d84315" }}>Your Fire</h3>
              <div style={{ fontSize: "3rem", margin: "10px 0" }}>🔥</div>

              <div style={{ textAlign: "left", background: "#fff", padding: "10px", borderRadius: "6px", border: "1px dashed #ffb74d", marginBottom: "15px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                  <h4 style={{ margin: 0, fontSize: "0.9rem" }}>Sitting at your fire:</h4>
                  <span style={{ fontSize: "0.8rem", color: isAtCapacity ? "#c0392b" : "#7f8fa6" }}>
                    Capacity: {myGuests.length} / 2
                  </span>
                </div>

                {myGuests.length === 0 ? (
                  <span style={{ color: "#888", fontStyle: "italic", fontSize: "0.85rem" }}>It's just you for now.</span>
                ) : (
                  <ul style={{ paddingLeft: "20px", margin: 0, fontSize: "0.85rem" }}>
                    {myGuests.map(m => {
                      const guestId = m.action === "OFFER" ? m.to_id : m.from_id;
                      return <li key={m.id}><strong>{getPlayerName(guestId)}</strong></li>;
                    })}
                  </ul>
                )}
              </div>

              {/* Incoming Requests Box */}
              {incomingRequests.length > 0 && (
                <div style={{ textAlign: "left", background: "#ffebee", padding: "10px", borderRadius: "6px", border: "1px solid #e57373" }}>
                  <h4 style={{ margin: "0 0 10px 0", color: "#c62828", fontSize: "0.9rem" }}>Villagers asking for warmth:</h4>
                  {incomingRequests.map(msg => (
                    <div key={msg.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", fontSize: "0.85rem" }}>
                      <span><strong>{getPlayerName(msg.from_id)}</strong></span>
                      <div style={{ display: "flex", gap: "5px" }}>
                        <button className="btn-sm success" disabled={isAtCapacity} onClick={() => onSend({ id: msg.id, action: "ACCEPT" })}>Let In</button>
                        <button className="btn-sm danger" onClick={() => onSend({ id: msg.id, action: "DENY" })}>Turn Away</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

        </div>
      </div>
    </div>
  );
};

export default CampfireRing;
