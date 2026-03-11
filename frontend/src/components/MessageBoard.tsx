import React, { useState } from 'react';
import { Message, Player, Development } from '../types/game';

type MessageType = 'TEXT' | 'TRADE' | 'EMPLOYMENT';

interface Props {
  phase: 'WORK' | 'TRADE' | 'NIGHT';
  messages: Message[];
  playerId: string;
  players: Player[];
  myDevelopments: Development[];
  onSend: (payload: Partial<Message> & { action?: string }) => void;
}

interface BarterState {
  wage_offer?: number;
  wage_type?: string;
  dev_id?: string;
  offer_amount?: number;
  offer_type?: string;
  gain_amount?: number;
  gain_type?: string;
}

const MessageBoard: React.FC<Props> = ({ phase, messages, playerId, players, myDevelopments, onSend }) => {
  const [editingMsgId, setEditingMsgId] = useState<string | null>(null);
  const [barterValues, setBarterValues] = useState<BarterState>({});

  // Compose State
  const [toId, setToId] = useState('');
  const [type, setType] = useState<MessageType>('TEXT');
  const [content, setContent] = useState('');

  // Compose: Trade/Job Defaults
  const [offerAmount, setOfferAmount] = useState(1);
  const [offerType, setOfferType] = useState('food');
  const [gainAmount, setGainAmount] = useState(1);
  const [gainType, setGainType] = useState('wood');
  const [wageOffer, setWageOffer] = useState(1);
  const [wageType, setWageType] = useState('wood');
  const [devId, setDevId] = useState('');

  // --- Helpers ---

  const getFirstItem = (itemsDict: Record<string, number> | undefined) => {
    if (!itemsDict) return { type: 'food', amount: 0 };
    const key = Object.keys(itemsDict)[0];
    return { type: key, amount: itemsDict[key] };
  };

  const getPlayerName = (id: string) => {
    const p = players.find((player) => player.id === id);
    return p ? p.name : id.substring(0, 4);
  };

  // --- Handlers ---

  const handleBarterStart = (msg: Message) => {
    setEditingMsgId(msg.id);

    if (msg.type === 'EMPLOYMENT') {
      setBarterValues({
        wage_offer: msg.wage_offer,
        wage_type: msg.wage_type,
        dev_id: msg.dev_id
      });
    } else if (msg.type === 'TRADE') {
      const offer = getFirstItem(msg.offer_items);
      const req = getFirstItem(msg.request_items);

      setBarterValues({
        offer_amount: offer.amount,
        offer_type: offer.type,
        gain_amount: req.amount,
        gain_type: req.type
      });
    }
  };

  const handleSendUpdate = (msg: Message) => {
    const payload: Partial<Message> & { action: string } = {
      id: msg.id,
      action: 'BARTER',
      from_id: playerId
    };

    if (msg.type === 'EMPLOYMENT') {
      payload.wage_offer = parseInt(String(barterValues.wage_offer));
      payload.wage_type = barterValues.wage_type;
    } else if (msg.type === 'TRADE') {
      payload.offer_items = { [barterValues.offer_type!]: parseInt(String(barterValues.offer_amount)) };
      payload.request_items = { [barterValues.gain_type!]: parseInt(String(barterValues.gain_amount)) };
    }

    onSend(payload);
    setEditingMsgId(null);
  };

  const handleComposeSend = () => {
    if (!toId) return alert("Select a recipient");

    const payload: Partial<Message> = {
      to_id: toId,
      from_id: playerId,
      type: type
    };

    if (type === 'TEXT') {
      payload.content = content;
    } else if (type === 'EMPLOYMENT') {
      payload.wage_offer = parseInt(String(wageOffer));
      payload.wage_type = wageType;
      payload.dev_id = devId;
    } else if (type === 'TRADE') {
      payload.offer_items = { [offerType]: parseInt(String(offerAmount)) };
      payload.request_items = { [gainType]: parseInt(String(gainAmount)) };
    }

    onSend(payload);
    setContent('');
  };

  // --- Renderers ---

  const renderMessage = (msg: Message) => {
    const isMe = msg.from_id === playerId;
    const isEditing = editingMsgId === msg.id;

    const showActions = msg.type !== 'TEXT' && !isEditing && (
      (!isMe && msg.status === 'PENDING') ||
      (msg.status === 'BARTERING')
    );

    if (msg.is_system) {
      return (
        <div key={msg.id} style={{ textAlign: 'center', fontStyle: 'italic', color: '#666', margin: '5px 0', fontSize: '0.8rem' }}>
          {msg.content}
        </div>
      );
    }

    let displayOffer: string, displayRequest: string;
    if (msg.type === 'TRADE') {
      const o = getFirstItem(msg.offer_items);
      const r = getFirstItem(msg.request_items);
      displayOffer = `${o.amount} ${o.type}`;
      displayRequest = `${r.amount} ${r.type}`;
    }

    const inputStyle = { width: '70px', padding: '4px', marginRight: '4px' };
    const selectStyle = { padding: '4px', marginRight: '4px' };

    return (
      <div key={msg.id} className="message-card" style={{
        border: isEditing ? '2px solid #2196F3' : '1px solid #ddd',
        padding: '10px', marginBottom: '8px', borderRadius: '6px', background: '#fff',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '8px', color: '#555' }}>
          <span style={{ fontWeight: 'bold' }}>
            {isMe ? `To: ${getPlayerName(msg.to_id)}` : `From: ${getPlayerName(msg.from_id)}`}
          </span>
          <span style={{
            background: msg.status === 'ACCEPTED' ? '#e8f5e9' : msg.status === 'DENIED' ? '#ffebee' : msg.status === 'BARTERING' ? '#fff3e0' : '#e3f2fd',
            padding: '2px 6px', borderRadius: '4px', textTransform: 'uppercase', fontSize: '0.7rem'
          }}>
            {msg.status}
          </span>
        </div>

        <div style={{ padding: '5px 0', fontSize: '0.9rem' }}>
          {isEditing ? (
            <div style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
              {msg.type === 'EMPLOYMENT' && (
                <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                  <span>Offer:</span>
                  <input type="number" style={inputStyle} value={barterValues.wage_offer}
                    onChange={e => setBarterValues({ ...barterValues, wage_offer: Number(e.target.value) })} />
                  <select style={selectStyle} value={barterValues.wage_type} onChange={e => setBarterValues({ ...barterValues, wage_type: e.target.value })}>
                    <option value="food">Food</option><option value="wood">Wood</option><option value="iron">Iron</option>
                  </select>
                </div>
              )}
              {msg.type === 'TRADE' && (
                <div style={{ display: 'flex', gap: '5px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <span>Give</span>
                  <input type="number" style={inputStyle} value={barterValues.offer_amount}
                    onChange={e => setBarterValues({ ...barterValues, offer_amount: Number(e.target.value) })} />
                  <select style={selectStyle} value={barterValues.offer_type} onChange={e => setBarterValues({ ...barterValues, offer_type: e.target.value })}>
                    <option value="food">Food</option><option value="wood">Wood</option><option value="iron">Iron</option>
                  </select>
                  <span>for</span>
                  <input type="number" style={inputStyle} value={barterValues.gain_amount}
                    onChange={e => setBarterValues({ ...barterValues, gain_amount: Number(e.target.value) })} />
                  <select style={selectStyle} value={barterValues.gain_type} onChange={e => setBarterValues({ ...barterValues, gain_type: e.target.value })}>
                    <option value="food">Food</option><option value="wood">Wood</option><option value="iron">Iron</option>
                  </select>
                </div>
              )}
            </div>
          ) : (
            <div>
              {msg.type === 'TEXT' && <span>{msg.content}</span>}
              {msg.type === 'EMPLOYMENT' && <span><strong>Job:</strong> Work for {msg.wage_offer} {msg.wage_type}</span>}
              {msg.type === 'TRADE' && <span><strong>Trade:</strong> {displayOffer!} ↔ {displayRequest!}</span>}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
          {showActions && (
            <>
              <button className="btn-sm success" onClick={() => onSend({ id: msg.id, action: 'ACCEPT' })}>Accept</button>
              <button className="btn-sm warning" onClick={() => handleBarterStart(msg)}>Counter Offer</button>
              <button className="btn-sm danger" onClick={() => onSend({ id: msg.id, action: 'DENY' })}>Deny</button>
            </>
          )}
          {isEditing && (
            <>
              <button className="btn-sm success" onClick={() => handleSendUpdate(msg)}>Send Offer</button>
              <button className="btn-sm" onClick={() => setEditingMsgId(null)}>Cancel</button>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="card" style={{ height: '550px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px', margin: '0 0 10px 0' }}>Communications</h3>

      <div style={{ flex: 1, overflowY: 'auto', background: '#fafafa', padding: '10px', borderRadius: '4px', border: '1px solid #eee' }}>
        {messages?.length > 0 ? messages.map(renderMessage) : <p style={{ textAlign: 'center', color: '#999' }}>No messages.</p>}
      </div>

      <div style={{ borderTop: '2px solid #eee', padding: '10px 0 0 0', marginTop: '10px' }}>
        <div style={{ display: 'flex', gap: '5px', marginBottom: '8px' }}>
          <select style={{ flex: 1 }} value={toId} onChange={(e) => setToId(e.target.value)}>
            <option value="">To Player...</option>
            {players.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <select value={type} onChange={(e) => setType(e.target.value as MessageType)}>
            <option value="TEXT">Chat</option>
            {phase === 'WORK' && <option value="EMPLOYMENT">Job Offer</option>}
            {phase === 'TRADE' && <option value="TRADE">Trade</option>}
          </select>
        </div>

        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
          {type === 'TEXT' && <input style={{ flex: 1 }} value={content} onChange={e => setContent(e.target.value)} placeholder="Message..." />}

          {type === 'EMPLOYMENT' && (
            <>
              <input type="number" style={{ width: '70px' }} value={wageOffer} onChange={e => setWageOffer(Number(e.target.value))} />
              <select value={wageType} onChange={e => setWageType(e.target.value)}>
                <option value="food">Food</option><option value="wood">Wood</option><option value="iron">Iron</option>
              </select>
              <select style={{ flex: 1 }} value={devId} onChange={e => setDevId(e.target.value)}>
                <option value="">Site...</option>
                {myDevelopments.map((d, i) => <option key={i} value={d.id}>{d.type} ({d.level})</option>)}
              </select>
            </>
          )}

          {type === 'TRADE' && (
            <>
              <input type="number" style={{ width: '70px' }} value={offerAmount} onChange={e => setOfferAmount(Number(e.target.value))} />
              <select value={offerType} onChange={e => setOfferType(e.target.value)}>
                <option value="food">Food</option><option value="wood">Wood</option><option value="iron">Iron</option>
              </select>
              <span>for</span>
              <input type="number" style={{ width: '70px' }} value={gainAmount} onChange={e => setGainAmount(Number(e.target.value))} />
              <select value={gainType} onChange={e => setGainType(e.target.value)}>
                <option value="food">Food</option><option value="wood">Wood</option><option value="iron">Iron</option>
              </select>
            </>
          )}

          <button className="btn" onClick={handleComposeSend}>Send</button>
        </div>
      </div>
    </div>
  );
};

export default MessageBoard;
