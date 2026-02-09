

const StatusCards = ({ state, onAction }) => {

  if (!state || !state.me) return null;

  const { me, day, phase, time_remaining, map } = state;

  const getPlayerName = (id) => {
    const p = state.player_list.find((player) => player.id === id);
    return p ? p.name : me.name; // If Id is not in list, then the development is likely the users
  };

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

      {/* Right Col: Available Work */}
      <div className="card" style={{ flex: 1 }}>
        <h3>Available Work</h3>
        <p style={{ fontSize: '0.8rem', color: '#666' }}>Sites you can work today</p>

        {!me.available_work || me.available_work.length === 0 ? (
          <p style={{ color: '#888', fontStyle: 'italic' }}>No work available.</p>
        ) : (
          <ul style={{ paddingLeft: '20px' }}>
            {me.available_work.map((devId) => {
              // 1. Find the tile safely
              const tile = map.find(t => t.id === devId);

              // 2. Handle missing tiles (e.g., if map hasn't loaded yet)
              if (!tile) return null;

              return (
                <li key={devId} style={{ marginBottom: '5px', display: 'flex', justifyContent: 'space-between' }}>
                  <span>
                    <strong>{tile.type}</strong> <span style={{ fontSize: '0.8em', color: '#666' }}>({getPlayerName(tile.owner_id)})</span>
                  </span>

                  {/* Work Button */}
                  {phase === 'WORK' && !me.finished_phase && (
                    <button
                      className="btn-sm success"
                      style={{ marginLeft: '10px', padding: '2px 8px', fontSize: '0.7rem' }}
                      onClick={() => onAction('WORK_DEV', { dev_id: devId })}
                    >
                      Work
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </>
  );
}

export default StatusCards;
