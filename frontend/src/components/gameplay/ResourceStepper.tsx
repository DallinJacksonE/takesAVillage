import React from "react";
import { Resource } from "../../dtos/index";

// Map your resources to emojis
const RESOURCE_EMOJIS: Record<Resource, string> = {
  food: "🍎",
  wood: "🪵",
  iron: "⛏️",
};

interface StepperProps {
  resource: Resource;
  value: number;
  onChange: (newValue: number) => void;
}

const ResourceStepper: React.FC<StepperProps> = ({ resource, value, onChange }) => {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
      <span style={{ minWidth: "45px", fontSize: "0.85rem", textTransform: "capitalize", fontWeight: "bold", color: "#555" }}>
        {resource}:
      </span>

      {/* Red Minus Button */}
      <button
        onClick={() => onChange(Math.max(0, value - 1))}
        style={{ background: "#ffebee", color: "#c62828", border: "1px solid #ef9a9a", borderRadius: "4px", padding: "2px 8px", cursor: "pointer", fontWeight: "bold" }}
      >
        -
      </button>

      {/* The Number */}
      <span style={{ minWidth: "24px", textAlign: "center", fontWeight: "bold", fontSize: "0.9rem" }}>
        {value}
      </span>

      {/* Emoji Plus Button */}
      <button
        onClick={() => onChange(value + 1)}
        style={{ background: "#e8f5e9", color: "#2e7d32", border: "1px solid #a5d6a7", borderRadius: "4px", padding: "2px 8px", cursor: "pointer", fontWeight: "bold" }}
      >
        {RESOURCE_EMOJIS[resource]} +
      </button>
    </div>
  );
};

export default ResourceStepper;
