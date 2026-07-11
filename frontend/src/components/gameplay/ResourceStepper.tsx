import React from "react";
import { Resource } from "../../dtos/index";

import styles from "./ResourceStepper.module.css";
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
    <div className={styles.row}>
      <span className={styles.text2}>
        {resource}:
      </span>

      {/* Red Minus Button */}
      <button
        onClick={() => onChange(Math.max(0, value - 1))}
        className={styles.decrementButton}
      >
        -
      </button>

      {/* The Number */}
      <span className={styles.text}>
        {value}
      </span>

      {/* Emoji Plus Button */}
      <button
        onClick={() => onChange(value + 1)}
        className={styles.incrementButton}
      >
        {RESOURCE_EMOJIS[resource]} +
      </button>
    </div>
  );
};

export default ResourceStepper;
