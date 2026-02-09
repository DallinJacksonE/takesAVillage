import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import io from 'socket.io-client';
import StatusCards from './gameUIComponents/StatusCards';
import VillageMap from './gameUIComponents/VillageMap';
import MessageBoard from './gameUIComponents/MessageBoard';

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

  useEffect(() => {
    const getCookie = (name) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
    };
    const uid = getCookie('user_session') || "anon";
    setUserId(uid);

    socket.emit('join_room', { gameId: gameId, userId: uid });

    socket.on('room_update', (data) => setPlayerCount(data.player_count));
    socket.on('game_state', (data) => {
      setGameState(data);
      setTimeLeft(data.time_remaining);
    });
    socket.on('game_started', () => socket.emit('request_update', { gameId, userId: uid }));
    socket.on('error', (data) => alert(data.message));

    return () => socket.off();
  }, [gameId]);

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prevTime) => (prevTime > 0 ? prevTime - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleStartGame = () => socket.emit('start_game_request', { gameId, userId });

  // UNIFIED HANDLER for new messages and updates
  const handleSendMessage = (payload) => {
    const message = {
      from_id: userId,
      gameId,
      ...payload
    }
    socket.emit('send_message', message);
  };

  const handleUserAction = (action, payload) => {
    socket.emit('user_action', { gameId, userId, action, payload });
  };

  if (!gameState) return <div>Connecting...</div>;

  if (gameState.status === 'WAITING') {
    return (
      <div className="container" style={{ textAlign: 'center', marginTop: '50px' }}>
        <h1>Waiting for Players...</h1>
        <h2>Game ID: {gameId}</h2>
        <p>Players: {playerCount}</p>
        {gameState.is_host && <button className="btn" onClick={handleStartGame}>Start Game</button>}
      </div>
    );
  }

  const { me, day, phase } = gameState;

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #333', paddingBottom: '10px', marginBottom: '20px' }}>
        <h2>{me.name}</h2>
        <h2 style={{ color: '#2e7d32' }}>Day {day}: {phase}</h2>
        <h3>{Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}</h3>
      </div>

      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        <StatusCards
          state={gameState}
          players={gameState.player_list}
          map={gameState.map}
          onAction={handleUserAction}
        />
      </div>

      <MessageBoard
        messages={gameState.messages || []}
        playerId={userId}
        players={gameState.player_list || []}
        myDevelopments={me.developments || []}
        onSend={handleSendMessage}
      />

      {phase === 'TRADE' && (
        <>
          {/* IF condition is true, show Button A, ELSE show Button B */}
          {!me.finished_phase ? (
            <div className="card" style={{ background: '#D4ECD6', textAlign: 'center', margin: '20px 0' }}>
              <button className="btn" onClick={() => handleUserAction('FINISH_PHASE')}>Finish Trading</button>
            </div>
          ) : (
            <div className="card" style={{ background: '#e59f71', textAlign: 'center', margin: '20px 0' }}>Waiting For Others To Finish</div>
          )}
        </>
      )}


      {phase === 'NIGHT' && (
        <>
          {/* IF condition is true, show Button A, ELSE show Button B */}
          {!me.finished_phase ? (
            <div className="card" style={{ background: '#333', color: 'white', textAlign: 'center', margin: '20px 0' }}>
              <button className="btn" onClick={() => handleUserAction('FINISH_PHASE')}>End Day</button>
            </div>
          ) : (
            <div className="card" style={{ background: '#e59f71', textAlign: 'center', margin: '20px 0' }}>Waiting For Others To Finish</div>
          )}
        </>
      )}

      {gameState.map && <VillageMap mapData={gameState.map} players={gameState.player_list} onAction={handleUserAction} />}
    </div >
  );
}

export default Gameplay;
