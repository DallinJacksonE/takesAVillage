import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import io from 'socket.io-client';

// Connect to the flask service
const socket = io({
  path: '/socket.io', // Standard path for socket.io
  transports: ['websocket', 'polling'] // Force stable transports
});

function Gameplay() {
  const { gameId } = useParams(); // Assumes route is /game/:gameId
  const [gameState, setGameState] = useState(null);
  const [playerCount, setPlayerCount] = useState(0);
  const [userId, setUserId] = useState(null); // In reality, read from cookie

  useEffect(() => {
    // 1. Get User ID (Mocking cookie read)
    const getCookie = (name) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
    };
    const uid = getCookie('user_session') || "anon";
    setUserId(uid);

    // 2. Connect to Room
    socket.emit('join_room', { gameId: gameId, userId: uid });

    // 3. Listeners
    socket.on('room_update', (data) => {
      setPlayerCount(data.player_count);
    });

    socket.on('game_state', (data) => {
      console.log("State Received:", data);
      setGameState(data);
    });

    socket.on('game_started', () => {
      // Trigger a pull of the new state
      socket.emit('request_update', { gameId, userId: uid });
    });

    return () => socket.off(); // Cleanup
  }, [gameId]);

  const handleStartGame = () => {
    socket.emit('start_game_request', { gameId, userId });
  };

  // --- WAITING ROOM ---
  if (!gameState || gameState.status === 'WAITING') {
    return (
      <div className="container" style={{ textAlign: 'center', marginTop: '50px' }}>
        <h1>Waiting for Players...</h1>
        <h2>Game ID: {gameId}</h2>
        <p>Players Joined: {playerCount}</p>

        {/* Only show Start button if Host (logic handled in backend, but visually here) */}
        {gameState && gameState.is_host && (
          <button className="btn" onClick={handleStartGame}>
            Start Game
          </button>
        )}
      </div>
    );
  }

  // --- MAIN HUD ---
  const { me, day, phase } = gameState;

  return (
    <div className="container">
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #333', paddingBottom: '10px' }}>
        <h2>Day {day}</h2>
        <h2 style={{ color: '#2e7d32' }}>Phase: {phase}</h2>
      </div>

      <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>

        {/* Left Col: Resources & Health */}
        <div className="card" style={{ flex: 1 }}>
          <h3>My Resources</h3>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li>🔥 Fire: {me.resources.fire}</li>
            <li>🍖 Food: {me.resources.food}</li>
            <li>⛏️ Ferrous: {me.resources.ferrous}</li>
          </ul>

          <hr />

          <h3>Health Status</h3>
          <p>State: <strong>{me.health.toUpperCase()}</strong></p>
          <p>Sickness Chance: {(me.sickness_chance * 100).toFixed(0)}%</p>
        </div>

        {/* Middle Col: Developments */}
        <div className="card" style={{ flex: 1 }}>
          <h3>Developments</h3>
          {me.developments.length === 0 ? <p>No developments yet.</p> : (
            me.developments.map((dev, idx) => (
              <div key={idx} style={{ background: '#eee', padding: '10px', marginBottom: '10px' }}>
                <strong>{dev.type} (Lvl {dev.level})</strong>
                <div style={{ fontSize: '0.8rem' }}>Maint: {dev.maintenance_days} days</div>
              </div>
            ))
          )}
        </div>

        {/* Right Col: Sentiments */}
        <div className="card" style={{ flex: 1 }}>
          <h3>Social Sentiments</h3>
          <p style={{ fontSize: '0.8rem', color: '#666' }}>Your opinion of others (-2 to 2)</p>
          {Object.keys(me.sentiments).length === 0 ? <p>No interactions yet.</p> : (
            <ul>
              {Object.entries(me.sentiments).map(([pid, score]) => (
                <li key={pid}>Player {pid.substring(0, 4)}... : <strong>{score}</strong></li>
              ))}
            </ul>
          )}
        </div>

      </div>
    </div>
  );
}

export default Gameplay;
