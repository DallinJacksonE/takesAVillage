import React, { useEffect, useState } from "react";
import { NewGameModal } from "../components/NewGameModal";
import { GameResearchDetail } from "../components/research/GameResearchDetail";
import { ResearchLayout } from "../components/research/ResearchLayout";
import { ResearchSidebar } from "../components/research/ResearchSidebar";
import { TrainingBatchDetail } from "../components/research/TrainingBatchDetail";
import {
  ResearchPresenter,
  ResearchTab,
  ResearchTrainingBatchRow,
  ResearchView,
} from "../presenters/ResearchPresenter";
import { ResearchSortMode } from "../service/ResearchService";
import {
  ResearchGameDetailDTO,
  ResearchGameListItemDTO,
  TrainingBatchDetailDTO,
} from "@takes-a-village/shared";

const Research: React.FC = () => {
  const [presenter, setPresenter] = useState<ResearchPresenter | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(true);
  const [activeTab, setActiveTab] = useState<ResearchTab>("games");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortMode, setSortMode] = useState<ResearchSortMode>("time_desc");
  const [games, setGames] = useState<ResearchGameListItemDTO[]>([]);
  const [trainingBatches, setTrainingBatches] = useState<ResearchTrainingBatchRow[]>([]);
  const [selectedGame, setSelectedGame] = useState<ResearchGameDetailDTO | null>(null);
  const [selectedTrainingBatch, setSelectedTrainingBatch] = useState<TrainingBatchDetailDTO | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isTrainingModalOpen, setIsTrainingModalOpen] = useState(false);
  const [gameOptions, setGameOptions] = useState<Record<string, Record<string, any>>>({});

  useEffect(() => {
    const view: ResearchView = {
      setIsLoggedIn,
      setSelectedGame,
      setSelectedTrainingBatch,
      setGames,
      setTrainingBatches,
      setActiveTab,
      setSearchQuery,
      setSortMode,
      setIsLoading,
      setStatusMessage,
      setErrorMessage,
      setTrainingOptions: (options) => setGameOptions(options.gameOptions),
      setIsTrainingModalOpen,
    };
    const researchPresenter = new ResearchPresenter(view);
    setPresenter(researchPresenter);

    return () => researchPresenter.dispose();
  }, []);

  if (!presenter) {
    return <div>Loading...</div>;
  }

  const handleLogin = (event: React.FormEvent) => {
    event.preventDefault();
    presenter.handleLogin();
  };

  if (!isLoggedIn) {
    return (
      <div className="card" style={{ maxWidth: "400px", margin: "50px auto" }}>
        <h2 style={{ textAlign: "center" }}>Research Access</h2>
        <form onSubmit={handleLogin}>
          <label>Email</label>
          <input type="email" placeholder="researcher@lab.edu" required />
          <label>Password</label>
          <input type="password" required />
          <button type="submit" className="btn" style={{ width: "100%", marginTop: "10px" }}>Login</button>
        </form>
      </div>
    );
  }

  const header = (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "16px", marginBottom: "18px" }}>
      <div>
        <h1 style={{ marginBottom: "4px" }}>Research Dashboard</h1>
        {isLoading && <span style={{ color: "#888" }}>Loading research data...</span>}
        {statusMessage && <div style={{ color: "#2e7d32" }}>{statusMessage}</div>}
        {errorMessage && <div style={{ color: "#c0392b" }}>{errorMessage}</div>}
      </div>
      <button className="btn btn-secondary" onClick={() => presenter.handleOpenTrainingMenu()} style={{ color: "black", backgroundColor: "white" }}>
        Start Training Loop
      </button>
    </div>
  );

  const sidebar = (
    <ResearchSidebar
      activeTab={activeTab}
      searchQuery={searchQuery}
      sortMode={sortMode}
      games={games}
      trainingBatches={trainingBatches}
      selectedGameId={selectedGame?.game_id}
      selectedBatchId={selectedTrainingBatch?.batch_id}
      onTabChange={(tab) => presenter.handleTabChanged(tab)}
      onSearchChange={(query) => void presenter.handleSearchQueryChanged(query)}
      onSortChange={(mode) => void presenter.handleSortModeChanged(mode)}
      onSelectGame={(game) => void presenter.handleSelectGame(game)}
      onSelectTrainingBatch={(batch) => void presenter.handleSelectTrainingBatch(batch)}
    />
  );

  const detail = (
    <div className="card">
      {selectedTrainingBatch ? (
        <TrainingBatchDetail
          batch={selectedTrainingBatch}
          onSelectGame={(gameId) => {
            setActiveTab("games");
            void presenter.handleSelectGame({ game_id: gameId } as ResearchGameListItemDTO);
          }}
        />
      ) : (
        <GameResearchDetail game={selectedGame} />
      )}
    </div>
  );

  return (
    <>
      <ResearchLayout header={header} sidebar={sidebar} detail={detail} />
      <NewGameModal
        isOpen={isTrainingModalOpen}
        onClose={() => setIsTrainingModalOpen(false)}
        onSubmit={(options) => void presenter.handleStartTraining(options)}
        gameOptions={gameOptions}
        isTrainingMode={true}
      />
    </>
  );
};

export default Research;
