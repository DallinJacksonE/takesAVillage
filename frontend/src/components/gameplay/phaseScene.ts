import type { Phase } from "../../dtos";

export interface PhaseScene {
  label: string;
  showAxialMap: boolean;
  theme: "work" | "trade" | "night";
}

export const getPhaseScene = (phase: Phase): PhaseScene => {
  if (phase === "TRADE") {
    return {
      label: "Trade clearing",
      showAxialMap: false,
      theme: "trade",
    };
  }
  if (phase === "NIGHT") {
    return {
      label: "Night clearing",
      showAxialMap: false,
      theme: "night",
    };
  }
  return {
    label: "Village work map",
    showAxialMap: true,
    theme: "work",
  };
};