import React, { useState, useEffect } from "react";
import { GenomeDTO } from "../../../dtos";

export interface GameSetupOptions {
  ruleset: string;
  botCount: number;
  botModel: string;
  generations?: number;
  baseGenome?: string;
  botGenome?: string;
}

interface NewGameModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (options: GameSetupOptions) => void;
  gameOptions: Record<string, Record<string, any>>;
  isTrainingMode?: boolean;
}

export const NewGameModal: React.FC<NewGameModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  gameOptions,
  isTrainingMode = false,
}) => {
  const [selectedRuleset, setSelectedRuleset] = useState<string>("");
  const [hoveredRuleset, setHoveredRuleset] = useState<string | null>(null);
  const [botCount, setBotCount] = useState<number>(isTrainingMode ? 5 : 0);

  // Model state
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [botModel, setBotModel] = useState<string>("genetic");

  const [generations, setGenerations] = useState<number>(10);
  const [baseGenome, setBaseGenome] = useState<string>("random");
  const [botGenome, setBotGenome] = useState<string>("random");
  const [availableGenomes, setAvailableGenomes] = useState<GenomeDTO[]>([]);

  // Auto-select first ruleset on load
  useEffect(() => {
    const keys = Object.keys(gameOptions);
    if (keys.length > 0 && !selectedRuleset) {
      setSelectedRuleset(keys[0]);
    }
  }, [gameOptions, selectedRuleset]);

  useEffect(() => {
    if (!isOpen) return;

    const fetchGenomesAndModels = async () => {
      try {
        const genomeRes = await fetch("/api/research/genomes");

        if (!genomeRes.ok) {
          throw new Error(`Genome request failed: ${genomeRes.status}`);
        }

        const genomeData = await genomeRes.json();

        console.log(`[NewGameModal] Loaded ${genomeData.genomes?.length || 0} genomes and ${genomeData.models?.length || 0} models`);

        setAvailableGenomes(genomeData.genomes || []);

        // Populate the dynamic models from the Bot Server
        const fetchedModels = genomeData.models || ["genetic"];
        setAvailableModels(fetchedModels);
        if (fetchedModels.length > 0) {
          setBotModel(fetchedModels[0]);
        }

      } catch (e) {
        console.error("Failed to load genomes and models", e);
      }
    };

    fetchGenomesAndModels();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = () => {
    const payload = {
      ruleset: selectedRuleset,
      botCount,
      botModel, // Include the selected architecture
      ...(isTrainingMode ? { generations, baseGenome } : { botGenome }),
    };
    console.log("Submitting game options:", payload);
    onSubmit(payload);
    onClose();
  };

  return (
    <div style={{
      position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: "rgba(0,0,0,0.5)", display: "flex",
      alignItems: "center", justifyContent: "center", zIndex: 1000, color: "black"
    }}>
      <div style={{
        backgroundColor: "white", padding: "30px", borderRadius: "8px",
        width: "600px", maxWidth: "90%", boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        maxHeight: "90vh", overflowY: "auto"
      }}>
        <h2 style={{ marginTop: 0 }}>{isTrainingMode ? "Configure Training Loop" : "Game Setup"}</h2>

        {/* Ruleset Selection UI */}
        <div style={{ display: "flex", gap: "20px", marginTop: "20px", height: "150px" }}>
          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <h4>Ruleset</h4>
            <div style={{ flex: 1, overflowY: "auto", border: "1px solid #ddd", borderRadius: "4px" }}>
              {Object.keys(gameOptions).map((ruleset) => (
                <div
                  key={ruleset}
                  onClick={() => setSelectedRuleset(ruleset)}
                  onMouseEnter={() => setHoveredRuleset(ruleset)}
                  onMouseLeave={() => setHoveredRuleset(null)}
                  style={{
                    padding: "10px", cursor: "pointer", borderBottom: "1px solid #eee",
                    backgroundColor: selectedRuleset === ruleset ? "#e3f2fd" : "transparent",
                    borderLeft: selectedRuleset === ruleset ? "4px solid #1976d2" : "4px solid transparent",
                  }}
                >
                  {ruleset}
                </div>
              ))}
            </div>
          </div>
          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <h4>Rules Preview</h4>
            <div style={{ flex: 1, padding: "10px", backgroundColor: "#f5f5f5", borderRadius: "4px", fontSize: "0.85rem", overflowY: "auto", border: "1px solid #ddd" }}>
              {hoveredRuleset || selectedRuleset ? (
                <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                  {JSON.stringify(gameOptions[hoveredRuleset || selectedRuleset], null, 2)}
                </pre>
              ) : (
                <span style={{ color: "#888" }}>Hover to see configuration.</span>
              )}
            </div>
          </div>
        </div>

        {/* Dynamic Inputs based on Mode */}
        <div style={{ marginTop: "20px", display: "flex", flexDirection: "column", gap: "15px" }}>

          <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
            <h4>Bots per Game:</h4>
            <input type="number" min={isTrainingMode ? "1" : "0"} max="10" value={botCount}
              onChange={(e) => setBotCount(Math.max(0, parseInt(e.target.value) || 0))}
              style={{ width: "60px", padding: "5px" }} />
          </div>

          {/* ONLY show Bot Architecture and Genomes if bots are actually being spawned */}
          <>
            {/* Architecture Selection */}
            <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
              <h4>Bot Architecture:</h4>
              <select
                value={botModel}
                onChange={(e) => setBotModel(e.target.value)}
                style={{ padding: "5px", minWidth: "250px" }}
              >
                {availableModels.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            {!isTrainingMode && (
              <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
                <h4>Bot Genome:</h4>
                <select value={botGenome} onChange={(e) => setBotGenome(e.target.value)} style={{ padding: "5px", minWidth: "250px" }}>
                  <option value="random">Random Genome</option>
                  {availableGenomes.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.shorthand_name} - {g.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </>

          {isTrainingMode && (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
                <h4>Generations:</h4>
                <input type="number" min="1" max="1000" value={generations}
                  onChange={(e) => setGenerations(Math.max(1, parseInt(e.target.value) || 1))}
                  style={{ width: "80px", padding: "5px" }} />
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
                <h4>Base Genome:</h4>
                <select value={baseGenome} onChange={(e) => setBaseGenome(e.target.value)} style={{ padding: "5px", minWidth: "250px" }}>
                  <option value="random">Random (Fresh Gene Pool)</option>
                  {availableGenomes.map(g => (
                    <option key={g.id} value={g.id}>{g.shorthand_name} - {g.name}</option>
                  ))}
                </select>
              </div>
            </>
          )}
        </div>

        {/* Actions */}
        <div style={{ marginTop: "30px", display: "flex", justifyContent: "flex-end", gap: "15px" }}>
          <button className="btn" onClick={onClose} style={{ backgroundColor: "#ccc", color: "black" }}>Cancel</button>
          <button className="btn" onClick={handleSubmit} disabled={!selectedRuleset}>
            {isTrainingMode ? "Start Training" : "Start Game"}
          </button>
        </div>
      </div>
    </div>
  );
};
