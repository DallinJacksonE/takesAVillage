

const StatusCards = (state) => {
  // console.log(state.state);
  const me = state.state;
  return (
    <>
      {/* Left Col: Resources & Health */}
      <div className="card" style={{ flex: 1 }}>
        <h3>My Resources</h3>
        <ul style={{ listStyle: 'none', padding: 0, lineHeight: '1.8' }}>
          <li>🪵 Wood: <strong>{me.resources.wood}</strong></li>
          <li>🍖 Food: <strong>{me.resources.food}</strong></li>
          <li>⛏️ Iron: <strong>{me.resources.iron}</strong></li>
        </ul>
        <hr style={{ margin: '15px 0', borderTop: '1px solid #eee' }} />
        <h3>Health Status</h3>
        <p>State: <strong style={{ color: me.health === 'healthy' ? '#2e7d32' : '#c62828' }}>{me.health.toUpperCase()}</strong></p>
        <p>Sickness Chance: {(me.sickness_chance * 100).toFixed(0)}%</p>
      </div>

      {/* Middle Col: Developments */}
      <div className="card" style={{ flex: 1 }}>
        <h3>Developments</h3>
        {me.developments.length === 0 ? <p style={{ color: '#888', fontStyle: 'italic' }}>No developments yet.</p> : (
          me.developments.map((dev, idx) => (
            <div key={idx} style={{ background: '#f9f9f9', padding: '10px', marginBottom: '10px', borderRadius: '4px', border: '1px solid #eee' }}>
              <strong>{dev.type} (Lvl {dev.level})</strong>
              <div style={{ fontSize: '0.85rem', color: '#555', marginTop: '5px' }}>Maint: {dev.maintenance_days} days remaining</div>
            </div>
          ))
        )}
      </div>

      {/* Right Col: Sentiments */}
      <div className="card" style={{ flex: 1 }}>
        <h3>Social Sentiments</h3>
        <p style={{ fontSize: '0.8rem', color: '#666' }}>Your opinion of others (-2 to 2)</p>
        {Object.keys(me.sentiments).length === 0 ? <p style={{ color: '#888', fontStyle: 'italic' }}>No interactions yet.</p> : (
          <ul style={{ paddingLeft: '20px' }}>
            {Object.entries(me.sentiments).map(([pid, score]) => (
              <li key={pid} style={{ marginBottom: '5px' }}>
                Player {pid.substring(0, 4)}... : <strong style={{ color: score > 0 ? '#2e7d32' : score < 0 ? '#c62828' : '#555' }}>{score}</strong>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}

export default StatusCards;
