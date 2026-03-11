import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface JoinableGame {
  id: string;
  name: string;
  players: string;
}

const Play: React.FC = () => {
  const navigate = useNavigate();
  const [hasConsented, setHasConsented] = useState(false);
  const [is18Plus, setIs18Plus] = useState(false);
  const [joinableGames, setJoinableGames] = useState<JoinableGame[]>([]);

  useEffect(() => {
    if (hasConsented) {
      const fetchGames = async () => {
        try {
          const response = await fetch('/api/activeGames');
          if (response.ok) {
            const data: JoinableGame[] = await response.json();
            setJoinableGames(data);
          }
        } catch (error) {
          console.error("Error fetching active games:", error);
        }
      };

      fetchGames();
      const interval = setInterval(fetchGames, 10000);
      return () => clearInterval(interval);
    }
  }, [hasConsented]);

  const handleConsent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (is18Plus) {
      try {
        const response = await fetch('/api/consent', { method: 'POST' });
        if (response.ok) {
          setHasConsented(true);
        } else {
          console.error("Server rejected consent request");
        }
      } catch (error) {
        console.error("Error sending consent:", error);
      }
    } else {
      alert("You must be 18 or older to participate.");
    }
  };

  const startNewGame = async () => {
    try {
      const response = await fetch('/api/newGame', { method: 'POST' });
      if (response.ok) {
        const data = await response.json();
        navigate(`/game/${data.gameId}`);
      }
    } catch (error) {
      console.error("Error starting game:", error);
    }
  };

  const joinGame = async (gameId: string) => {
    try {
      const response = await fetch('/api/joinGame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gameId })
      });

      if (response.ok) {
        const data = await response.json();
        navigate(`/game/${data.gameId}`);
      }
    } catch (error) {
      console.error("Error joining game:", error);
    }
  }

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

  return (
    <div className="card" style={{ display: 'flex', height: '600px', padding: 0, overflow: 'hidden' }}>

      <div style={{ flex: 1, padding: '40px', display: 'flex', flexDirection: 'column', justifyContent: 'center', borderRight: '1px solid #ddd' }}>
        <h3>Create a Village</h3>
        <p style={{ color: '#666', marginBottom: '2rem' }}>
          Initialize a new game instance. You will be the first settler.
        </p>
        <button className="btn" onClick={startNewGame}>
          Start New Game
        </button>
      </div>

      <div style={{ flex: 1, padding: '40px', backgroundColor: '#fafafa' }}>
        <h3>Join Existing Village</h3>
        <p style={{ color: '#666', fontSize: '0.9rem' }}>Select a game to join:</p>

        <div style={{ height: '400px', overflowY: 'auto', border: '1px solid #eee', borderRadius: '4px' }}>
          {joinableGames.length === 0 ? (
            <p style={{ color: '#999', textAlign: 'center', marginTop: '50px' }}>No active games found.</p>
          ) : (
            joinableGames.map((game) => (
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
                <strong>{game.name || `Game ${game.id}`}</strong>
                <span style={{ fontSize: '0.85rem', color: '#888' }}>{game.players}</span>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}

export default Play;
