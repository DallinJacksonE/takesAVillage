import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import io from 'socket.io-client';

// Import UI Components
import StatusCards from './gameUIComponents/StatusCards';
import VillageMap from './gameUIComponents/VillageMap';
import MessageBoard from './gameUIComponents/MessageBoard';

// Connect to current host, Vite proxies /socket.io automatically
const socket = io({
  path: '/socket.io',
  transports: ['websocket', 'polling']
});

function Gameplay() {
  const { gameId } = useParams();
  const [gameState, setGameState] = useState(null);
  const [userId, setUserId] = useState(null);
  const [playerCount, setPlayerCount] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);

  // --- 1. Connection & Game State Management ---
  useEffect(() => {
    // A. Get User ID from Cookie
    const getCookie = (name) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
    };
    const uid = getCookie('user_session') || "anon";
    setUserId(uid);

    // B. Join Room
    socket.emit('join_room', { gameId: gameId, userId: uid });

    // C. Define Listeners
    socket.on('room_update', (data) => {
      setPlayerCount(data.player_count);
    });

    socket.on('game_state', (data) => {
      console.log("State Updated:", data);
      setGameState(data);
      setTimeLeft(data.time_remaining); // <--- Add this line
    });
    socket.on('game_started', () => {
      // Trigger a refresh when the game actually starts
      socket.emit('request_update', { gameId, userId: uid });
    });

    socket.on('error', (data) => {
      alert(data.message);
    });

    // Cleanup listeners on unmount
    return () => socket.off();
  }, [gameId]);

  // --- Timer Stuff ---
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prevTime) => (prevTime > 0 ? prevTime - 1 : 0));
    }, 1000);

    // Cleanup interval on component unmount
    return () => clearInterval(timer);
  }, []);

  // --- 2. Action Handlers ---

  const handleStartGame = () => {
    socket.emit('start_game_request', { gameId, userId });
  };

  const handleSendMessage = (payload) => {
    // Payload comes from MessageBoard: { to_id, type, ...details }
    socket.emit('send_message', {
      gameId,
      userId,
      ...payload
    });
  };

  const handleUpdateMessage = (msgId, action, values = null) => {
    socket.emit('update_message', {
      gameId,
      userId,
      msgId,
      action, // 'ACCEPT', 'DENY', 'BARTER'
      values  // The new offer details if bartering
    });
  };


  // --- 3. Render Views ---

  // A. Loading State
  if (!gameState) {
    return (
      <div className="container" style={{ textAlign: 'center', marginTop: '100px', color: '#666' }}>
        <h2>Connecting to Village...</h2>
      </div>
    );
  }

  // B. Waiting Room
  if (gameState.status === 'WAITING') {
    return (
      <div className="container" style={{ textAlign: 'center', marginTop: '50px' }}>
        <h1>Waiting for Players...</h1>
        <h2>Game ID: {gameId.substring(0, 8)}</h2>
        <p>Players Joined: {playerCount}</p>

        {gameState.is_host ? (
          <button className="btn" onClick={handleStartGame}>
            Start Game
          </button>
        ) : (
          <p style={{ fontStyle: 'italic', color: '#888' }}>Waiting for host to start...</p>
        )}
      </div>
    );
  }

  // C. Main HUD
  const { me, day, phase, time_remaining } = gameState;

  return (
    <div className="container">
      {/* --- HEADER --- */}
      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #333', paddingBottom: '10px', marginBottom: '20px' }}>
        <h2>{me.name}</h2>
        <h2 style={{ color: '#2e7d32' }}>Day {day}: {phase}</h2>
        <h3 style={{ color: timeLeft < 30 ? 'red' : 'black', minWidth: '60px', textAlign: 'right' }}>
          {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
        </h3>
      </div>

      {/* --- ROW 1: STATUS CARDS (Resources, Developments, Sentiments) --- */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        <StatusCards state={me} />
      </div>

      {/* --- ROW 2: MESSAGES & COMMS --- */}
      <MessageBoard
        messages={gameState.messages || []}
        playerId={userId}
        players={gameState.player_list || []}      // Passed from backend for "To" dropdown
        myDevelopments={me.developments || []}     // Passed for Job Offer dropdown
        onSend={handleSendMessage}
        onUpdateMessage={handleUpdateMessage}
      />

      {/* --- ROW 3: PHASE CONTROLS --- */}
      {phase === 'TRADE' && (
        <div className="card" style={{ background: '#e8f5e9', textAlign: 'center', margin: '20px 0' }}>
          <button className="btn" onClick={() => socket.emit('finish_phase', { gameId })}>
            Finish Trading
          </button>
        </div>
      )}

      {phase === 'NIGHT' && (
        <div className="card" style={{ background: '#333', color: 'white', textAlign: 'center', margin: '20px 0' }}>
          <p>Eating 1 Food, Burning 1 Wood...</p>
          <button className="btn" onClick={() => socket.emit('end_day', { gameId })}>
            End Day
          </button>
        </div>
      )}

      {/* --- ROW 4: MAP --- */}
      {gameState.map && (
        <VillageMap
          mapData={gameState.map}
          players={gameState.players} // Note: VillageMap might need full player dict for names/owners
        />
      )}
    </div>
  );
}

export default Gameplay;
