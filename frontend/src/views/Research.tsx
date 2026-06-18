import React, { useEffect, useState } from "react";
import {
  ResearchPresenter,
  ResearchView,
} from "../presenters/ResearchPresenter";
import { ResearchGameDTO } from "../../../dtos";
import { NewGameModal } from "../components/NewGameModal";
const Research: React.FC = () => {
  const [presenter, setPresenter] = useState<ResearchPresenter | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(true);
  const [selectedGame, setSelectedGame] = useState<ResearchGameDTO | null>(
    null,
  );
  const [games, setGames] = useState<ResearchGameDTO[]>([]);
  const [isTrainingModalOpen, setIsTrainingModalOpen] = useState(false);
  const [availableGenomes, setAvailableGenomes] = useState([]);
  const [gameOptions, setGameOptions] = useState({});
  const [showTrainingSessions, setShowTrainingSessions] = useState(false);
  const [trainingSessions, setTrainingSessions] = useState<any[]>([]);
  const loadTrainingSessions = async () => {
    try {
      const res = await fetch("/api/research/training-sessions");
      const data = await res.json();
      setTrainingSessions(data.sessions || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (!showTrainingSessions) return;

    loadTrainingSessions();

    const interval = setInterval(() => {
      loadTrainingSessions();
    }, 1000);

    return () => clearInterval(interval);
  }, [showTrainingSessions]);


  const handleOpenTrainingMenu = async () => {
    try {
      console.log("[Research] Opening training menu...");

      // Fetch Rulesets
      console.log("[Research] Fetching rulesets from /api/newGame...");
      const rulesRes = await fetch("/api/newGame");
      console.log(`[Research] Ruleset response status: ${rulesRes.status}`);

      if (!rulesRes.ok) {
        throw new Error(`Failed to fetch rulesets: ${rulesRes.status} ${rulesRes.statusText}`);
      }

      const rulesData = await rulesRes.json();
      console.log(`[Research] Received rulesets:`, rulesData);
      setGameOptions(rulesData.options || {});

      // Fetch Genomes
      console.log("[Research] Fetching genomes from /api/research/genomes...");
      const genomeRes = await fetch("/api/research/genomes");
      console.log(`[Research] Genomes response status: ${genomeRes.status}`);

      if (!genomeRes.ok) {
        throw new Error(`Failed to fetch genomes: ${genomeRes.status} ${genomeRes.statusText}`);
      }

      const genomeData = await genomeRes.json();
      console.log(`[Research] Received ${genomeData.genomes?.length || 0} genomes:`, genomeData);
      setAvailableGenomes(genomeData.genomes || []);

      console.log("[Research] Opening training modal...");
      setIsTrainingModalOpen(true);
    } catch (e) {
      console.error("Failed to load training options:", e);
      alert(`Error loading training options: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const handleStartTraining = async (options: any) => {
    try {
      await fetch("/api/research/train", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ruleset: options.ruleset,
          botCount: options.botCount,
          generations: options.generations,
          baseGenome: options.baseGenome
        })
      });
      alert("Training Sequence Initiated!");
    } catch (e) {
      console.error("Failed to start training", e);
    }
  };
  const getDays = () => {
    if (!selectedGame) return [];

    return Object.entries(selectedGame.data.players);
  };

  useEffect(() => {
    const view: ResearchView = {
      setIsLoggedIn,
      setSelectedGame,
      setGames,
    };
    const researchPresenter = new ResearchPresenter(view);
    setPresenter(researchPresenter);
  }, []);

  if (!presenter) {
    return <div>Loading...</div>;
  }

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    presenter.handleLogin();
  };

  if (!isLoggedIn) {
    return (
      <div className='card' style={{ maxWidth: "400px", margin: "50px auto" }}>
        <h2 style={{ textAlign: "center" }}>Research Access</h2>
        <form onSubmit={handleLogin}>
          <label>Email</label>
          <input type='email' placeholder='researcher@lab.edu' required />

          <label>Password</label>
          <input type='password' required />

          <button
            type='submit'
            className='btn'
            style={{ width: "100%", marginTop: "10px" }}
          >
            Login
          </button>
        </form>
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}
      >
        <h1>Research Dashboard</h1>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            className="btn"
            onClick={() => {setShowTrainingSessions(!showTrainingSessions);}}
            style={{ backgroundColor: "#2c3e50" }}
          >
            Active Training Loops
          </button>

          <button
            className="btn"
            onClick={handleOpenTrainingMenu}
            style={{ backgroundColor: "#8e44ad" }}
          >
            Start Training Loop
          </button>
        </div>
      </div>

      {showTrainingSessions && (
        <div className="card" style={{ marginBottom: "20px" }}>
          <h3>Active Training Loops</h3>

          {trainingSessions.length === 0 ? (
            <p>No active training loops.</p>
          ) : (
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse"
              }}
            >
              <thead>
                <tr>
                  <th>Session</th>
                  <th>Current Game ID</th>
                  <th>Generation</th>
                  <th>Remaining</th>
                  <th>Bots</th>
                  <th>Population</th>
                  <th>Ruleset</th>
                </tr>
              </thead>

              <tbody>
                {trainingSessions.map((session) => (
                  <tr style={{textAlign: "center"}} key={session.session_id}>
                    <td>{session.session_id.slice(0, 8)}</td>
                    <td>{session.current_game_id ?? "-"}</td>
                    <td>{session.generation}</td>
                    <td>{session.generations_left}</td>
                    <td>{session.bot_count}</td>
                    <td>{session.population_size}</td>
                    <td>{session.ruleset}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <div style={{ display: "flex", gap: "20px" }}>
        <div className='card' style={{ flex: 1 }}>
          <h3>Game Logs</h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #ddd", textAlign: "left" }}>
                <th>ID</th>
                <th>Date</th>
                <th>Rounds</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {games.map((g) => (
                <tr key={g.game_id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: "10px 0" }}>{g.game_id}</td>
                  <td>{new Date(g.created_at).toLocaleString()}</td>
                  <td>{g.day_num}</td>
                  <td>
                    <button
                      className='btn btn-secondary'
                      style={{ padding: "5px 10px", fontSize: "0.8rem" }}
                      onClick={() => presenter.handleSelectGame(g)}
                    >
                      Analyze
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card" style={{ flex: 2 }}>
          {selectedGame ? (
            <div>
              <h3>Game {selectedGame.game_id}</h3>

              <p>
                Day: {selectedGame.day_num} | Phase: {selectedGame.phase}
              </p>

              {Object.entries(selectedGame.data.players).map(
                ([day, dayPlayers]: [string, any]) => (
                  <div
                    key={day}
                    style={{
                      marginBottom: "20px",
                      border: "1px solid #ddd",
                      padding: "10px",
                      borderRadius: "4px",
                    }}
                  >
                    <h4>Day {day}</h4>

                    {Object.entries(dayPlayers).map(
                      ([playerId, player]: [string, any]) => (
                        <div
                          key={playerId}
                          style={{
                            marginBottom: "10px",
                            padding: "10px",
                            background: "#f7f7f7",
                            borderRadius: "4px",
                          }}
                        >
                          <strong>
                            {player.name ?? playerId}
                          </strong>

                          <div>Health: {player.health}</div>

                          <div>
                            Resources:
                            <ul>
                              <li>Food: {player.resources?.food ?? 0}</li>
                              <li>Wood: {player.resources?.wood ?? 0}</li>
                              <li>Iron: {player.resources?.iron ?? 0}</li>
                            </ul>
                          </div>

                          <div>
                            Sickness Chance: {player.sickness_chance}
                          </div>

                          <div>
                            Fire Status: {player.fire_status}
                          </div>

                          <div>
                            Actions:
                            <pre
                              style={{
                                maxHeight: "150px",
                                overflow: "auto",
                              }}
                            >
                              {JSON.stringify(
                                player.actions,
                                null,
                                2
                              )}
                            </pre>
                          </div>

                          <div>
                            Committed Action:
                            <pre>
                              {JSON.stringify(
                                player.committed_action,
                                null,
                                2
                              )}
                            </pre>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                )
              )}
            </div>
          ) : (
            <p style={{ color: "#888", fontStyle: "italic" }}>
              Select a game to analyze.
            </p>
          )}
        </div>
      </div>
      <NewGameModal
        isOpen={isTrainingModalOpen}
        onClose={() => setIsTrainingModalOpen(false)}
        onSubmit={handleStartTraining}
        gameOptions={gameOptions}
        isTrainingMode={true}
        availableGenomes={availableGenomes}
      />
    </div>
  );
};

export default Research;
