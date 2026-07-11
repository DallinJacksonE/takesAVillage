import React, { useState } from "react";

import styles from "./ExpandableJsonPanel.module.css";
interface ExpandableJsonPanelProps {
  title: string;
  data: unknown;
}

export const ExpandableJsonPanel: React.FC<ExpandableJsonPanelProps> = ({ title, data }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <section className={styles.section}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={styles.toggle}
      >
        {isOpen ? "▾" : "▸"} {title}
      </button>
      {isOpen && (
        <pre className={styles.code}>
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </section>
  );
};
