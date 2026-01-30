import React, { useState, useEffect } from 'react';

function Play() {
  const [hasConsented, setHasConsented] = useState(false);
  const [is18Plus, setIs18Plus] = useState(false);

  // Dummy data for joinable games
  const [joinableGames, setJoinableGames] = useState([
    { id: 'g_101', name: 'Alpha Simulation', players: '3/10' },
    { id: 'g_102', name: 'Beta Cluster', players: '1/10' },
    { id: 'g_103', name: 'Village Test 4', players: '8/10' },
    { id: 'g_104', name: 'Economy V2', players: '2/10' },
    { id: 'g_105', name: 'Social Impact', players: '5/10' },
  ]);

  const handleConsent = (e) => {
    e.preventDefault();
    if (is18Plus) {
      // Simulate setting a cookie
      document.cookie = "user_session=" + Math.random().toString(36).substring(2);
      setHasConsented(true);
    } else {
      alert("You must be 18 or older to participate.");
    }
  };

  const startNewGame = async () => {
    try {
      // OLD: fetch('http://localhost:5000/api/newGame'...)
      // NEW: Relative path thanks to proxy
      const response = await fetch('/api/newGame', { method: 'POST' });
      if (response.ok) {
        const data = await response.json();
        // Navigate to the specific game instance
        navigate(`/game/${data.gameId}`);
      }
    } catch (error) {
      console.error("Error starting game:", error);
    }
  };

  const joinGame = async (gameId) => {
    try {
      console.log(`Joining game ${gameId}...`);
      const response = await fetch('/api/joinGame', { method: 'POST' });
      if (response.ok) {
        const data = await response.json();
        // Navigate to the specific game instance
        navigate(`/game/${data.gameId}`);
      }
    } catch (error) {
      console.error("Error starting game:", error);
    }
  }


  // --- View 1: Consent Form ---
  if (!hasConsented) {
    return (
      <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
        <h2>Informed Consent</h2>
        <p>
          You are being asked to participate in a research study regarding social behavior
          in economic markets. Your data will be anonymized.
        </p>
        <p>
          <strong>Participation Requirement:</strong> You must be at least 18 years of age.
        </p>
        <form onSubmit={handleConsent}>
          <div style={{ margin: '20px 0' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={is18Plus}
                onChange={(e) => setIs18Plus(e.target.checked)}
                style={{ width: 'auto', marginBottom: 0 }}
              />
              I certify that I am 18 years of age or older.
            </label>
          </div>
          <button type="submit" className="btn" disabled={!is18Plus} style={{ opacity: is18Plus ? 1 : 0.5 }}>
            I Agree & Enter
          </button>
        </form>
      </div>
    );
  }

  // --- View 2: Game Lobby ---
  return (
    <div className="card" style={{ display: 'flex', height: '600px', padding: 0, overflow: 'hidden' }}>

      {/* Left Side: Start Game */}
      <div style={{ flex: 1, padding: '40px', display: 'flex', flexDirection: 'column', justifyContent: 'center', borderRight: '1px solid #ddd' }}>
        <h3>Create a Village</h3>
        <p style={{ color: '#666', marginBottom: '2rem' }}>
          Initialize a new game instance. You will be the first settler.
        </p>
        <button className="btn" onClick={startNewGame}>
          Start New Game
        </button>
      </div>

      {/* Right Side: Join List */}
      <div style={{ flex: 1, padding: '40px', backgroundColor: '#fafafa' }}>
        <h3>Join Existing Village</h3>
        <p style={{ color: '#666', fontSize: '0.9rem' }}>Select a game to join:</p>

        <div style={{ height: '400px', overflowY: 'auto', border: '1px solid #eee', borderRadius: '4px' }}>
          {joinableGames.map((game) => (
            <div
              key={game.id}
              onClick={() => joinGame(game.id)}
              style={{
                padding: '15px',
                borderBottom: '1px solid #eee',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                transition: 'background 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#e8e8e8'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <strong>{game.name}</strong>
              <span style={{ fontSize: '0.85rem', color: '#888' }}>{game.players}</span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}

export default Play;
