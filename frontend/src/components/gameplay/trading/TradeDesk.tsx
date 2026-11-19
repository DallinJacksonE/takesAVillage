import React, { useState } from "react";
import { GameStateDTO, TradeActionDTO, Resource, ResourceBundle } from "../../../dtos/index";
import { usePlayerName } from "../../hooks/usePlayerName";
import ResourceStepper from "../ResourceStepper";
import TradeCard, { renderItems } from "./TradeCard";
import ShippingWindow from "./ShippingWindow";
import styles from "./TradeDesk.module.css";

const TRADE_RESOURCES: Resource[] = ["food", "wood", "iron"];

const PUBLIC_STATUS_LABELS = {
  PENDING: "Negotiating",
  ACCEPTED: "Accepted",
  FINALIZED: "Completed",
  DENIED: "Declined",
  EXPIRED: "Expired",
} as const;

export interface TradeDeskProps {
  state: GameStateDTO;
  onDraftTrade: (
    targetId: string,
    offerItems: Partial<ResourceBundle>,
    requestItems: Partial<ResourceBundle>,
  ) => void;
  onCounterTrade: (
    actionId: string,
    offerItems: Partial<ResourceBundle>,
    requestItems: Partial<ResourceBundle>,
  ) => void;
  onAcceptTrade: (actionId: string) => void;
  onDenyTrade: (actionId: string) => void;
  onCancelTrade: (actionId: string) => void;
  onFinalizeTrade: (actionId: string, actualItems: Partial<ResourceBundle>) => void;
}

export const TradeDesk: React.FC<TradeDeskProps> = ({
  state,
  onDraftTrade,
  onCounterTrade,
  onAcceptTrade,
  onDenyTrade,
  onCancelTrade,
  onFinalizeTrade,
}) => {
  const { me, player_list } = state;
  const getPlayerName = usePlayerName();

  const [targetId, setTargetId] = useState<string | null>(null);
  const [draftGiveItems, setDraftGiveItems] = useState<Partial<ResourceBundle>>({});
  const [draftReqItems, setDraftReqItems] = useState<Partial<ResourceBundle>>({});

  const tradeActions = (me.actions || []).filter(
    (action): action is TradeActionDTO => action.type === "TRADE" || action.type === "BARTER",
  );
  const incomingTrades = tradeActions.filter(
    (trade) => trade.status === "PENDING" && trade.waiting_on_id === me.id,
  );
  const outgoingTrades = tradeActions.filter(
    (trade) => trade.status === "PENDING" && trade.waiting_on_id !== me.id,
  );
  const acceptedTrades = tradeActions.filter((trade) => trade.status === "ACCEPTED");
  const otherPlayers = player_list.filter((player) => player.id !== me.id);
  const thirdPartyTrades = (state.public_interactions || []).filter(
    (interaction) =>
      interaction.kind === "TRADE" && !interaction.participant_ids.includes(me.id),
  );

  const handleDraftTrade = () => {
    if (!targetId) return;
    onDraftTrade(targetId, draftGiveItems, draftReqItems);
    setTargetId(null);
    setDraftGiveItems({});
    setDraftReqItems({});
  };

  return (
    <div className={`card ${styles.tradeDeskContainer}`}>
      <h3 className={styles.tradeDeskTitle}>Trade Desk</h3>

      {thirdPartyTrades.length > 0 && (
        <div className={styles.sidebarSection}>
          <strong className={styles.sidebarTitle}>Village Activity</strong>
          {thirdPartyTrades.map((interaction) => (
            <div key={interaction.id} className={styles.mutedText}>
              <div>
                {getPlayerName(interaction.participant_ids[0])}
                {" ↔ "}
                {getPlayerName(interaction.participant_ids[1])}
              </div>
              <strong>{PUBLIC_STATUS_LABELS[interaction.status]}</strong>
            </div>
          ))}
        </div>
      )}

      {/* --- TOP ROW: DRAFTING & HISTORY --- */}
      <div className={styles.topRow}>
        {/* LEFT: Drafting Tray */}
        <div className={styles.draftSection}>
          <strong className={styles.draftSectionTitle}>Draft New Trade</strong>
          <div className={styles.partnerSelectRow}>
            {otherPlayers.map((player) => (
              <button
                key={player.id}
                className={[
                  "btn-user",
                  styles.partnerButton,
                  targetId === player.id ? styles.partnerButtonSelected : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => setTargetId(targetId === player.id ? null : player.id)}
              >
                {player.name}
              </button>
            ))}
          </div>

          {targetId && (
            <div className={styles.draftDetailsCard}>
              <div className={styles.draftColumns}>
                <div className={styles.resourceColumn}>
                  <strong className={styles.giveLabel}>I Give:</strong>
                  {TRADE_RESOURCES.map((res) => (
                    <ResourceStepper
                      key={res}
                      resource={res}
                      value={draftGiveItems[res] || 0}
                      onChange={(val) => setDraftGiveItems({ ...draftGiveItems, [res]: val })}
                    />
                  ))}
                </div>

                <div className={styles.resourceColumn}>
                  <strong className={styles.wantLabel}>I Want:</strong>
                  {TRADE_RESOURCES.map((res) => (
                    <ResourceStepper
                      key={res}
                      resource={res}
                      value={draftReqItems[res] || 0}
                      onChange={(val) => setDraftReqItems({ ...draftReqItems, [res]: val })}
                    />
                  ))}
                </div>
              </div>

              <div className={styles.sendOfferWrapper}>
                <button className={`btn ${styles.sendOfferButton}`} onClick={handleDraftTrade}>
                  Send Trade Offer
                </button>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Trade History */}
        <div className={styles.sidebarSection}>
          <strong className={styles.sidebarTitle}>Recent Trades</strong>
          {(me.trade_history || []).length === 0 && (
            <div className={styles.mutedText}>No recent trades</div>
          )}
          {(me.trade_history || [])
            .slice()
            .reverse()
            .map((trade) => (
              <div key={trade.id} className={styles.historyCard}>
                <div className={styles.historyPartner}>With {getPlayerName(trade.target_id)}</div>
                <div className={styles.historyRow}>
                  <strong>Offered:</strong> <div>{renderItems(trade.offered)}</div>
                </div>
                <div className={styles.historyRow}>
                  <strong>Requested:</strong> <div>{renderItems(trade.requested)}</div>
                </div>
                <div className={styles.actualTransfersSection}>
                  <div className={styles.historyRow}>
                    <strong>Sent:</strong> <div>{renderItems(trade.actual_sent)}</div>
                  </div>
                  <div>
                    <strong>Received:</strong> <div>{renderItems(trade.actual_received)}</div>
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>

      <hr className={styles.divider} />

      {/* --- MIDDLE ROW: INBOX & OUTBOX --- */}
      <div className={styles.inboxOutboxRow}>
        {/* INBOX */}
        <div className={styles.tradeQueueColumn}>
          <strong className={styles.inboxTitle}>
            Inbox ({incomingTrades.length})
          </strong>
          {incomingTrades.map((trade) => (
            <TradeCard
              key={trade.id}
              trade={trade}
              meId={me.id}
              getPlayerName={getPlayerName}
              onAccept={onAcceptTrade}
              onDeny={onDenyTrade}
              onCounterTrade={onCounterTrade}
            />
          ))}
        </div>

        {/* OUTBOX */}
        <div className={styles.tradeQueueColumn}>
          <strong className={styles.outboxTitle}>
            Awaiting Reply ({outgoingTrades.length})
          </strong>
          {outgoingTrades.map((trade) => {
            const isInitiator = me.id === trade.initiator_id;
            const otherPersonId = isInitiator ? trade.target_id : trade.initiator_id;
            const iGive = isInitiator ? trade.offer_items : trade.request_items;
            const iWant = isInitiator ? trade.request_items : trade.offer_items;
            return (
              <div key={trade.id} className={styles.outboxCard}>
                <div className={styles.outboxHeader}>
                  <strong>To: {getPlayerName(otherPersonId || "")}</strong>
                  <button
                    className={`btn-tooltip danger ${styles.revokeButton}`}
                    onClick={() => onCancelTrade(trade.id)}
                  >
                    Revoke
                  </button>
                </div>
                <div className={styles.outboxDetails}>
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
        <div className={styles.shippingBaySection}>
          <strong className={styles.shippingBayTitle}>
            Shipping Bay (Lock-in your payload)
          </strong>
          {acceptedTrades.map((trade) => (
            <div key={trade.id} id={`action-item-${trade.id}`}>
              <ShippingWindow
                trade={trade}
                meId={me.id}
                onFinalizeTrade={onFinalizeTrade}
                getPlayerName={getPlayerName}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TradeDesk;
