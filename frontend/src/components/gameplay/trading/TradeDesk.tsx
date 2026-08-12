import React, { useState } from "react";
import { GameStateDTO, TradeActionDTO, Resource, ResourceBundle } from "@takes-a-village/shared";
import { usePlayerName } from "../../hooks/usePlayerName";
import TradeCard, { renderItems } from "../trading/TradeCard";
import ShippingWindow from "../trading/ShippingWindow";
import styles from "./TradeDesk.module.css";
import ResourceStepper from "../ResourceStepper"; // <-- Import the new stepper

interface Props {
  state: GameStateDTO;
  onDraftTrade: (targetId: string, offerItems: Partial<ResourceBundle>, requestItems: Partial<ResourceBundle>) => void;
  onCounterTrade: (actionId: string, offerItems: Partial<ResourceBundle>, requestItems: Partial<ResourceBundle>) => void;
  onAcceptTrade: (actionId: string) => void;
  onDenyTrade: (actionId: string) => void;
  onCancelTrade: (actionId: string) => void;
  onFinalizeTrade: (actionId: string, actualItems: Partial<ResourceBundle>) => void;
}

const TradeDesk: React.FC<Props> = ({ state, onDraftTrade, onCounterTrade, onAcceptTrade, onDenyTrade, onCancelTrade, onFinalizeTrade }) => {
  const { me, player_list } = state;
  const getPlayerName = usePlayerName();

  const [targetId, setTargetId] = useState<string | null>(null);
  const [draftGiveItems, setDraftGiveItems] = useState<Partial<ResourceBundle>>({});
  const [draftReqItems, setDraftReqItems] = useState<Partial<ResourceBundle>>({});

  const tradeActions = (me.actions || []).filter((a): a is TradeActionDTO => a.type === "TRADE" || a.type === "BARTER");
  const incomingTrades = tradeActions.filter(t => t.status === "PENDING" && t.waiting_on_id === me.id);
  const outgoingTrades = tradeActions.filter(t => t.status === "PENDING" && t.waiting_on_id !== me.id);
  const acceptedTrades = tradeActions.filter(t => t.status === "ACCEPTED");
  const otherPlayers = player_list.filter(p => p.id !== me.id);

  const handleDraftTrade = () => {
    if (!targetId) return;
    onDraftTrade(targetId, draftGiveItems, draftReqItems);
    setTargetId(null);
    setDraftGiveItems({});
    setDraftReqItems({});
  };

  return (
    <div className={`card ${styles.column}`} >
      <h3 className={styles.header}>Trade Desk</h3>

      {/* --- TOP ROW: DRAFTING & HISTORY --- */}
      <div className={styles.row5}>

        {/* LEFT: Drafting Tray (Flex 2 takes up more room) */}
        <div className={styles.panel18}>
          <strong className={styles.label7}>Draft New Trade</strong>
          <div className={styles.row4}>
            {otherPlayers.map(p => (
              <button
                key={p.id}
                className={[
                  "btn-user",
                  styles.button3,
                  targetId === p.id ? styles.buttonSelected : "",
                ].filter(Boolean).join(" ")}
                onClick={() => setTargetId(targetId === p.id ? null : p.id)}
              >
                {p.name}
              </button>
            ))}
          </div>

          {targetId && (
            <div className={styles.panel17}>
              <div className={styles.row3}>
                <div className={styles.panel16}>
                  <strong className={styles.label6}>I Give:</strong>
                  {(["food", "wood", "iron"] as Resource[]).map(res => (
                    <ResourceStepper
                      key={res}
                      resource={res}
                      value={draftGiveItems[res] || 0}
                      onChange={(val) => setDraftGiveItems({ ...draftGiveItems, [res]: val })}
                    />
                  ))}
                </div>

                <div className={styles.panel15}>
                  <strong className={styles.label5}>I Want:</strong>
                  {(["food", "wood", "iron"] as Resource[]).map(res => (
                    <ResourceStepper
                      key={res}
                      resource={res}
                      value={draftReqItems[res] || 0}
                      onChange={(val) => setDraftReqItems({ ...draftReqItems, [res]: val })}
                    />
                  ))}
                </div>
              </div>

              <div className={styles.panel14}>
                <button className={`btn ${styles.button2}`}  onClick={handleDraftTrade}>
                  Send Trade Offer
                </button>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Trade History (Flex 1) */}
        <div className={styles.panel13}>
          <strong className={styles.label4}>
            Recent Trades
          </strong>
          {(me.trade_history || []).length === 0 && <div className={styles.panel12}>No recent trades</div>}
          {(me.trade_history || []).slice().reverse().map((trade) => (
            <div key={trade.id} className={styles.panel11}>
              <div className={styles.panel10}>With {getPlayerName(trade.target_id)}</div>
              <div className={styles.panel9}><strong>Offered:</strong> <div>{renderItems(trade.offered)}</div></div>
              <div className={styles.panel8}><strong>Requested:</strong> <div>{renderItems(trade.requested)}</div></div>
              <div className={styles.panel7}>
                <div className={styles.panel6}><strong>Sent:</strong> <div>{renderItems(trade.actual_sent)}</div></div>
                <div><strong>Received:</strong> <div>{renderItems(trade.actual_received)}</div></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <hr className={styles.hr} />

      {/* --- MIDDLE ROW: INBOX & OUTBOX --- */}
      <div className={styles.row2}>

        {/* INBOX */}
        <div className={styles.panel5}>
          <strong className={styles.label3}>
            Inbox ({incomingTrades.length})
          </strong>
          {incomingTrades.map(trade => (
            <TradeCard key={trade.id} trade={trade} meId={me.id} getPlayerName={getPlayerName} onAccept={onAcceptTrade} onDeny={onDenyTrade} onCounterTrade={onCounterTrade} />
          ))}
        </div>

        {/* OUTBOX */}
        <div className={styles.panel4}>
          <strong className={styles.label2}>
            Awaiting Reply ({outgoingTrades.length})
          </strong>
          {outgoingTrades.map(trade => {
            const isInitiator = me.id === trade.initiator_id;
            const otherPersonId = isInitiator ? trade.target_id : trade.initiator_id;
            const iGive = isInitiator ? trade.offer_items : trade.request_items;
            const iWant = isInitiator ? trade.request_items : trade.offer_items;
            return (
              <div key={trade.id} className={styles.panel3}>
                <div className={styles.row}>
                  <strong>To: {getPlayerName(otherPersonId || "")}</strong>
                  <button className={`btn-tooltip danger ${styles.button}`}  onClick={() => onCancelTrade(trade.id)}>Revoke</button>
                </div>
                <div className={styles.panel2}>
                  <div>I Give: {renderItems(iGive)}</div>
                  <div>I Want: {renderItems(iWant)}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* --- BOTTOM ROW: SHIPPING BAY --- */}
      {acceptedTrades.length > 0 && (
        <div className={styles.panel}>
          <strong className={styles.label}>
            Shipping Bay (Lock-in your payload)
          </strong>
          {acceptedTrades.map(trade => (
            <ShippingWindow key={trade.id} trade={trade} meId={me.id} onFinalizeTrade={onFinalizeTrade} getPlayerName={getPlayerName} />
          ))}
        </div>
      )}
    </div>
  );
};

export default TradeDesk;
