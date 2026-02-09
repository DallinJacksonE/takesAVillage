import React, { useState } from 'react';

const MessageBoard = ({ messages, playerId, players, myDevelopments, onSend }) => {
  const [editingMsgId, setEditingMsgId] = useState(null);
  const [barterValues, setBarterValues] = useState({});

  // Compose State
  const [toId, setToId] = useState('');
  const [type, setType] = useState('TEXT');
  const [content, setContent] = useState('');
  const [wageOffer, setWageOffer] = useState(1);
  const [wageType, setWageType] = useState('food');
  const [devId, setDevId] = useState('');

  const handleBarterStart = (msg) => {
    setEditingMsgId(msg.id);
    if (msg.type === 'EMPLOYMENT') {
      setBarterValues({ wage_offer: msg.wage_offer, wage_type: msg.wage_type });
    } else if (msg.type === 'TRADE') {
      setBarterValues({ ...msg.offer_items });
    }
  };

  const handleSendUpdate = (msg) => {
    // Send update via the single onSend channel
    onSend({
      id: msg.id,
      action: 'BARTER',
      ...barterValues
    });
    setEditingMsgId(null);
  };

  const handleComposeSend = () => {
    if (!toId) return alert("Select a recipient");

    const payload = { to_id: toId, type: type };

    if (type === 'TEXT') {
      payload.content = content;
    } else if (type === 'EMPLOYMENT') {
      payload.wage_offer = wageOffer;
      payload.wage_type = wageType;
      payload.dev_id = devId;
    } else if (type === 'TRADE') {
      payload.offer_items = { [wageType]: wageOffer };
      payload.request_items = {};
    }

    onSend(payload);
    setContent('');
  };

  const getPlayerName = (id) => {
    const p = players.find((player) => player.id === id);
    return p ? p.name : id.substring(0, 4);
  };

  const handleAccept = (msg) => {
    // We just send the ACCEPT action. 
    // The backend detects this and triggers the WORK_DEV action automatically.
    onSend({
      id: msg.id,
      action: 'ACCEPT'
    });
  };

  const handleDeny = (msg) => {
    onSend({ id: msg.id, action: 'DENY' });
  };

  const renderMessage = (msg) => {
    const isMe = msg.from_id === playerId;
    const isEditing = editingMsgId === msg.id;

    if (msg.is_system) {
      return (
        <div key={msg.id} style={{ padding: '5px', fontSize: '0.8rem', color: '#666', textAlign: 'center', fontStyle: 'italic' }}>
          {msg.content}
        </div>
      )
    }

    let borderStyle = '1px solid #f0f0f0';
    if (msg.status === 'ACCEPTED') borderStyle = '2px solid #2e7d32';
    if (isEditing || msg.status === 'BARTERING') borderStyle = '2px solid #f57c00';
    if (msg.status === 'DENIED') borderStyle = '1px solid #ffcdd2';

    return (
      <div key={msg.id} style={{
        display: 'flex', alignItems: 'center', padding: '10px',
        borderBottom: borderStyle, background: '#fff', marginBottom: '5px'
      }}>
        <div style={{ fontWeight: 'bold', width: '100px', fontSize: '0.8rem' }}>
          {isMe ? <span>To: {getPlayerName(msg.to_id)}</span> : <span>From: {getPlayerName(msg.from_id)}</span>}
        </div>

        <div style={{ flex: 1, padding: '0 10px' }}>
          <span style={{
            fontSize: '0.7rem', padding: '2px 4px', borderRadius: '4px',
            background: '#eee', marginRight: '5px'
          }}>{msg.type}</span>

          {msg.type === 'TEXT' && <span>{msg.content}</span>}
          {msg.type === 'EMPLOYMENT' && (
            <span>Offered {msg.wage_offer} {msg.wage_type} {isMe ? 'to work' : 'for work'}</span>
          )}
          {msg.type === 'TRADE' && <span>Trade Offer</span>}

          {msg.status === 'DENIED' && <span style={{ color: 'red', marginLeft: '10px' }}>(Denied)</span>}
          {msg.status === 'ACCEPTED' && <span style={{ color: 'green', marginLeft: '10px' }}>(Accepted)</span>}
        </div>

        {!isMe && msg.status === 'PENDING' && msg.type !== 'TEXT' && !isEditing && (
          <div style={{ display: 'flex', gap: '5px' }}>
            <button className="btn-sm success" onClick={() => handleAccept(msg)}>Accept</button>
            <button className="btn-sm warning" onClick={() => handleBarterStart(msg)}>Barter</button>
            <button className="btn-sm danger" onClick={() => handleDeny(msg)}>Deny</button>
          </div>
        )}
        {isEditing && (
          <button className="btn-sm warning" onClick={() => handleSendUpdate(msg)}>Send Update</button>
        )}
      </div>
    );
  };

  return (
    <div className="card" style={{ height: '500px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px' }}>Communications</h3>

      <div style={{ flex: 1, overflowY: 'auto', background: '#fafafa', padding: '10px' }}>
        {messages && messages.length > 0 ? messages.map(renderMessage) : <p style={{ color: '#999', textAlign: 'center' }}>No messages.</p>}
      </div>

      <div style={{ borderTop: '2px solid #eee', paddingTop: '10px', marginTop: '10px' }}>
        <div style={{ display: 'flex', gap: '5px', marginBottom: '5px' }}>
          <select style={{ flex: 1, padding: '5px' }} value={toId} onChange={(e) => setToId(e.target.value)}>
            <option value="">To Player...</option>
            {players.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <select style={{ width: '120px', padding: '5px' }} value={type} onChange={(e) => setType(e.target.value)}>
            <option value="TEXT">Chat</option>
            <option value="EMPLOYMENT">Job Offer</option>
            <option value="TRADE">Trade</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: '5px' }}>
          {type === 'TEXT' && (
            <input type="text" style={{ flex: 1, padding: '5px' }} placeholder="Message..."
              value={content} onChange={(e) => setContent(e.target.value)} />
          )}

          {type === 'EMPLOYMENT' && (
            <>
              <input type="number" style={{ width: '50px' }} value={wageOffer} onChange={e => setWageOffer(e.target.value)} />
              <select value={wageType} onChange={e => setWageType(e.target.value)}>
                <option value="food">Food</option>
                <option value="wood">Wood</option>
                <option value="iron">Iron</option>
              </select>
              <select value={devId} onChange={e => setDevId(e.target.value)} style={{ flex: 1 }}>
                <option value="">Select Site...</option>
                {myDevelopments.map((d, i) => <option key={i} value={d.id || i}>{d.type} (Lvl {d.level})</option>)}
              </select>
            </>
          )}

          {type === 'TRADE' && (
            <>
              <input type="number" style={{ width: '50px' }} value={wageOffer} onChange={e => setWageOffer(e.target.value)} />
              <select value={wageType} onChange={e => setWageType(e.target.value)}>
                <option value="food">Food</option>
                <option value="wood">Wood</option>
              </select>
              <span style={{ fontSize: '0.8rem', alignSelf: 'center' }}>to offer</span>
            </>
          )}

          <button className="btn" style={{ padding: '5px 15px' }} onClick={handleComposeSend}>Send</button>
        </div>
      </div>
    </div>
  );
};

export default MessageBoard;
