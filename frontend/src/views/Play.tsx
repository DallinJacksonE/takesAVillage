import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { PlayPresenter, PlayView } from "../presenters/PlayPresenter";
import { JoinableGameDTO } from "@takes-a-village/shared";
import { NewGameModal } from "../components/NewGameModal"; // adjust path as needed

const Play: React.FC = () => {
  const navigate = useNavigate();
  const [hasConsented, setHasConsented] = useState(false);
  const [is18Plus, setIs18Plus] = useState(true);
  const [joinableGames, setJoinableGames] = useState<JoinableGameDTO[]>([]);

  // New Game Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [gameOptions, setGameOptions] = useState<Record<string, Record<string, any>>>({});
  const [selectedRuleset, setSelectedRuleset] = useState<string>("");
  const [hoveredRuleset, setHoveredRuleset] = useState<string | null>(null);
  const [botCount, setBotCount] = useState<number>(0);

  const presenter = useMemo(() => {
    const view: PlayView = {
      setJoinableGames: (games) => setJoinableGames(games),
      setHasConsented: (consented) => setHasConsented(consented),
      navigateToGame: (gameId) => navigate(`/game/${gameId}`),
      showAlert: (message) => alert(message),
      showNewGameModal: (options) => {
        setGameOptions(options);
        // Auto-select the first option if available
        const keys = Object.keys(options);
        if (keys.length > 0) setSelectedRuleset(keys[0]);
        setBotCount(0); // Reset bot count
        setIsModalOpen(true);
      },
      hideNewGameModal: () => setIsModalOpen(false),
    };
    return new PlayPresenter(view);
  }, [navigate]);

  useEffect(() => {
    if (hasConsented) {
      presenter.startFetchingGames();
    }
    return () => {
      presenter.destroy();
    };
  }, [presenter, hasConsented]);

  const handleConsent = (e: React.FormEvent) => {
    e.preventDefault();
    presenter.handleConsent(is18Plus);
  };

  const handleOpenNewGameMenu = () => {
    presenter.getNewGameOptions();
  };

  const handleStartNewGame = (options: any) => {
    console.log("Submitting:", options);

    presenter.startNewGame(
      options.ruleset,
      options.botCount,
      options.botGenome,
      options.botModel // <-- Forward model selection
    );
  };

  const joinGame = (gameId: string) => {
    presenter.joinGame(gameId);
  };

  if (!hasConsented) {
    return (
      <div className='card' style={{ maxWidth: "600px", margin: "0 auto" }}>
        <h2>Informed Consent</h2>
        <p>
          You are being asked to participate in a research study regarding
          social behavior in economic markets. Your data will be anonymized.
        </p>
        <p>
          <strong>Participation Requirement:</strong> You must be at least 18
          years of age.
        </p>
        <form onSubmit={handleConsent}>
          <div style={{ margin: "20px 0" }}>
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                cursor: "pointer",
              }}
            >
              <input
                type='checkbox'
                checked={is18Plus}
                onChange={(e) => setIs18Plus(e.target.checked)}
                style={{ width: "auto", marginBottom: 0 }}
              />
              I certify that I am 18 years of age or older.
            </label>
          </div>
          <button
            type='submit'
            className='btn'
            disabled={!is18Plus}
            style={{ opacity: is18Plus ? 1 : 0.5 }}
          >
            I Agree & Enter
          </button>
        </form>
      </div>
    );
  }

  return (
    <>
      <div
        className='card'
        style={{
          display: "flex",
          height: "600px",
          padding: 0,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            flex: 1,
            padding: "40px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            borderRight: "1px solid #ddd",
          }}
        >
          <h3>Create a Village</h3>
          <p style={{ color: "#666", marginBottom: "2rem" }}>
            Initialize a new game instance.
          </p>
          <button className='btn' onClick={handleOpenNewGameMenu}>
            Start New Game
          </button>
        </div>

        <div style={{ flex: 1, padding: "40px", backgroundColor: "#fafafa" }}>
          <h3>Join Existing Village</h3>
          <p style={{ color: "#666", fontSize: "0.9rem" }}>
            Select a game to join:
          </p>

          <div
            style={{
              height: "400px",
              overflowY: "auto",
              border: "1px solid #eee",
              borderRadius: "4px",
              backgroundColor: "white",
            }}
          >
            {/* MOCK GAME BUTTON FOR UI TESTING */}
            <div
              onClick={() => navigate("/game/test-render")}
              style={{
                padding: "15px",
                borderBottom: "1px solid #eee",
                cursor: "pointer",
                display: "flex",
                justifyContent: "space-between",
                backgroundColor: "#e0f7fa",
                borderLeft: "4px solid #00acc1"
              }}
            >
              <strong>UI Test Render</strong>
              <span style={{ fontSize: "0.85rem", color: "#00acc1", fontWeight: "bold" }}>
                Offline
              </span>
            </div>
            {joinableGames.length === 0 ? (
              <p
                style={{ color: "#999", textAlign: "center", marginTop: "50px" }}
              >
                No active games found.
              </p>
            ) : (
              joinableGames.map((game) => (
                <div
                  key={game.id}
                  onClick={() => joinGame(game.id)}
                  style={{
                    padding: "15px",
                    borderBottom: "1px solid #eee",
                    cursor: "pointer",
                    display: "flex",
                    justifyContent: "space-between",
                    backgroundColor: game.isRejoinable ? "#e8f5e9" : "transparent",
                    borderLeft: game.isRejoinable ? "4px solid #4caf50" : "none",
                    transition: "background 0.2s",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.backgroundColor = game.isRejoinable ? "#c8e6c9" : "#e8e8e8")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.backgroundColor = game.isRejoinable ? "#e8f5e9" : "transparent")
                  }
                >
                  <div>
                    <strong>{game.name || `Game ${game.id}`}</strong>
                    {game.isRejoinable && (
                      <span style={{ marginLeft: "10px", fontSize: "0.8rem", color: "#4caf50", fontWeight: "bold" }}>
                        (Rejoin)
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: "0.85rem", color: "#888" }}>
                    {game.players}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <NewGameModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleStartNewGame}
        gameOptions={gameOptions}
      />
    </>
  );
};

export default Play;
