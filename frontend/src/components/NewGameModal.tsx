import React, { useState, useEffect } from "react";
import { GenomeDTO } from "../dtos";

import styles from "./NewGameModal.module.css";
export interface GameSetupOptions {
  ruleset: string;
  botCount: number;
  botModel: string;
  generations?: number;
  gamesPerGeneration?: number;
  mutationStrength?: number;
  mutationRate?: number;
  randomImmigrantCount?: number;
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
  const [gamesPerGeneration, setGamesPerGeneration] = useState<number>(5);
  const [mutationStrength, setMutationStrength] = useState<number>(0.25);
  const [mutationRate, setMutationRate] = useState<number>(0.15);
  const [randomImmigrantCount, setRandomImmigrantCount] = useState<number>(1);
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
      ...(isTrainingMode ? {
        generations,
        gamesPerGeneration,
        mutationStrength,
        mutationRate,
        randomImmigrantCount,
        baseGenome,
      } : { botGenome }),
    };
    console.log("Submitting game options:", payload);
    onSubmit(payload);
    onClose();
  };

  return (
    <div className={styles.row8}>
      <div className={styles.panel3}>
        <h2 className={styles.header}>{isTrainingMode ? "Configure Training Loop" : "Game Setup"}</h2>

        {/* Ruleset Selection UI */}
        <div className={styles.row7}>
          <div className={styles.column3}>
            <h4>Ruleset</h4>
            <div className={styles.panel2}>
              {Object.keys(gameOptions).map((ruleset) => (
                <div
                  key={ruleset}
                  className={[
                    styles.rulesetOption,
                    selectedRuleset === ruleset ? styles.rulesetOptionSelected : "",
                  ].filter(Boolean).join(" ")}
                  onClick={() => setSelectedRuleset(ruleset)}
                  onMouseEnter={() => setHoveredRuleset(ruleset)}
                  onMouseLeave={() => setHoveredRuleset(null)}
                >
                  {ruleset}
                </div>
              ))}
            </div>
          </div>
          <div className={styles.column2}>
            <h4>Rules Preview</h4>
            <div className={styles.panel}>
              {hoveredRuleset || selectedRuleset ? (
                <pre className={styles.code}>
                  {JSON.stringify(gameOptions[hoveredRuleset || selectedRuleset], null, 2)}
                </pre>
              ) : (
                <span className={styles.text}>Hover to see configuration.</span>
              )}
            </div>
          </div>
        </div>

        {/* Dynamic Inputs based on Mode */}
        <div className={styles.column}>

          <div className={styles.row6}>
            <h4>Bots per Game:</h4>
            <input type="number" min={isTrainingMode ? "1" : "0"} max="10" value={botCount}
              onChange={(e) => setBotCount(Math.max(0, parseInt(e.target.value) || 0))}
              className={styles.botCountInput} />
          </div>

          {/* ONLY show Bot Architecture and Genomes if bots are actually being spawned */}
          <>
            {/* Architecture Selection */}
            <div className={styles.row5}>
              <h4>Bot Architecture:</h4>
              <select
                value={botModel}
                onChange={(e) => setBotModel(e.target.value)}
                className={styles.genomeSelect}
              >
                {availableModels.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            {!isTrainingMode && (
              <div className={styles.row4}>
                <h4>Bot Genome:</h4>
                <select value={botGenome} onChange={(e) => setBotGenome(e.target.value)} className={styles.genomeSelect}>
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
              <div className={styles.row3}>
                <h4>Generations:</h4>
                <input type="number" min="1" max="1000" value={generations}
                  onChange={(e) => setGenerations(Math.max(1, parseInt(e.target.value) || 1))}
                  className={styles.generationsInput} />
              </div>

              <div className={styles.row3}>
                <h4>Games per Generation:</h4>
                <input type="number" min="1" max="50" value={gamesPerGeneration}
                  onChange={(e) => setGamesPerGeneration(Math.max(1, Math.min(50, parseInt(e.target.value) || 1)))}
                  className={styles.generationsInput} />
              </div>

              <div className={styles.row3}>
                <h4>Mutation Strength:</h4>
                <input type="number" min="0" max="5" step="0.01" value={mutationStrength}
                  onChange={(e) => setMutationStrength(Math.max(0, parseFloat(e.target.value) || 0))}
                  className={styles.generationsInput} />
              </div>

              <div className={styles.row3}>
                <h4>Mutation Rate:</h4>
                <input type="number" min="0" max="1" step="0.01" value={mutationRate}
                  onChange={(e) => setMutationRate(Math.max(0, Math.min(1, parseFloat(e.target.value) || 0)))}
                  className={styles.generationsInput} />
              </div>

              <div className={styles.row3}>
                <h4>Random Immigrants:</h4>
                <input type="number" min="0" max="50" value={randomImmigrantCount}
                  onChange={(e) => setRandomImmigrantCount(Math.max(0, parseInt(e.target.value) || 0))}
                  className={styles.generationsInput} />
              </div>

              <div className={styles.row2}>
                <h4>Base Genome:</h4>
                <select value={baseGenome} onChange={(e) => setBaseGenome(e.target.value)} className={styles.genomeSelect}>
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
        <div className={styles.row}>
          <button className={`btn ${styles.button}`} onClick={onClose} >Cancel</button>
          <button className="btn" onClick={handleSubmit} disabled={!selectedRuleset}>
            {isTrainingMode ? "Start Training" : "Start Game"}
          </button>
        </div>
      </div>
    </div>
  );
};
